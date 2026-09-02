import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_scoped_silver_candidate_review import (
    Task039Error,
    validate_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
E39 = ROOT / "docs/evidence/TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW_0.8.0.json"
E36 = ROOT / "docs/evidence/TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST_0.8.0.json"
E37 = ROOT / "docs/evidence/TASK_037_LOA_JOM_TARGETED_OCR_REVIEW_0.8.0.json"
E38 = ROOT / "docs/evidence/TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION_0.8.0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class Task039Tests(unittest.TestCase):
    def setUp(self):
        self.e39 = load(E39)
        self.e36 = load(E36)
        self.e37 = load(E37)
        self.e38 = load(E38)

    def validate(self, e39=None, e36=None, e37=None, e38=None):
        return validate_candidate(e39 or self.e39, e36 or self.e36, e37 or self.e37, e38 or self.e38)

    def test_candidate_passes(self):
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW")
        self.assertEqual(result["f01_status"], "NOT_SILVER")
        self.assertIn("SEPARATE_AUTH_REQUIRED", result["readiness"])

    def test_complete_loa_claim_fails(self):
        value = copy.deepcopy(self.e39)
        value["candidate_payload"]["guardrails"]["complete_loa_parse_claim"] = True
        with self.assertRaises(Task039Error):
            self.validate(e39=value)

    def test_silver_promotion_fails(self):
        value = copy.deepcopy(self.e39)
        value["promotion"]["silver"] = True
        with self.assertRaises(Task039Error):
            self.validate(e39=value)

    def test_remote_write_authorization_fails(self):
        value = copy.deepcopy(self.e39)
        value["readiness"]["remote_write_authorized"] = True
        with self.assertRaises(Task039Error):
            self.validate(e39=value)

    def test_eiti_financial_identity_strengthening_fails(self):
        value = copy.deepcopy(self.e39)
        value["candidate_payload"]["guardrails"]["eiti_financial_identity"] = "PROVEN"
        with self.assertRaises(Task039Error):
            self.validate(e39=value)

    def test_ocr_candidate_page_cannot_become_canonical_silently(self):
        value = copy.deepcopy(self.e39)
        value["candidate_payload"]["coverage"]["ocr_candidate_text_excluded_from_canonical_text"] = [475,476,477,478]
        with self.assertRaises(Task039Error):
            self.validate(e39=value)

    def test_task036_pin_drift_fails(self):
        upstream = copy.deepcopy(self.e36)
        upstream["manifest"]["rows_sha256"] = "0" * 64
        with self.assertRaises(Task039Error):
            self.validate(e36=upstream)

    def test_task037_repeatability_weakening_fails(self):
        upstream = copy.deepcopy(self.e37)
        upstream["manifest"]["repeatability"]["all_page_text_hashes_identical"] = False
        with self.assertRaises(Task039Error):
            self.validate(e37=upstream)

    def test_task038_numeric_truth_weakening_fails(self):
        upstream = copy.deepcopy(self.e38)
        upstream["policy"]["ocr_used_as_numeric_source_truth"] = True
        with self.assertRaises(Task039Error):
            self.validate(e38=upstream)


if __name__ == "__main__":
    unittest.main()
