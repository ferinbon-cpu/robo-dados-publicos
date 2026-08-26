from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_official_olinda_limeira_pilot_readonly_get import (
    SiopeOfficialOlindaLimeiraPilotReadonlyGetError,
    load_config as load_pilot_config,
    run_pilot_get,
    validate_design,
)
from robo_dados_publicos.sources.siope_official_olinda_minimal_readonly_get_review import (
    SiopeOfficialOlindaMinimalReadonlyGetReviewError,
    load_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_minimal_readonly_get_review.json"
PILOT_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_limeira_pilot_readonly_get_design.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-limeira-pilot-readonly-get-gate.yml"


class FakeResponse:
    def __init__(self, payload: dict, *, url: str, status: int = 200, content_type: str = "application/json"):
        self._raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int = -1) -> bytes:
        return self._raw if size < 0 else self._raw[:size]

    def geturl(self) -> str:
        return self.url

    def getcode(self) -> int:
        return self.status


class LimeiraPilotReadonlyGetTests(unittest.TestCase):
    def test_pinned_minimal_get_review_passes_offline(self):
        config = load_json(REVIEW_CONFIG)
        evidence_path = ROOT / config["pinned_evidence_path"]
        result = run_review(config, load_json(evidence_path), evidence_path=evidence_path)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_REVIEW")
        self.assertEqual(result["executable_contract_status"], "PROVEN_FOR_EXACT_RESOURCE_AND_PARAMETER_SHAPE_ON_PINNED_MANUAL_RUN")
        self.assertTrue(result["required_limeira_pilot_schema_keys_observed"])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["ongoing_resource_get_authorized"])

    def test_pinned_review_rejects_tampered_evidence(self):
        config = load_json(REVIEW_CONFIG)
        evidence_path = ROOT / config["pinned_evidence_path"]
        evidence = load_json(evidence_path)
        tampered = copy.deepcopy(evidence)
        tampered["result"]["value_count"] = 185
        with self.assertRaises(SiopeOfficialOlindaMinimalReadonlyGetReviewError):
            run_review(config, tampered, evidence_path=evidence_path)

    def test_review_and_pilot_scripts_run_directly_from_repo_root(self):
        review = subprocess.run(
            [sys.executable, "scripts/github_siope_official_olinda_minimal_readonly_get_review_gate.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(review.returncode, 0, review.stderr)
        self.assertEqual(json.loads(review.stdout)["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_REVIEW")
        dry = subprocess.run(
            [sys.executable, "scripts/github_siope_official_olinda_limeira_pilot_readonly_get_gate.py", "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(dry.returncode, 0, dry.stderr)
        payload = json.loads(dry.stdout)
        self.assertEqual(payload["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_DESIGN")
        self.assertFalse(payload["network_called"])

    def test_design_is_exact_filtered_selected_and_keeps_operations_closed(self):
        config = load_pilot_config(PILOT_CONFIG)
        result = validate_design(config)
        self.assertIn("$filter=COD_MUNI%20eq%20352690", config["exact_url"])
        self.assertIn("$select=COD_MUNI,NOM_MUNI,NUM_ANO,NUM_PERI,SIG_UF", config["exact_url"])
        self.assertNotIn("+", config["exact_url"])
        self.assertEqual(config["selected_fields"], ["COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"])
        self.assertFalse(config["collection_authorized"])
        self.assertFalse(config["processing_authorized"])
        self.assertFalse(config["recurrence_authorized"])
        self.assertFalse(config["schedule_enabled"])
        self.assertEqual(result["selected_field_count"], 5)
        self.assertTrue(result["server_side_filter_required"])
        self.assertTrue(result["server_side_select_required"])

    def test_mocked_live_success_is_one_get_identity_checked_and_sanitized(self):
        config = load_pilot_config(PILOT_CONFIG)
        calls = []
        payload = {
            "@odata.context": "context-not-persisted-by-result",
            "value": [
                {
                    "COD_MUNI": 352690,
                    "NOM_MUNI": "Limeira",
                    "NUM_ANO": 2024,
                    "NUM_PERI": 6,
                    "SIG_UF": "SP",
                }
            ],
        }

        def opener(req, timeout):
            calls.append((req.get_method(), req.full_url, timeout))
            return FakeResponse(payload, url=config["exact_url"])

        result = run_pilot_get(config, opener=opener)
        self.assertEqual(calls, [("GET", config["exact_url"], 20)])
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET")
        self.assertEqual(result["request_count"], 1)
        self.assertTrue(result["pilot_limeira_values_sent"])
        self.assertTrue(result["selected_schema_exact"])
        self.assertTrue(result["all_records_match_municipality_code"])
        self.assertTrue(result["all_records_match_municipality_name"])
        self.assertTrue(result["all_records_match_year"])
        self.assertTrue(result["all_records_match_period"])
        self.assertTrue(result["all_records_match_state"])
        self.assertFalse(result["response_body_persisted"])
        self.assertFalse(result["record_values_persisted"])
        self.assertFalse(result["query_values_persisted_in_result"])
        self.assertFalse(result["ongoing_resource_get_authorized"])
        self.assertFalse(result["collection_authorized"])

    def test_identity_mismatch_fails_closed(self):
        config = load_pilot_config(PILOT_CONFIG)
        payload = {
            "value": [
                {
                    "COD_MUNI": 352680,
                    "NOM_MUNI": "Limeira",
                    "NUM_ANO": 2024,
                    "NUM_PERI": 6,
                    "SIG_UF": "SP",
                }
            ]
        }
        with self.assertRaises(SiopeOfficialOlindaLimeiraPilotReadonlyGetError):
            run_pilot_get(config, opener=lambda req, timeout: FakeResponse(payload, url=config["exact_url"]))

    def test_select_drift_or_nextlink_fails_closed(self):
        config = load_pilot_config(PILOT_CONFIG)
        drift = {
            "value": [
                {
                    "COD_MUNI": 352690,
                    "NOM_MUNI": "Limeira",
                    "NUM_ANO": 2024,
                    "NUM_PERI": 6,
                    "SIG_UF": "SP",
                    "VAL_RECE_REAL": 1,
                }
            ]
        }
        with self.assertRaises(SiopeOfficialOlindaLimeiraPilotReadonlyGetError):
            run_pilot_get(config, opener=lambda req, timeout: FakeResponse(drift, url=config["exact_url"]))
        nextlink = {
            "@odata.nextLink": "not-persisted",
            "value": [
                {
                    "COD_MUNI": 352690,
                    "NOM_MUNI": "Limeira",
                    "NUM_ANO": 2024,
                    "NUM_PERI": 6,
                    "SIG_UF": "SP",
                }
            ],
        }
        with self.assertRaises(SiopeOfficialOlindaLimeiraPilotReadonlyGetError):
            run_pilot_get(config, opener=lambda req, timeout: FakeResponse(nextlink, url=config["exact_url"]))

    def test_workflow_is_manual_readonly_full_qa_and_sanitized(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_limeira_pilot_readonly_get", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("python scripts/github_siope_official_olinda_minimal_readonly_get_review_gate.py", text)
        self.assertIn("python scripts/github_siope_official_olinda_limeira_pilot_readonly_get_gate.py --dry-run", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        live = "python scripts/github_siope_official_olinda_limeira_pilot_readonly_get_gate.py --output"
        self.assertIn(live, text)
        self.assertLess(text.index("python main.py selftest"), text.index(live))
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertIn("result.json", text)
        for forbidden in ["schedule:", "cron:", "curl ", "wget ", "gh workflow run", "google drive", "POST ", "HEAD "]:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
