import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_journal_text_layer_readiness import (
    LoaJournalTextLayerReadinessError,
    validate_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_034_LOA_JOM_TEXT_LAYER_READINESS_0.8.0.json"


class Task034LoaJomTextLayerReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_exact_evidence_passes(self):
        result = validate_evidence(copy.deepcopy(self.data))
        self.assertEqual(result["status"], "PASS_TASK_034_LOA_JOM_TEXT_LAYER_READINESS")
        self.assertEqual(result["law_pages"], 467)
        self.assertEqual(result["targeted_review_pages"], [475, 476, 477, 478, 479, 480, 481])
        self.assertFalse(result["full_document_ocr_required"])
        self.assertEqual(result["f01_status"], "NOT_SILVER")

    def test_page_481_cannot_be_dropped_from_loa_boundary(self):
        bad = copy.deepcopy(self.data)
        bad["law_boundary"]["end_page"] = 480
        with self.assertRaises(LoaJournalTextLayerReadinessError):
            validate_evidence(bad)

    def test_targeted_review_page_set_is_exact(self):
        bad = copy.deepcopy(self.data)
        bad["text_layer"]["targeted_ocr_or_visual_extraction_required_pages"] = [475, 476, 477, 478, 479, 480]
        with self.assertRaises(LoaJournalTextLayerReadinessError):
            validate_evidence(bad)

    def test_full_document_ocr_cannot_be_promoted(self):
        bad = copy.deepcopy(self.data)
        bad["text_layer"]["full_467_page_journal_law_ocr_required"] = True
        with self.assertRaises(LoaJournalTextLayerReadinessError):
            validate_evidence(bad)

    def test_silver_promotion_remains_blocked(self):
        bad = copy.deepcopy(self.data)
        bad["promotion"]["f01_status"] = "SILVER"
        with self.assertRaises(LoaJournalTextLayerReadinessError):
            validate_evidence(bad)


if __name__ == "__main__":
    unittest.main()
