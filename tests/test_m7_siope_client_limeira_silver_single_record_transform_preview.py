from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_bronze_drive_readback_review import (
    BronzeDriveReadbackReviewError,
    review,
)
from robo_dados_publicos.sources.siope_client_limeira_silver_single_record_transform_preview import (
    SilverTransformPreviewError,
    preview,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
READBACK_REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_bronze_drive_readback_review.json"
PREVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_silver_single_record_transform_preview.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-silver-single-record-transform-preview-gate.yml"


class SiopeSilverSingleRecordTransformPreviewTests(unittest.TestCase):
    def _readback_config(self) -> dict:
        return json.loads(READBACK_REVIEW_CONFIG.read_text(encoding="utf-8"))

    def _preview_config(self) -> dict:
        return json.loads(PREVIEW_CONFIG.read_text(encoding="utf-8"))

    def test_pinned_readback_review_passes_offline(self):
        result = review(self._readback_config(), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_REVIEW")
        self.assertEqual(result["pinned_run_id"], 33018602293)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["silver_authorized"])
        self.assertTrue(result["silver_transform_preview_design_authorized"])

    def test_readback_review_rejects_tampered_pinned_identity(self):
        config = self._readback_config()
        config["pinned_run_id"] += 1
        with self.assertRaises(BronzeDriveReadbackReviewError):
            review(config, root=ROOT)

    def test_preview_design_is_offline_and_write_closed(self):
        result = validate_config(self._preview_config())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["drive_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["silver_payload_persisted"])
        self.assertFalse(result["silver_remote_write_authorized"])

    def test_exact_bronze_record_builds_lossless_silver_preview(self):
        result = preview(self._preview_config(), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW")
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["schema_key_count"], 52)
        self.assertTrue(result["identity_verified"])
        self.assertTrue(result["lossless_record_embedding_verified"])
        self.assertEqual(result["record_sha256"], "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6")
        self.assertRegex(result["silver_payload_sha256"], r"^[0-9a-f]{64}$")
        self.assertGreater(result["silver_payload_bytes"], 0)
        self.assertFalse(result["silver_payload_persisted"])
        self.assertFalse(result["silver_remote_write_authorized"])

    def test_preview_result_does_not_expose_record_values(self):
        result = preview(self._preview_config(), root=ROOT)
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("VAL_DESP_EMPE", rendered)
        self.assertNotIn("DES_DIFE_METO_CALC", rendered)
        self.assertNotIn("2266806406.55", rendered)
        self.assertNotIn("389415", rendered)

    def test_identity_drift_fails_closed(self):
        record_path = ROOT / self._preview_config()["record_payload_path"]
        original = json.loads(record_path.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(original)
        tampered["COD_MUNI"] = 999999
        temp_path = ROOT / "tests/fixtures/_tmp_siope_silver_preview_tampered.json"
        try:
            temp_path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
            config = self._preview_config()
            config["record_payload_path"] = str(temp_path.relative_to(ROOT)).replace("\\", "/")
            with self.assertRaises(SilverTransformPreviewError):
                preview(config, root=ROOT)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_schema_drift_fails_closed(self):
        record_path = ROOT / self._preview_config()["record_payload_path"]
        original = json.loads(record_path.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(original)
        tampered.pop("VAL_DESP_EMPE")
        temp_path = ROOT / "tests/fixtures/_tmp_siope_silver_preview_schema.json"
        try:
            temp_path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
            config = self._preview_config()
            config["record_payload_path"] = str(temp_path.relative_to(ROOT)).replace("\\", "/")
            with self.assertRaises(SilverTransformPreviewError):
                preview(config, root=ROOT)
        finally:
            temp_path.unlink(missing_ok=True)

    def test_config_drift_cannot_enable_remote_or_derived_operations(self):
        for field, value in (
            ("drive_network_authorized", True),
            ("silver_payload_persistence_authorized", True),
            ("silver_remote_write_authorized", True),
            ("processing_authorized", True),
            ("gold_authorized", True),
            ("recurrence_authorized", True),
            ("schedule_enabled", True),
        ):
            config = self._preview_config()
            config[field] = value
            with self.assertRaises(SilverTransformPreviewError, msg=field):
                validate_config(config)

    def test_gate_scripts_run_directly_from_repo_root(self):
        review_proc = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_bronze_drive_readback_review_gate.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(review_proc.returncode, 0, review_proc.stdout + review_proc.stderr)
        preview_proc = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_silver_single_record_transform_preview_gate.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(preview_proc.returncode, 0, preview_proc.stdout + preview_proc.stderr)

    def test_workflow_is_manual_offline_full_qa_and_no_drive_write(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_silver_single_record_transform_preview", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("github_siope_client_limeira_bronze_drive_readback_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_silver_single_record_transform_preview_gate.py --dry-run", text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_ID", text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_SECRET", text)
        self.assertNotIn("GOOGLE_DRIVE_REFRESH_TOKEN", text)
        self.assertNotIn("www.fnde.gov.br", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("requests.", text)
        self.assertNotIn("schedule:", text)


if __name__ == "__main__":
    unittest.main()
