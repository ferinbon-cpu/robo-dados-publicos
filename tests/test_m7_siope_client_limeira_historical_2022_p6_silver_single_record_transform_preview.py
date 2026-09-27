from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_bronze_drive_readback_review import (
    Historical2022P6BronzeDriveReadbackReviewError,
    review,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_silver_single_record_transform_preview import (
    Historical2022P6SilverTransformPreviewError,
    preview,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
READBACK_REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_bronze_drive_readback_review.json"
PREVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_silver_single_record_transform_preview.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2022-p6-silver-single-record-transform-preview-gate.yml"
EXPECTED_SILVER_SHA256 = "d8f14e5fa52cf214c837cb6a3d702f8b5a12310252045695547b289f88a03632"
EXPECTED_SILVER_BYTES = 1825


class SiopeHistorical2022P6SilverSingleRecordTransformPreviewTests(unittest.TestCase):
    def _readback_config(self) -> dict:
        return json.loads(READBACK_REVIEW_CONFIG.read_text(encoding="utf-8"))

    def _preview_config(self) -> dict:
        return json.loads(PREVIEW_CONFIG.read_text(encoding="utf-8"))

    def test_pinned_historical_readback_review_passes_offline(self):
        result = review(self._readback_config(), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW")
        self.assertEqual(result["pinned_run_id"], 33073981604)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["silver_authorized"])
        self.assertTrue(result["silver_transform_preview_design_authorized"])

    def test_readback_review_rejects_config_drift(self):
        config = self._readback_config()
        config["pinned_run_id"] += 1
        with self.assertRaises(Historical2022P6BronzeDriveReadbackReviewError):
            review(config, root=ROOT)

    def test_readback_review_rejects_pinned_evidence_byte_drift(self):
        config = self._readback_config()
        source = ROOT / config["pinned_evidence_path"]
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            target = temp_root / config["pinned_evidence_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes() + b" ")
            with self.assertRaises(Historical2022P6BronzeDriveReadbackReviewError):
                review(config, root=temp_root)

    def test_preview_design_is_offline_write_closed_and_single_record_only(self):
        result = validate_config(self._preview_config())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["drive_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["silver_payload_persisted"])
        self.assertFalse(result["silver_remote_write_authorized"])
        self.assertFalse(result["gold_authorized"])

    def test_exact_historical_bronze_builds_expected_lossless_silver_preview(self):
        result = preview(self._preview_config(), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["schema_key_count"], 52)
        self.assertTrue(result["identity_verified"])
        self.assertTrue(result["lossless_record_embedding_verified"])
        self.assertEqual(result["record_sha256"], "79b786f438d29803fe15d513f4ff17d4ab55fde1dd631f503b6752370e21b68a")
        self.assertEqual(result["silver_contract"], "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1")
        self.assertEqual(result["silver_payload_bytes"], EXPECTED_SILVER_BYTES)
        self.assertEqual(result["silver_payload_sha256"], EXPECTED_SILVER_SHA256)
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["silver_payload_persisted"])
        self.assertFalse(result["silver_remote_write_authorized"])
        self.assertFalse(result["gold_authorized"])

    def test_preview_result_does_not_expose_record_values(self):
        result = preview(self._preview_config(), root=ROOT)
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("VAL_DESP_EMPE", rendered)
        self.assertNotIn("DES_DIFE_METO_CALC", rendered)
        self.assertNotIn("1390963706.43", rendered)
        self.assertNotIn("291748", rendered)

    def test_config_drift_cannot_repoint_payloads_or_enable_operations(self):
        cases = (
            ("record_payload_path", "other.json"),
            ("manifest_payload_path", "other.json"),
            ("source_network_authorized", True),
            ("drive_network_authorized", True),
            ("drive_write_count", 1),
            ("silver_payload_persistence_authorized", True),
            ("silver_remote_write_authorized", True),
            ("processing_authorized", True),
            ("gold_authorized", True),
            ("historical_collection_authorized", True),
            ("recurrence_authorized", True),
            ("schedule_enabled", True),
        )
        for field, value in cases:
            config = self._preview_config()
            config[field] = value
            with self.assertRaises(Historical2022P6SilverTransformPreviewError, msg=field):
                validate_config(config)

    def test_identity_hash_and_expected_output_drift_fail_closed(self):
        for mutation in (
            lambda c: c["expected_identity"].update(year=2023),
            lambda c: c.__setitem__("record_sha256", "0" * 64),
            lambda c: c.__setitem__("source_bundle_sha256", "0" * 64),
            lambda c: c.__setitem__("expected_silver_payload_bytes", 1826),
            lambda c: c.__setitem__("expected_silver_payload_sha256", "0" * 64),
        ):
            config = copy.deepcopy(self._preview_config())
            mutation(config)
            with self.assertRaises(Historical2022P6SilverTransformPreviewError):
                validate_config(config)

    def test_gate_scripts_run_directly_from_repo_root(self):
        review_proc = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_bronze_drive_readback_review_gate.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(review_proc.returncode, 0, review_proc.stdout + review_proc.stderr)
        preview_proc = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_silver_single_record_transform_preview_gate.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(preview_proc.returncode, 0, preview_proc.stdout + preview_proc.stderr)

    def test_workflow_is_manual_offline_full_qa_and_no_remote_writes(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2022_p6_silver_single_record_transform_preview", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_bronze_drive_readback_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_silver_single_record_transform_preview_gate.py --dry-run", text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_ID", text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_SECRET", text)
        self.assertNotIn("GOOGLE_DRIVE_REFRESH_TOKEN", text)
        self.assertNotIn("www.fnde.gov.br", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("requests.", text)
        self.assertNotIn("schedule:", text)


if __name__ == "__main__":
    unittest.main()
