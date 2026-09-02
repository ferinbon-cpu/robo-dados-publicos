import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_journal_numeric_table_validation import (
    Task038Error, validate_evidence
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION_0.8.0.json"

class Task038Tests(unittest.TestCase):
    def load(self):
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_evidence_passes(self):
        result = validate_evidence(self.load())
        self.assertEqual(result["status"], "PASS_TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION")
        self.assertEqual(result["page_480_total_brl"], "128600000.00")
        self.assertEqual(result["page_481_rows"], 11)
        self.assertEqual(result["f01_status"], "NOT_SILVER")

    def test_fails_if_page_480_value_changes(self):
        value = self.load()
        value["page_480"]["rows"][0]["amount_brl"] = "45933001.00"
        with self.assertRaises(Task038Error):
            validate_evidence(value)

    def test_fails_if_silver_promoted(self):
        value = self.load()
        value["promotion"]["silver"] = True
        with self.assertRaises(Task038Error):
            validate_evidence(value)

    def test_fails_if_ocr_becomes_numeric_truth(self):
        value = self.load()
        value["policy"]["ocr_used_as_numeric_source_truth"] = True
        with self.assertRaises(Task038Error):
            validate_evidence(value)

    def test_fails_if_eiti_identity_is_strengthened(self):
        value = self.load()
        value["policy"]["financial_identity_eiti"] = "PROVEN"
        with self.assertRaises(Task038Error):
            validate_evidence(value)

if __name__ == "__main__":
    unittest.main()
