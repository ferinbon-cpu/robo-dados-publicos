from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_bronze_single_record_capture import (
    Historical2023P6BronzeCaptureError,
    capture,
    validate_config,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_full_schema_readonly_validation_review import (
    Historical2023P6ValidationReviewError,
    load_json as load_review_json,
    review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_full_schema_readonly_validation_review.json"
CAPTURE_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_bronze_single_record_capture.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2023-p6-bronze-single-record-capture-gate.yml"


class FakeResponse:
    def __init__(self, payload: dict, *, url: str, content_type: str = "application/json", status: int = 200):
        self._raw = json.dumps(payload).encode("utf-8")
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def read(self, n: int = -1):
        return self._raw if n < 0 else self._raw[:n]


def full_record_2023() -> dict:
    record = {field: None for field in PROVEN_DADOS_GERAIS_FIELDS}
    record.update({
        "COD_MUNI": 352690,
        "NOM_MUNI": "Limeira",
        "NUM_ANO": 2023,
        "NUM_PERI": 6,
        "SIG_UF": "SP",
    })
    return record


def opener_for(payload: dict):
    return lambda req, timeout: FakeResponse(payload, url=req.full_url)


class Historical2023P6BronzeCaptureTests(unittest.TestCase):
    def test_pinned_historical_validation_review_passes_offline(self):
        result = review(load_review_json(REVIEW_CONFIG), root=ROOT)
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW",
        )
        self.assertEqual(result["pinned_year"], 2023)
        self.assertEqual(result["selected_schema_key_count"], 52)
        self.assertTrue(result["bronze_single_record_capture_design_authorized"])
        self.assertFalse(result["historical_collection_authorized"])

    def test_review_rejects_config_drift(self):
        config = copy.deepcopy(load_review_json(REVIEW_CONFIG))
        config["pinned_run_id"] += 1
        with self.assertRaisesRegex(Historical2023P6ValidationReviewError, "CONFIG_DRIFT"):
            review(config, root=ROOT)

    def test_review_rejects_evidence_blob_drift(self):
        config = load_review_json(REVIEW_CONFIG)
        original = (ROOT / config["pinned_evidence_path"]).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / config["pinned_evidence_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = json.loads(original)
            payload["response_byte_count"] += 1
            target.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(Historical2023P6ValidationReviewError, "EVIDENCE_BLOB_DRIFT"):
                review(config, root=root)

    def test_capture_design_is_exact_and_remote_write_closed(self):
        config = json.loads(CAPTURE_CONFIG.read_text(encoding="utf-8"))
        result = validate_config(config)
        self.assertEqual(result["target_year"], 2023)
        self.assertEqual(result["target_period"], 6)
        self.assertFalse(result["network_called"])
        self.assertTrue(result["single_historical_record_capture_authorized"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["drive_persistence_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])

    def test_capture_config_drift_cannot_enable_bulk_drive_or_recurrence(self):
        base = json.loads(CAPTURE_CONFIG.read_text(encoding="utf-8"))
        for key in ("historical_collection_authorized", "drive_persistence_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
            config = copy.deepcopy(base)
            config[key] = True
            with self.subTest(key=key), self.assertRaises(Historical2023P6BronzeCaptureError):
                validate_config(config)

    def test_mocked_capture_persists_exact_public_record_and_manifest(self):
        config = json.loads(CAPTURE_CONFIG.read_text(encoding="utf-8"))
        record = full_record_2023()
        payload = {"@odata.context": "sanitized-test-context", "value": [record]}
        with tempfile.TemporaryDirectory() as td:
            result = capture(config, output_dir=td, opener=opener_for(payload))
            persisted = json.loads((Path(td) / "record.json").read_text(encoding="utf-8"))
            manifest = json.loads((Path(td) / "manifest.json").read_text(encoding="utf-8"))
            canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            expected_sha = hashlib.sha256(canonical).hexdigest()
            self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE")
            self.assertEqual(result["request_count"], 1)
            self.assertEqual(result["selected_schema_key_count"], 52)
            self.assertEqual(persisted, record)
            self.assertEqual(manifest["year"], 2023)
            self.assertEqual(manifest["period"], 6)
            self.assertEqual(manifest["record_sha256"], expected_sha)
            self.assertEqual(result["record_sha256"], expected_sha)
            self.assertFalse(manifest["drive_persistence_authorized"])
            self.assertFalse(manifest["historical_collection_authorized"])

    def test_capture_schema_drift_fails_closed(self):
        config = json.loads(CAPTURE_CONFIG.read_text(encoding="utf-8"))
        record = full_record_2023()
        record.pop("VAL_PIB")
        with tempfile.TemporaryDirectory() as td, self.assertRaisesRegex(Historical2023P6BronzeCaptureError, "SCHEMA"):
            capture(config, output_dir=td, opener=opener_for({"value": [record]}))

    def test_capture_identity_drift_fails_closed(self):
        config = json.loads(CAPTURE_CONFIG.read_text(encoding="utf-8"))
        for key, wrong in (("COD_MUNI", 1), ("NUM_ANO", 2024), ("NUM_PERI", 5), ("SIG_UF", "RJ")):
            record = full_record_2023()
            record[key] = wrong
            with tempfile.TemporaryDirectory() as td, self.subTest(key=key), self.assertRaises(Historical2023P6BronzeCaptureError):
                capture(config, output_dir=td, opener=opener_for({"value": [record]}))

    def test_gate_scripts_run_directly_without_live_network(self):
        commands = [
            [sys.executable, "scripts/github_siope_client_limeira_historical_2023_p6_full_schema_readonly_validation_review_gate.py"],
            [sys.executable, "scripts/github_siope_client_limeira_historical_2023_p6_bronze_single_record_capture_gate.py", "--dry-run"],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_workflow_is_manual_one_get_local_capture_and_no_drive(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2023_p6_bronze_single_record_capture", text)
        self.assertIn("contents: read", text)
        self.assertIn("github_siope_client_limeira_historical_2023_p6_full_schema_readonly_validation_review_gate.py", text)
        self.assertIn("--dry-run", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("continue-on-error: true", text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertNotIn("GOOGLE_DRIVE_", text)
        self.assertNotIn("upload_file", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("rerun", text.lower())

    def test_workflow_orders_review_and_full_qa_before_capture(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        review_at = text.index("github_siope_client_limeira_historical_2023_p6_full_schema_readonly_validation_review_gate.py")
        tests_at = text.index("python -m unittest discover -s tests -v")
        selftest_at = text.index("python main.py selftest")
        live_at = text.index("Capturar exatamente um registro Bronze de Limeira 2023 P6")
        self.assertLess(review_at, tests_at)
        self.assertLess(tests_at, selftest_at)
        self.assertLess(selftest_at, live_at)


if __name__ == "__main__":
    unittest.main()
