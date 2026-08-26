from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client import PROVEN_DADOS_GERAIS_FIELDS
from robo_dados_publicos.sources.siope_client_limeira_full_schema_readonly_validation import (
    SiopeClientLimeiraFullSchemaReadonlyValidationError,
    run_validation,
    validate_config,
)
from robo_dados_publicos.sources.siope_client_limeira_live_validation_review import (
    SiopeClientLimeiraLiveValidationReviewError,
    load_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_live_validation_review.json"
FULL_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_full_schema_readonly_validation.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-full-schema-readonly-validation-gate.yml"


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


def full_record() -> dict:
    record = {field: None for field in PROVEN_DADOS_GERAIS_FIELDS}
    record.update(
        {
            "COD_MUNI": 352690,
            "NOM_MUNI": "Limeira",
            "NUM_ANO": 2024,
            "NUM_PERI": 6,
            "SIG_UF": "SP",
        }
    )
    return record


def opener_for(payload: dict):
    return lambda req, timeout: FakeResponse(payload, url=req.full_url)


class SiopeClientFullSchemaValidationTests(unittest.TestCase):
    def test_pinned_generic_client_review_passes_offline(self):
        config = load_json(REVIEW_CONFIG)
        evidence_path = ROOT / config["pinned_evidence_path"]
        result = run_review(config, load_json(evidence_path), evidence_path=evidence_path)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_REVIEW")
        self.assertEqual(result["generic_client_live_status"], "PROVEN_LIMEIRA_352690_SP_2024_6")
        self.assertFalse(result["collection_authorized"])

    def test_review_rejects_config_identity_drift(self):
        config = load_json(REVIEW_CONFIG)
        config = copy.deepcopy(config)
        config["pinned_run_id"] += 1
        evidence_path = ROOT / config["pinned_evidence_path"]
        with self.assertRaises(SiopeClientLimeiraLiveValidationReviewError):
            run_review(config, load_json(evidence_path), evidence_path=evidence_path)

    def test_full_schema_design_is_network_free_and_exact_52(self):
        config = json.loads(FULL_CONFIG.read_text(encoding="utf-8"))
        result = validate_config(config)
        self.assertEqual(len(PROVEN_DADOS_GERAIS_FIELDS), 52)
        self.assertEqual(result["proven_schema_allowlist_count"], 52)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["record_values_may_be_persisted"])

    def test_mocked_full_schema_success_is_sanitized(self):
        config = json.loads(FULL_CONFIG.read_text(encoding="utf-8"))
        payload = {"@odata.context": "sanitized-test-context", "value": [full_record()]}
        result = run_validation(config, opener=opener_for(payload))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION")
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(result["selected_schema_key_count"], 52)
        self.assertTrue(result["selected_schema_exact"])
        self.assertFalse(result["record_values_persisted"])
        self.assertFalse(result["response_body_persisted"])
        self.assertFalse(result["collection_authorized"])

    def test_missing_full_schema_field_fails_closed(self):
        config = json.loads(FULL_CONFIG.read_text(encoding="utf-8"))
        record = full_record()
        record.pop("VAL_PIB")
        payload = {"@odata.context": "sanitized-test-context", "value": [record]}
        with self.assertRaisesRegex(SiopeClientLimeiraFullSchemaReadonlyValidationError, "FULL_SCHEMA_DRIFT"):
            run_validation(config, opener=opener_for(payload))

    def test_identity_drift_fails_closed_even_with_52_fields(self):
        config = json.loads(FULL_CONFIG.read_text(encoding="utf-8"))
        record = full_record()
        record["COD_MUNI"] = 1
        payload = {"@odata.context": "sanitized-test-context", "value": [record]}
        with self.assertRaisesRegex(SiopeClientLimeiraFullSchemaReadonlyValidationError, "IDENTITY_MISMATCH"):
            run_validation(config, opener=opener_for(payload))

    def test_scripts_run_directly_without_live_network(self):
        commands = [
            [sys.executable, "scripts/github_siope_client_limeira_live_validation_review_gate.py"],
            [sys.executable, "scripts/github_siope_client_limeira_full_schema_readonly_validation_gate.py", "--dry-run"],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_workflow_is_manual_readonly_full_qa_and_sanitized(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_full_schema_readonly_validation", text)
        self.assertIn("contents: read", text)
        self.assertIn("github_siope_client_limeira_live_validation_review_gate.py", text)
        self.assertIn("--dry-run", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("continue-on-error: true", text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("rerun", text.lower())


if __name__ == "__main__":
    unittest.main()
