import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_journal_targeted_ocr_review import (
    TargetedOcrReviewError,
    validate_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_037_LOA_JOM_TARGETED_OCR_REVIEW_0.8.0.json"


class Task037TargetedOcrReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_valid_evidence_passes(self):
        result = validate_evidence(copy.deepcopy(self.evidence))
        self.assertEqual(result["status"], "PASS_TASK_037_LOA_JOM_TARGETED_OCR_REVIEW")
        self.assertEqual(result["numeric_table_review_pages"], [480, 481])
        self.assertEqual(result["f01_status"], "NOT_SILVER")

    def test_rejects_source_hash_drift(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["source"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(TargetedOcrReviewError, "SOURCE_SHA256_MISMATCH"):
            validate_evidence(evidence)

    def test_rejects_ocr_config_drift(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["ocr"]["psm"] = 4
        with self.assertRaisesRegex(TargetedOcrReviewError, "OCR_PSM_MISMATCH"):
            validate_evidence(evidence)

    def test_rejects_nonrepeatable_ocr(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["manifest"]["repeatability"]["all_page_text_hashes_identical"] = False
        with self.assertRaisesRegex(TargetedOcrReviewError, "OCR_NOT_REPEATABLE"):
            validate_evidence(evidence)

    def test_rejects_manifest_mutation(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["manifest"]["rows"][5]["ocr_text_chars"] = 999
        with self.assertRaisesRegex(TargetedOcrReviewError, "MANIFEST_ROWS_HASH_MISMATCH"):
            validate_evidence(evidence)

    def test_rejects_silver_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["promotion"]["silver"] = True
        with self.assertRaisesRegex(TargetedOcrReviewError, "PROMOTION_SILVER_WEAKENED"):
            validate_evidence(evidence)

    def test_rejects_llm_numeric_reconstruction(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["policy"]["llm_numeric_reconstruction"] = True
        with self.assertRaisesRegex(TargetedOcrReviewError, "POLICY_LLM_NUMERIC_RECONSTRUCTION_WEAKENED"):
            validate_evidence(evidence)


if __name__ == "__main__":
    unittest.main()
