import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_journal_page_manifest import (
    EXPECTED_ACTION_INDEX_SHA256,
    LoaJournalPageManifestError,
    action_code_index_sha256,
    build_page_manifest,
    detect_corrupted_action_code_candidate_strict,
    summarize,
    validate_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST_0.8.0.json"
ACTION_INDEX = ROOT / "docs/evidence/TASK_036_LOA_JOM_ACTION_CODE_INDEX_0.8.0.json"


class Task036LoaJomPageManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.action_index = json.loads(ACTION_INDEX.read_text(encoding="utf-8"))

    def test_action_index_canonical_digest_is_pinned(self):
        actual = action_code_index_sha256(self.action_index)
        self.assertEqual(
            actual,
            EXPECTED_ACTION_INDEX_SHA256,
            f"actual={actual} expected={EXPECTED_ACTION_INDEX_SHA256}",
        )

    def test_pinned_evidence_passes(self):
        result = validate_evidence(copy.deepcopy(self.evidence), copy.deepcopy(self.action_index))
        self.assertEqual(result["status"], "PASS_TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST")
        self.assertEqual(result["row_count"], 467)
        self.assertEqual(result["code_corruption_review_pages"], [174])
        self.assertEqual(result["targeted_review_pages"], [475, 476, 477, 478, 479, 480, 481])
        self.assertEqual(result["f01_status"], "NOT_SILVER")

    def test_strict_corruption_detector_keeps_observed_page_174_case(self):
        text = "112. 30 6 . 2001. 2 ~20 ALIMENTACAO ESCOLAR"
        self.assertTrue(detect_corrupted_action_code_candidate_strict(text))

    def test_strict_corruption_detector_rejects_page_392_style_false_positive(self):
        text = (
            "1 2001 EDUCACAO QUE INCLUI E TRANSFORMA VIDAS\n"
            "I P ~oclut o (Unicl a cle el e Me clicl a )\n"
            "V4lo ~ I\n"
            "12 690 TRANSPORTE ESCOLAR\n"
            "111.614.000,00"
        )
        self.assertFalse(detect_corrupted_action_code_candidate_strict(text))

    def test_builder_is_complete_page_span_and_fail_closed(self):
        records = [{"page": page, "text": ""} for page in range(15, 482)]
        by_page = {row["page"]: row for row in records}
        by_page[171]["text"] = "12.362.2001.2690 TRANSPORTE ESCOLAR 6.152.000,00"
        by_page[174]["text"] = "112. 30 6 . 2001. 2 ~20 ALIMENTACAO ESCOLAR 29.000.000,00"
        by_page[392]["text"] = "1 2001 EDUCACAO I P ~oclut o V4lo ~ I 12 690 TRANSPORTE ESCOLAR"

        rows = build_page_manifest(records)
        self.assertEqual(len(rows), 467)
        indexed = {row["page"]: row for row in rows}
        self.assertEqual(indexed[171]["action_codes"], ["12.362.2001.2690"])
        self.assertEqual(indexed[174]["status"], "REVIEW_REQUIRED_CODE_CORRUPTION")
        self.assertEqual(indexed[392]["status"], "PARSED_CANDIDATES_ONLY")
        self.assertEqual(indexed[375]["status"], "SKIP_BLANK")
        self.assertEqual(indexed[475]["status"], "REVIEW_REQUIRED_TARGETED_EXTRACTION")
        self.assertFalse(indexed[171]["critical_numeric_auto_promotion"])
        self.assertFalse(indexed[171]["numeric_values_in_manifest"])
        self.assertNotIn("numeric_candidates", indexed[171])

    def test_builder_rejects_missing_page(self):
        records = [{"page": page, "text": ""} for page in range(15, 481)]
        with self.assertRaises(LoaJournalPageManifestError):
            build_page_manifest(records)

    def test_summary_never_emits_numeric_values(self):
        records = [{"page": page, "text": ""} for page in range(15, 482)]
        rows = build_page_manifest(records)
        result = summarize(rows)
        self.assertFalse(result["numeric_values_committed"])
        self.assertEqual(result["row_count"], 467)
        self.assertEqual(result["skip_blank_pages"], [375, 386, 413, 415, 421, 426])
        self.assertEqual(result["targeted_review_pages"], [475, 476, 477, 478, 479, 480, 481])

    def test_action_index_is_exact_pinned_shape(self):
        entries = self.action_index["entries"]
        self.assertEqual(len(entries), 18)
        self.assertEqual(sum(len(entry["action_codes"]) for entry in entries), 49)
        self.assertIn({"page": 171, "action_codes": ["12.362.2001.2690"]}, entries)
        self.assertNotIn(174, [entry["page"] for entry in entries])

    def test_numeric_promotion_cannot_be_enabled(self):
        bad = copy.deepcopy(self.evidence)
        bad["manifest"]["numeric_values_committed"] = True
        with self.assertRaises(LoaJournalPageManifestError):
            validate_evidence(bad, copy.deepcopy(self.action_index))

    def test_silver_promotion_cannot_be_enabled(self):
        bad = copy.deepcopy(self.evidence)
        bad["promotion"]["silver"] = True
        with self.assertRaises(LoaJournalPageManifestError):
            validate_evidence(bad, copy.deepcopy(self.action_index))

    def test_financial_identity_cannot_be_overstated(self):
        bad = copy.deepcopy(self.evidence)
        bad["promotion"]["financial_identity"] = "PROVEN"
        with self.assertRaises(LoaJournalPageManifestError):
            validate_evidence(bad, copy.deepcopy(self.action_index))

    def test_runtime_effects_must_remain_zero(self):
        bad = copy.deepcopy(self.evidence)
        bad["effects"]["drive_write"] = 1
        with self.assertRaises(LoaJournalPageManifestError):
            validate_evidence(bad, copy.deepcopy(self.action_index))


if __name__ == "__main__":
    unittest.main()
