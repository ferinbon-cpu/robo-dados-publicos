from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.sources.siope_client_limeira_bronze_single_record_capture import BronzeCaptureError, capture, validate_config
from robo_dados_publicos.sources.siope_client_limeira_full_schema_readonly_validation_review import load_json, run_review

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/source_expansion.siope_client_limeira_bronze_single_record_capture.json"
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_full_schema_readonly_validation_review.json"
EVIDENCE = ROOT / "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_RUN_1_0.8.0.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-bronze-single-record-capture-gate.yml"


class FakeResponse:
    def __init__(self, url: str, payload: dict):
        self.url = url
        self.status = 200
        self.headers = {"Content-Type": "application/json"}
        self._raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def geturl(self): return self.url
    def getcode(self): return self.status
    def read(self, _limit): return self._raw


def full_record() -> dict:
    record = {field: None for field in PROVEN_DADOS_GERAIS_FIELDS}
    record.update({"COD_MUNI": 352690, "NOM_MUNI": "Limeira", "NUM_ANO": 2024, "NUM_PERI": 6, "SIG_UF": "SP"})
    return record


class BronzeSingleRecordCaptureTests(unittest.TestCase):
    def test_pinned_full_schema_review_passes_offline(self):
        result = run_review(load_json(REVIEW_CONFIG), load_json(EVIDENCE), evidence_path=EVIDENCE)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_REVIEW")
        self.assertFalse(result["recurring_collection_authorized"])

    def test_design_is_exact_single_capture_only(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        result = validate_config(config)
        self.assertTrue(result["single_collection_authorized"])
        self.assertFalse(result["recurring_collection_authorized"])
        self.assertFalse(result["processing_authorized"])

    def test_mocked_capture_persists_exact_public_record_and_manifest(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        holder = {}
        def opener(req, _timeout):
            holder["url"] = req.full_url
            return FakeResponse(req.full_url, {"@odata.context": "x", "value": [full_record()]})
        with tempfile.TemporaryDirectory() as tmp:
            result = capture(config, output_dir=tmp, opener=opener)
            record = json.loads((Path(tmp) / "record.json").read_text(encoding="utf-8"))
            manifest = json.loads((Path(tmp) / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE")
        self.assertEqual(set(record), set(PROVEN_DADOS_GERAIS_FIELDS))
        self.assertEqual(record["COD_MUNI"], 352690)
        self.assertEqual(manifest["record_count"], 1)
        self.assertEqual(manifest["schema_key_count"], 52)
        self.assertFalse(manifest["processing_authorized"])
        self.assertIn("$filter=COD_MUNI%20eq%20352690", holder["url"])

    def test_identity_drift_fails_closed_before_persistence(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        bad = full_record(); bad["COD_MUNI"] = 999999
        def opener(req, _timeout): return FakeResponse(req.full_url, {"value": [bad]})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(BronzeCaptureError):
                capture(config, output_dir=tmp, opener=opener)
            self.assertFalse((Path(tmp) / "record.json").exists())

    def test_workflow_is_manual_one_get_no_recurrence_or_processing(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", text)
        self.assertIn("confirm_siope_client_limeira_bronze_single_record_capture", text)
        self.assertIn("Revisar evidência pinada dos 52 campos", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("--retry", text)
        self.assertNotIn("silver", text.lower())
        self.assertNotIn("gold", text.lower())


if __name__ == "__main__":
    unittest.main()
