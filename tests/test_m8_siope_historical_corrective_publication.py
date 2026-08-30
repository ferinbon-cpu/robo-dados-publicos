from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy, validate_policy
from robo_dados_publicos.product.publication import PublicationNames
from robo_dados_publicos.product.siope_historical_corrective_publication import (
    CONFIG_PATH, CorrectivePublicationError, EXPECTED_COLUMNS, EXPECTED_ROWS,
    GATE_ID, OLD_REMOTE_BASENAME, OWNER_AUTHORIZATION_PATH, REMOTE_BASENAME,
    SEMANTIC_READBACK_RANGE, WRITE_RANGE, _load_contract,
    dry_run_result, execute_corrective_publication, matrix_sha256,
    parse_canonical_matrix, validate_matrix, validate_owner_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/m8-siope-historical-corrective-r2-publication.yml"


def valid_matrix() -> list[list[str]]:
    return [[f"r{row}c{column}" for column in range(EXPECTED_COLUMNS)] for row in range(EXPECTED_ROWS)]


class FakeDrive:
    def __init__(self, matrix=None, collisions=(), inventory_tokens=()):
        self.expected = valid_matrix()
        self.matrix = self.expected if matrix is None else matrix
        self.collisions = set(collisions)
        self.events = []
        self.files = {}
        self.inventory_tokens = list(inventory_tokens)
        self.inventory_calls = 0
        self.readback_ranges = []

    def list_children_single_page(self, parent, page_size=1000):
        self.inventory_calls += 1
        self.events.append("inventory" if not self.files else "final_readback")
        names = self.collisions | {item["name"] for item in self.files.values()}
        token = self.inventory_tokens.pop(0) if self.inventory_tokens else None
        return {"files": [{"name": name} for name in names], "next_page_token": token}

    def create_google_sheet(self, name, parent):
        self.events.append("create_sheet")
        self.files["sheet"] = {"id": "sheet", "name": name, "mimeType": "application/vnd.google-apps.spreadsheet", "parents": [parent]}
        return self.files["sheet"]

    def metadata(self, file_id):
        self.events.append(f"metadata_{file_id}")
        return self.files[file_id]

    def sheets_values_update_raw(self, file_id, range_a1, values):
        assert range_a1 == WRITE_RANGE
        self.events.append("write_raw_matrix")
        return {"updatedRows": 9, "updatedColumns": 7, "updatedCells": 63}

    def sheets_values_get(self, file_id, range_a1):
        self.readback_ranges.append(range_a1)
        self.events.append("semantic_readback")
        return {"values": self.matrix}

    def put(self, path, name, parent, mime):
        key = "pdf" if mime == "application/pdf" else "manifest"
        self.events.append(f"create_{key}")
        self.files[key] = {"id": key, "name": name, "mimeType": mime, "parents": [parent], "bytes": Path(path).read_bytes()}
        return self.files[key]

    def get(self, file_id, destination):
        self.events.append(f"readback_{file_id}")
        Path(destination).write_bytes(self.files[file_id]["bytes"])
        return {"sha256": hashlib.sha256(self.files[file_id]["bytes"]).hexdigest()}


class CorrectivePublicationTests(unittest.TestCase):
    SHA = "a" * 40

    def _execution_patches(self, bundle, source):
        module = "robo_dados_publicos.product.siope_historical_corrective_publication"
        return (
            patch(f"{module}._load_contract", return_value={}),
            patch(f"{module}.validate_owner_authorization", return_value={}),
            patch(f"{module}.prepare_source", return_value=(bundle, valid_matrix(), source)),
            patch(f"{module}.output_parent_id", return_value="outputs"),
        )

    def test_exact_r2_names_and_old_names_rejected(self):
        self.assertEqual(PublicationNames.from_basename(REMOTE_BASENAME).all(), (
            "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2_TABELA",
            "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2.pdf",
            "SIOPE_LIMEIRA_HISTORICAL_2016_2024_V0_8_0_R2_publication_manifest.json",
        ))
        contract = _load_contract(ROOT)
        self.assertFalse(set(PublicationNames.from_basename(OLD_REMOTE_BASENAME).all()) & set(contract["remote_names"]))

    def test_contract_rejects_every_prohibited_capability(self):
        original = json.loads((ROOT / CONFIG_PATH).read_text(encoding="utf-8"))
        prohibited = (
            "overwrite_allowed", "replace_allowed", "delete_allowed", "retry_allowed",
            "pagination_allowed",
            "schedule_enabled", "recurrence_enabled", "source_collection_allowed",
            "processing_rerun_allowed", "reconciliation_rerun_allowed", "include_2025",
            "release_0_8_0_promotion", "compliance_claim_promotion",
        )
        for key in prohibited:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as raw:
                root = Path(raw); path = root / CONFIG_PATH; path.parent.mkdir(parents=True)
                mutated = copy.deepcopy(original); mutated[key] = True
                path.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaisesRegex(CorrectivePublicationError, "CONTRACT_POLICY"):
                    _load_contract(root)
        for key in ("create_only", "one_shot", "manual", "preflight_all_names_before_first_write", "completion_manifest_written_last"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as raw:
                root = Path(raw); path = root / CONFIG_PATH; path.parent.mkdir(parents=True)
                mutated = copy.deepcopy(original); mutated[key] = False
                path.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaisesRegex(CorrectivePublicationError, "CONTRACT_POLICY"):
                    _load_contract(root)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / CONFIG_PATH; path.parent.mkdir(parents=True)
            original["remote_names"] = list(PublicationNames.from_basename(OLD_REMOTE_BASENAME).all())
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaises(CorrectivePublicationError):
                _load_contract(root)

    def test_checked_in_owner_authorization_is_pending_and_rejected(self):
        evidence = json.loads((ROOT / OWNER_AUTHORIZATION_PATH).read_text(encoding="utf-8"))
        self.assertEqual(evidence["status"], "PENDING_POST_MERGE_OWNER_AUTHORIZATION")
        self.assertIsNone(evidence["authorized_main_sha"])
        with self.assertRaisesRegex(CorrectivePublicationError, "OWNER_AUTHORIZATION_NOT_VALID"):
            validate_owner_authorization(root=ROOT, execution_sha=self.SHA)

    def test_owner_authorization_missing_and_every_governance_drift_rejected(self):
        original = json.loads((ROOT / OWNER_AUTHORIZATION_PATH).read_text(encoding="utf-8"))
        original["status"] = "AUTHORIZED_FOR_SINGLE_CORRECTIVE_R2_T3_PUBLICATION"
        original["authorized_main_sha"] = self.SHA
        mutations = {
            "schema": "WRONG", "gate_id": "WRONG", "drive_target": "WRONG",
            "remote_names": ["WRONG"], "authorized_main_sha": "b" * 40,
            "overwrite_allowed": True, "replace_allowed": True, "delete_allowed": True,
            "retry_allowed": True,
        }
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(CorrectivePublicationError, "OWNER_AUTHORIZATION_MISSING"):
                validate_owner_authorization(root=raw, execution_sha=self.SHA)
        for field, value in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as raw:
                root = Path(raw); path = root / OWNER_AUTHORIZATION_PATH; path.parent.mkdir(parents=True)
                evidence = copy.deepcopy(original); evidence[field] = value
                path.write_text(json.dumps(evidence), encoding="utf-8")
                with self.assertRaises(CorrectivePublicationError):
                    validate_owner_authorization(root=root, execution_sha=self.SHA)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / OWNER_AUTHORIZATION_PATH; path.parent.mkdir(parents=True)
            missing_sha = copy.deepcopy(original); missing_sha.pop("authorized_main_sha")
            path.write_text(json.dumps(missing_sha), encoding="utf-8")
            with self.assertRaises(CorrectivePublicationError):
                validate_owner_authorization(root=root, execution_sha=self.SHA)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); path = root / OWNER_AUTHORIZATION_PATH; path.parent.mkdir(parents=True)
            path.write_text(json.dumps(original), encoding="utf-8")
            self.assertEqual(validate_owner_authorization(root=root, execution_sha=self.SHA)["authorized_main_sha"], self.SHA)

    def test_exact_valid_matrix_and_hash_are_deterministic(self):
        matrix = valid_matrix()
        result = validate_matrix(matrix, expected=copy.deepcopy(matrix))
        self.assertEqual((result["rows"], result["columns"]), (9, 7))
        self.assertEqual(result["matrix_sha256"], matrix_sha256(matrix))

    def test_csv_parser_is_explicit_comma_and_rejects_malformed_shape(self):
        with tempfile.TemporaryDirectory() as raw:
            good = Path(raw) / "good.csv"
            good.write_text("\n".join(",".join(row) for row in valid_matrix()) + "\n", encoding="utf-8")
            self.assertEqual(parse_canonical_matrix(good), valid_matrix())
            bad = Path(raw) / "bad.csv"; bad.write_text("a;b;c\n", encoding="utf-8")
            with self.assertRaises(CorrectivePublicationError):
                parse_canonical_matrix(bad)

    def test_prepare_source_rejects_wrong_table_and_pdf_hashes(self):
        import robo_dados_publicos.product.siope_historical_corrective_publication as module
        expected = {
            "table.csv": module.EXPECTED_ZIP_MEMBERS["product/table.csv"][1],
            "report.pdf": module.EXPECTED_ZIP_MEMBERS["product/report.pdf"][1],
            "manifest.json": module.EXPECTED_ZIP_MEMBERS["product/manifest.json"][1],
        }
        for wrong_name, code in (("table.csv", "TABLE_SOURCE_HASH"), ("report.pdf", "PDF_SOURCE_HASH")):
            with self.subTest(wrong_name=wrong_name), tempfile.TemporaryDirectory() as raw:
                root = Path(raw); bundle = self._bundle(root); matrix = valid_matrix()
                def fake_hash(path):
                    return "wrong" if Path(path).name == wrong_name else expected[Path(path).name]
                with patch.object(module, "_load_contract", return_value={}), \
                     patch.object(module, "validate_source_zip", return_value={"zip_sha256": "pinned"}), \
                     patch.object(module, "extract_product_bundle", return_value=bundle), \
                     patch.object(module, "validate_bundle_integrity", return_value={"table_matrix": matrix}), \
                     patch.object(module, "parse_canonical_matrix", return_value=matrix), \
                     patch.object(module, "_sha256", side_effect=fake_hash):
                    with self.assertRaisesRegex(CorrectivePublicationError, code):
                        module.prepare_source(root=root, source_zip="unused", work_dir=root / "work")

    def test_semantic_readback_rejects_all_shape_and_value_mutations(self):
        expected = valid_matrix()
        mutations = {}
        mutations["wrong row count"] = expected[:-1]
        mutations["extra row"] = expected + [["x"] * 7]
        mutations["wrong column count"] = [row[:-1] for row in expected]
        mutations["extra column"] = [row + ["x"] for row in expected]
        mutations["single-cell header collapse"] = [[",".join(expected[0])]] + expected[1:]
        for label, row, column, value in (
            ("wrong header", 0, 0, "wrong"), ("wrong cell", 4, 3, "wrong"),
            ("missing cell", 4, 3, ""),
        ):
            mutated = copy.deepcopy(expected); mutated[row][column] = value; mutations[label] = mutated
        mutations["reordered rows"] = [expected[1], expected[0], *expected[2:]]
        mutations["reordered columns"] = [[row[1], row[0], *row[2:]] for row in expected]
        for label, observed in mutations.items():
            with self.subTest(label=label), self.assertRaises(CorrectivePublicationError):
                validate_matrix(observed, expected=expected)

    def _bundle(self, root: Path):
        bundle = root / "bundle"; bundle.mkdir()
        (bundle / "report.pdf").write_bytes(b"pdf")
        (bundle / "table.csv").write_text("table", encoding="utf-8")
        (bundle / "manifest.json").write_text("{}", encoding="utf-8")
        return bundle

    def test_collision_preflight_has_zero_writes(self):
        with tempfile.TemporaryDirectory() as raw:
            bundle = self._bundle(Path(raw)); drive = FakeDrive(collisions=[PublicationNames.from_basename(REMOTE_BASENAME).pdf])
            source = {"source": {"zip_sha256": "pinned"}}
            patches = self._execution_patches(bundle, source)
            with patches[0], patches[1], patches[2], patches[3]:
                with self.assertRaisesRegex(CorrectivePublicationError, "R2_NAME_COLLISION") as caught:
                    execute_corrective_publication(drive, root=ROOT, source_zip="unused", published_at="2026-08-30T00:00:00+00:00", execution_sha=self.SHA)
            self.assertEqual(caught.exception.created_count, 0)
            self.assertEqual(drive.events, ["inventory"])

    def test_semantic_failure_stops_after_one_sheet_without_retry_or_cleanup(self):
        with tempfile.TemporaryDirectory() as raw:
            bundle = self._bundle(Path(raw)); observed = valid_matrix(); observed[2][2] = "wrong"; drive = FakeDrive(observed)
            source = {"source": {"zip_sha256": "pinned"}}
            patches = self._execution_patches(bundle, source)
            with patches[0], patches[1], patches[2], patches[3]:
                with self.assertRaises(CorrectivePublicationError) as caught:
                    execute_corrective_publication(drive, root=ROOT, source_zip="unused", published_at="2026-08-30T00:00:00+00:00", execution_sha=self.SHA)
            self.assertEqual(caught.exception.created_count, 1)
            self.assertEqual(drive.events.count("create_sheet"), 1)
            self.assertNotIn("create_pdf", drive.events); self.assertNotIn("create_manifest", drive.events)

    def test_success_order_requires_semantics_then_pdf_and_manifest_last(self):
        with tempfile.TemporaryDirectory() as raw:
            bundle = self._bundle(Path(raw)); drive = FakeDrive(); source = {"source": {"zip_sha256": "pinned"}}
            patches = self._execution_patches(bundle, source)
            with patches[0], patches[1], patches[2], patches[3]:
                result = execute_corrective_publication(drive, root=ROOT, source_zip="unused", published_at="2026-08-30T00:00:00+00:00", execution_sha=self.SHA)
            order = [drive.events.index(name) for name in ("create_sheet", "write_raw_matrix", "semantic_readback", "create_pdf", "readback_pdf", "create_manifest", "readback_manifest", "final_readback")]
            self.assertEqual(order, sorted(order)); self.assertTrue(result["completion_manifest_written_last"])
            self.assertEqual(drive.readback_ranges, [SEMANTIC_READBACK_RANGE, SEMANTIC_READBACK_RANGE])

    def test_full_range_live_adapter_rejects_h1_and_a10(self):
        expected = valid_matrix()
        cases = {
            "H1": [expected[0] + ["extra"], *expected[1:]],
            "A10": expected + [["extra"]],
        }
        for label, observed in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as raw:
                bundle = self._bundle(Path(raw)); drive = FakeDrive(observed); source = {"source": {"zip_sha256": "pinned"}}
                patches = self._execution_patches(bundle, source)
                with patches[0], patches[1], patches[2], patches[3], self.assertRaises(CorrectivePublicationError):
                    execute_corrective_publication(drive, root=ROOT, source_zip="unused", published_at="2026-08-30T00:00:00+00:00", execution_sha=self.SHA)
                self.assertEqual(drive.readback_ranges, ["A:Z"])
                self.assertNotIn("create_pdf", drive.events)

    def test_preflight_pagination_token_stops_zero_writes_without_second_request(self):
        with tempfile.TemporaryDirectory() as raw:
            bundle = self._bundle(Path(raw)); drive = FakeDrive(inventory_tokens=["next"]); source = {"source": {"zip_sha256": "pinned"}}
            patches = self._execution_patches(bundle, source)
            with patches[0], patches[1], patches[2], patches[3], self.assertRaisesRegex(CorrectivePublicationError, "PAGINATION_PROHIBITED") as caught:
                execute_corrective_publication(drive, root=ROOT, source_zip="unused", published_at="2026-08-30T00:00:00+00:00", execution_sha=self.SHA)
            self.assertEqual(caught.exception.created_count, 0); self.assertEqual(drive.inventory_calls, 1)
            self.assertNotIn("create_sheet", drive.events)

    def test_final_inventory_pagination_token_fails_closed_without_retry(self):
        with tempfile.TemporaryDirectory() as raw:
            bundle = self._bundle(Path(raw)); drive = FakeDrive(inventory_tokens=[None, "next"]); source = {"source": {"zip_sha256": "pinned"}}
            patches = self._execution_patches(bundle, source)
            with patches[0], patches[1], patches[2], patches[3], self.assertRaisesRegex(CorrectivePublicationError, "FINAL_INVENTORY_PAGINATION_PROHIBITED") as caught:
                execute_corrective_publication(drive, root=ROOT, source_zip="unused", published_at="2026-08-30T00:00:00+00:00", execution_sha=self.SHA)
            self.assertEqual(caught.exception.created_count, 3); self.assertEqual(drive.inventory_calls, 2)

    def test_dry_run_ready_path_has_zero_network_and_writes(self):
        result = dry_run_result(valid_matrix(), {"source": {"zip_sha256": "pinned"}})
        self.assertEqual(result["drive_writes"], 0); self.assertFalse(result["network_called"])
        self.assertEqual(result["would_create"], 3)

    def test_workflow_is_manual_only_with_boolean_confirmation(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text); self.assertIn("type: boolean", text)
        self.assertNotIn("\n  push:", text); self.assertNotIn("\n  schedule:", text)
        self.assertNotIn("workflow_call:", text); self.assertIn("persist-credentials: false", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertLess(text.index("Validar autorização separada"), text.index("GOOGLE_DRIVE_CLIENT_ID"))
        self.assertIn('--execution-sha "$GITHUB_SHA"', text)

    def test_automation_policy_registers_corrective_t3_as_blocked(self):
        policy = load_policy(ROOT)
        validate_policy(policy)
        gate = next(row for row in policy["gates"] if row["id"] == "M8_SIOPE_HISTORICAL_CORRECTIVE_R2_PUBLICATION")
        self.assertEqual(gate["tier"], "T3_MUTATING_OR_PUBLICATION")
        self.assertFalse(gate["auto_allowed"]); self.assertFalse(gate["future_batch_execution_authorized"])
        self.assertTrue(gate["effects"]["drive_writes"]); self.assertTrue(gate["effects"]["publication"])
        decision = evaluate_gate(policy, gate["id"])
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertIn("CORRECTIVE_R2_PUBLICATION_REQUIRES_SEPARATE_EXPLICIT_OWNER_AUTHORIZATION", decision["blockers"])
        mutated = copy.deepcopy(policy)
        next(row for row in mutated["gates"] if row["id"] == gate["id"])["auto_allowed"] = True
        with self.assertRaisesRegex(Exception, "STOP_MANUAL_TIER_AUTO_ENABLED"):
            validate_policy(mutated)


if __name__ == "__main__":
    unittest.main()
