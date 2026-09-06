from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfWriter

from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.manual_ingest.ephemeral_runtime_digest import (
    EphemeralDigestStop,
    REMOTE_EFFECT_KEYS,
    _git_blob_sha,
    _validate_processor_source,
    run_ephemeral_digest,
    validate_contract,
)
from robo_dados_publicos.manual_ingest.source_family_maturity import (
    load_maturity_registry,
)
from scripts.run_ephemeral_runtime_digest import _safe_input_path, _safe_result_path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "ephemeral_runtime_digest.v1.json"
MATURITY_PATH = ROOT / "config" / "source_family_maturity_registry.v1.json"
FIXTURE = ROOT / "tests" / "fixtures" / "jornal_oficial_fixture_2pages.pdf"
PROCESSOR_PATH = ROOT / "robo_dados_publicos" / "journal" / "processing.py"


def manifest_for(relative_path: str = "input.pdf") -> dict:
    return {
        "schema": "EPHEMERAL_DIGEST_BATCH_V1",
        "batch_id": "task090-fixture",
        "inputs": [
            {
                "family": "JORNAL_OFICIAL",
                "source_key": "journal-7309",
                "relative_path": relative_path,
                "mime_type": "application/pdf",
                "metadata": {
                    "edition": 7309,
                    "publication_date": "2026-08-21",
                    "source_url": "https://example.invalid/jornal/7309.pdf",
                },
            }
        ],
        "remote_effects_authorized": {key: False for key in REMOTE_EFFECT_KEYS},
    }


class TestTask090EphemeralRuntimeDigest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.maturity = load_maturity_registry(MATURITY_PATH)

    def _workspace_with_fixture(self):
        td = tempfile.TemporaryDirectory()
        workspace = Path(td.name)
        shutil.copyfile(FIXTURE, workspace / "input.pdf")
        return td, workspace

    def test_contract_is_strict_local_only_and_bounded(self):
        contract = validate_contract(deepcopy(self.contract))
        self.assertEqual("T0_OFFLINE_EPHEMERAL_RUNTIME_DIGEST", contract["mode"])
        self.assertEqual(3, contract["limits"]["max_batch_files"])
        self.assertLessEqual(contract["limits"]["max_input_bytes_each"], 70_000_000)
        self.assertLessEqual(contract["limits"]["max_total_input_bytes"], 110_000_000)
        self.assertEqual({"JORNAL_OFICIAL"}, set(contract["adapters"]))
        source_cfg = contract["adapters"]["JORNAL_OFICIAL"]["processor_source"]
        self.assertEqual(
            "50c7d0f697f63f651daaf010beed541bc46ec9a1",
            source_cfg["expected_git_blob_sha"],
        )
        self.assertIn("socket", source_cfg["forbidden_import_roots"])
        self.assertIn("subprocess", source_cfg["forbidden_import_roots"])
        self.assertTrue(
            all(value is False for value in contract["automatic_remote_effects"].values())
        )


    def test_contract_processor_blob_matches_repository_file(self):
        observed = _git_blob_sha(PROCESSOR_PATH.read_bytes())
        expected = self.contract["adapters"]["JORNAL_OFICIAL"]["processor_source"][
            "expected_git_blob_sha"
        ]
        self.assertEqual("50c7d0f697f63f651daaf010beed541bc46ec9a1", observed)
        self.assertEqual(expected, observed)

    def test_processor_source_audit_rejects_forbidden_import_if_declared(self):
        contract = deepcopy(self.contract)
        contract["adapters"]["JORNAL_OFICIAL"]["processor_source"][
            "forbidden_import_roots"
        ].append("json")
        with self.assertRaisesRegex(EphemeralDigestStop, "PROCESSOR_FORBIDDEN_IMPORT"):
            _validate_processor_source(contract)

    def test_happy_path_digests_only_in_ephemeral_workspace(self):
        td, workspace = self._workspace_with_fixture()
        try:
            result = run_ephemeral_digest(
                deepcopy(self.contract),
                manifest_for(),
                deepcopy(self.maturity),
                workspace_root=workspace,
            )
            self.assertEqual(
                "PASS_EPHEMERAL_RUNTIME_DIGEST_NOT_PERSISTED", result["status"]
            )
            self.assertFalse(result["persistence_authorized"])
            self.assertEqual(1, result["input_count"])
            self.assertEqual(4, result["candidate_file_count"])
            self.assertEqual(
                "50c7d0f697f63f651daaf010beed541bc46ec9a1",
                result["processor_git_blob_sha"],
            )
            self.assertEqual(0, result["effects"]["source_network_calls"])
            self.assertEqual(0, result["effects"]["drive_network_calls"])
            self.assertEqual(0, result["effects"]["bronze_writes"])
            self.assertEqual(0, result["effects"]["silver_writes"])
            self.assertEqual(0, result["effects"]["gold_writes"])
            self.assertEqual(0, result["effects"]["rag_writes"])
            self.assertEqual(4, result["effects"]["local_candidate_files"])

            batch_dir = workspace / "ephemeral_digest_candidates" / "task090-fixture"
            item_dir = batch_dir / "journal-7309"
            self.assertTrue(item_dir.is_dir())
            observed = {p.name for p in item_dir.iterdir() if p.is_file()}
            self.assertEqual(
                {
                    "edition_manifest.json",
                    "pages_silver.jsonl",
                    "events_gold.jsonl",
                    "chunks_rag.jsonl",
                },
                observed,
            )
            self.assertFalse((item_dir / "bronze").exists())
            self.assertFalse((item_dir / "reconciliation_tasks.jsonl").exists())

            item = result["items"][0]
            self.assertEqual("PASS_DOCUMENT_PROCESSING", item["adapter_status"])
            self.assertEqual(2, item["silver_rows"])
            self.assertGreaterEqual(item["gold_rows"], 2)
            self.assertGreaterEqual(item["rag_rows"], 1)

            combined = (
                (item_dir / "pages_silver.jsonl").read_text(encoding="utf-8")
                + (item_dir / "events_gold.jsonl").read_text(encoding="utf-8")
                + (item_dir / "chunks_rag.jsonl").read_text(encoding="utf-8")
            )
            self.assertNotIn("123.456.789-09", combined)
            self.assertNotIn("teste.pessoa@example.com", combined)
        finally:
            td.cleanup()

    def test_same_bytes_in_fresh_workspace_are_deterministic(self):
        results = []
        for _ in range(2):
            td, workspace = self._workspace_with_fixture()
            try:
                result = run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest_for(),
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
                results.append(
                    (result["result_sha256"], result["candidate_set_sha256"])
                )
            finally:
                td.cleanup()
        self.assertEqual(results[0], results[1])

    def test_unknown_family_stops_before_output(self):
        td, workspace = self._workspace_with_fixture()
        try:
            manifest = manifest_for()
            manifest["inputs"][0]["family"] = "RREO"
            with self.assertRaisesRegex(EphemeralDigestStop, "FAMILY_NOT_ADAPTED"):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest,
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
            self.assertFalse((workspace / "ephemeral_digest_candidates").exists())
        finally:
            td.cleanup()

    def test_maturity_downgrade_stops_before_output(self):
        td, workspace = self._workspace_with_fixture()
        try:
            maturity = deepcopy(self.maturity)
            maturity["families"]["JORNAL_OFICIAL"][
                "level"
            ] = "ROUTING_ONLY_SUPERVISED_EXECUTION"
            with self.assertRaisesRegex(EphemeralDigestStop, "FAMILY_MATURITY"):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest_for(),
                    maturity,
                    workspace_root=workspace,
                )
            self.assertFalse((workspace / "ephemeral_digest_candidates").exists())
        finally:
            td.cleanup()

    def test_path_traversal_stops(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            manifest = manifest_for("../outside.pdf")
            with self.assertRaisesRegex(EphemeralDigestStop, "INPUT_PATH"):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest,
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )

    def test_duplicate_input_path_stops(self):
        td, workspace = self._workspace_with_fixture()
        try:
            manifest = manifest_for()
            duplicate = deepcopy(manifest["inputs"][0])
            duplicate["source_key"] = "journal-7310"
            duplicate["metadata"]["edition"] = 7310
            manifest["inputs"].append(duplicate)
            with self.assertRaisesRegex(EphemeralDigestStop, "DUPLICATE_INPUT_PATH"):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest,
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
        finally:
            td.cleanup()

    def test_more_than_three_inputs_stops(self):
        td, workspace = self._workspace_with_fixture()
        try:
            manifest = manifest_for()
            base = manifest["inputs"][0]
            manifest["inputs"] = []
            for index in range(4):
                item = deepcopy(base)
                item["source_key"] = f"journal-{7309 + index}"
                item["relative_path"] = f"input-{index}.pdf"
                item["metadata"]["edition"] = 7309 + index
                shutil.copyfile(FIXTURE, workspace / item["relative_path"])
                manifest["inputs"].append(item)
            with self.assertRaisesRegex(EphemeralDigestStop, "INPUT_COUNT"):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest,
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
        finally:
            td.cleanup()

    def test_remote_effect_authorization_is_rejected(self):
        td, workspace = self._workspace_with_fixture()
        try:
            manifest = manifest_for()
            manifest["remote_effects_authorized"]["drive_network_calls"] = True
            with self.assertRaisesRegex(
                EphemeralDigestStop, "MANIFEST_REMOTE_EFFECT_ENABLED"
            ):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest,
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
        finally:
            td.cleanup()

    def test_blank_pdf_stops_and_cleans_partial_candidates(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            blank = workspace / "input.pdf"
            writer = PdfWriter()
            writer.add_blank_page(width=595, height=842)
            with blank.open("wb") as handle:
                writer.write(handle)

            with self.assertRaisesRegex(EphemeralDigestStop, "ADAPTER_STATUS"):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest_for(),
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
            self.assertFalse((workspace / "ephemeral_digest_candidates").exists())


    def test_invalid_batch_id_stops_before_output(self):
        td, workspace = self._workspace_with_fixture()
        try:
            manifest = manifest_for()
            manifest["batch_id"] = "../escape"
            with self.assertRaisesRegex(EphemeralDigestStop, "BATCH_ID"):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest,
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
            self.assertFalse((workspace / "ephemeral_digest_candidates").exists())
        finally:
            td.cleanup()

    def test_workspace_root_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            real = parent / "real"
            real.mkdir()
            shutil.copyfile(FIXTURE, real / "input.pdf")
            link = parent / "workspace-link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(
                EphemeralDigestStop, "WORKSPACE_ROOT_NOT_REAL_DIRECTORY"
            ):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest_for(),
                    deepcopy(self.maturity),
                    workspace_root=link,
                )
            self.assertFalse((real / "ephemeral_digest_candidates").exists())

    def test_processor_blob_drift_stops_before_processing(self):
        td, workspace = self._workspace_with_fixture()
        try:
            contract = deepcopy(self.contract)
            contract["adapters"]["JORNAL_OFICIAL"]["processor_source"][
                "expected_git_blob_sha"
            ] = "0" * 40
            with self.assertRaisesRegex(EphemeralDigestStop, "PROCESSOR_BLOB_DRIFT"):
                run_ephemeral_digest(
                    contract,
                    manifest_for(),
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
            self.assertFalse((workspace / "ephemeral_digest_candidates").exists())
        finally:
            td.cleanup()

    def test_unexpected_output_drift_stops_and_cleans_candidates(self):
        td, workspace = self._workspace_with_fixture()
        original = JournalPdfProcessor.process

        def polluted_process(processor, *args, **kwargs):
            result = original(processor, *args, **kwargs)
            (Path(kwargs["out_dir"]) / "unexpected.txt").write_text(
                "unexpected", encoding="utf-8"
            )
            return result

        try:
            with patch.object(JournalPdfProcessor, "process", new=polluted_process):
                with self.assertRaisesRegex(EphemeralDigestStop, "OUTPUT_SET_DRIFT"):
                    run_ephemeral_digest(
                        deepcopy(self.contract),
                        manifest_for(),
                        deepcopy(self.maturity),
                        workspace_root=workspace,
                    )
            self.assertFalse((workspace / "ephemeral_digest_candidates").exists())
        finally:
            td.cleanup()

    def test_cli_manifest_path_must_be_inside_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            workspace = parent / "workspace"
            workspace.mkdir()
            outside = parent / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError, "STOP_EPHEMERAL_DIGEST_MANIFEST_PATH"
            ):
                _safe_input_path(
                    workspace,
                    str(outside),
                    code="STOP_EPHEMERAL_DIGEST_MANIFEST_PATH",
                )


    def test_cli_result_path_accepts_bounded_relative_path(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            got = _safe_result_path(workspace, "results/result.json")
            self.assertEqual(workspace / "results" / "result.json", got)
            self.assertTrue((workspace / "results").is_dir())

    def test_cli_result_path_rejects_absolute_and_parent_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            with self.assertRaisesRegex(
                ValueError, "STOP_EPHEMERAL_DIGEST_RESULT_PATH"
            ):
                _safe_result_path(workspace, str((workspace / "absolute.json").resolve()))
            with self.assertRaisesRegex(
                ValueError, "STOP_EPHEMERAL_DIGEST_RESULT_PATH"
            ):
                _safe_result_path(workspace, "../outside.json")

    def test_cli_result_path_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            workspace = parent / "workspace"
            outside = parent / "outside"
            workspace.mkdir()
            outside.mkdir()
            (workspace / "escape").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(
                ValueError, "STOP_EPHEMERAL_DIGEST_RESULT_PATH"
            ):
                _safe_result_path(workspace, "escape/result.json")

    def test_candidate_root_must_be_fresh(self):
        td, workspace = self._workspace_with_fixture()
        try:
            (workspace / "ephemeral_digest_candidates").mkdir()
            with self.assertRaisesRegex(
                EphemeralDigestStop, "CANDIDATE_ROOT_NOT_FRESH"
            ):
                run_ephemeral_digest(
                    deepcopy(self.contract),
                    manifest_for(),
                    deepcopy(self.maturity),
                    workspace_root=workspace,
                )
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
