import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_journal_page_aware_parser import (
    LoaJournalPageAwareParserError,
    classify_page,
    extract_brl_candidates,
    extract_exact_action_codes,
    parse_pages,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]


class Task035LoaJournalPageAwareParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "config/loa_journal_page_aware_parser.v1.json").read_text(encoding="utf-8"))
        cls.fixture = json.loads((ROOT / "tests/fixtures/task_035_loa_journal_parser_preview.json").read_text(encoding="utf-8"))

    def test_contract_passes(self):
        self.assertEqual(validate_contract(self.contract)["status"], "PASS_TASK_035_CONTRACT")

    def test_page_policy_is_fail_closed(self):
        self.assertEqual(classify_page(375), "SKIP_BLANK")
        self.assertEqual(classify_page(475), "REVIEW_REQUIRED_TARGETED_EXTRACTION")
        self.assertEqual(classify_page(171), "PARSE_TEXT_LAYER_CANDIDATES")
        with self.assertRaises(LoaJournalPageAwareParserError):
            classify_page(482)

    def test_exact_code_is_parsed_without_repair(self):
        page = next(x for x in self.fixture["records"] if x["page"] == 171)
        self.assertEqual(extract_exact_action_codes(page["text"]), ["12.362.2001.2690"])

    def test_corrupted_code_is_not_silently_reconstructed(self):
        result = parse_pages([next(x for x in self.fixture["records"] if x["page"] == 174)])
        row = result["pages"][0]
        self.assertEqual(row["action_codes"], [])
        self.assertEqual(row["status"], "REVIEW_REQUIRED_CODE_CORRUPTION")
        self.assertFalse(result["promotion_authorized"])

    def test_numeric_candidates_are_never_final(self):
        candidates = extract_brl_candidates("R$ 2.303.934.000,00 e 6.152. 000,00")
        self.assertEqual(candidates[0]["cents"], 230393400000)
        self.assertTrue(all(x["status"] == "OCR_TEXT_NUMERIC_CANDIDATE_UNVERIFIED" for x in candidates))
        self.assertTrue(all(x["auto_promotable"] is False for x in candidates))

    def test_blank_and_targeted_pages_do_not_emit_numeric_candidates(self):
        records = [x for x in self.fixture["records"] if x["page"] in (375, 475)]
        rows = parse_pages(records)["pages"]
        self.assertEqual(rows[0]["status"], "SKIP_BLANK")
        self.assertEqual(rows[1]["status"], "REVIEW_REQUIRED_TARGETED_EXTRACTION")
        self.assertEqual(rows[0]["numeric_candidates"], [])
        self.assertEqual(rows[1]["numeric_candidates"], [])

    def test_visual_review_records_material_ocr_drift(self):
        review = self.fixture["visual_review"]
        self.assertEqual(review["page_171"]["text_visual_status"], "AGREEMENT")
        self.assertEqual(review["page_173"]["text_visual_status"], "NUMERIC_DRIFT")
        self.assertEqual(review["page_174"]["text_visual_status"], "CODE_AND_NUMERIC_DRIFT")
        self.assertNotEqual(review["page_174"]["visual_amount_brl"], review["page_174"]["ocr_text_amount_brl"])


if __name__ == "__main__":
    unittest.main()
