from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/md_01_3_incremental_value_audit.v1.json"


def doc_num(doc_id: str) -> int:
    return int(doc_id.removeprefix("DOC-"))


def expand(token: str) -> set[int]:
    if ".." not in token:
        return {doc_num(token)}
    left, right = token.split("..", 1)
    return set(range(doc_num(left), doc_num(right) + 1))


class TestTask226Md013IncrementalValueAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_schema_scope_and_coverage_guard(self) -> None:
        self.assertEqual(self.obj["schema"], "MD_01_3_INCREMENTAL_VALUE_AUDIT_V1")
        self.assertEqual(self.obj["task"], "TASK_226")
        self.assertEqual(self.obj["issue"], 764)
        self.assertEqual(self.obj["scope"]["safe_high_value_slice_before_subtraction"], 101)
        self.assertEqual(self.obj["scope"]["already_materialized_by_new_depth_tasks"], ["DOC-066", "DOC-105"])
        self.assertEqual(self.obj["scope"]["remaining_documents"], 99)
        self.assertEqual(self.obj["scope"]["contextual_coverage"], "38/38_UNCHANGED")

    def test_classification_counts_sum_to_99(self) -> None:
        counts = self.obj["classification_counts"]
        self.assertEqual(counts["NOVEL_SUBSTANTIVE"], 7)
        self.assertEqual(counts["CORROBORATION_ONLY"], 24)
        self.assertEqual(counts["SUPERSEDED_BY_STRONGER_CANONICAL_SOURCE"], 15)
        self.assertEqual(counts["INDEX_ONLY"], 52)
        self.assertEqual(counts["BLOCKED_NO_TEXT"], 1)
        self.assertEqual(sum(counts.values()), 99)

    def test_exact_partition_is_complete_and_disjoint(self) -> None:
        c = self.obj["classes"]
        novel = {doc_num(x) for x in c["NOVEL_SUBSTANTIVE"]["ids"]}
        corr = set()
        for subset in c["CORROBORATION_ONLY"]["subsets"].values():
            corr |= {doc_num(x) for x in subset["ids"]}
        sup = set()
        for subset in c["SUPERSEDED_BY_STRONGER_CANONICAL_SOURCE"]["subsets"].values():
            sup |= {doc_num(x) for x in subset["ids"]}
        index_only = {103, 104}
        for token in c["INDEX_ONLY"]["subsets"]["FUNDEB_25_EDUCACAO_PORTAL_REPORTS"]["id_ranges"]:
            index_only |= expand(token)
        blocked = {doc_num(x) for x in c["BLOCKED_NO_TEXT"]["ids"]}
        sets = [novel, corr, sup, index_only, blocked]
        for i, left in enumerate(sets):
            for right in sets[i + 1 :]:
                self.assertFalse(left & right)
        classified = set().union(*sets)
        safe = set(range(3, 67)) | set(range(68, 102)) | set(range(103, 106))
        expected = safe - {66, 105}
        self.assertEqual(classified, expected)
        self.assertNotIn(67, classified)
        self.assertEqual(len(classified), 99)

    def test_novel_accounting_bundle_and_receipts_are_not_conflated(self) -> None:
        c = self.obj["classes"]
        novel = set(c["NOVEL_SUBSTANTIVE"]["ids"])
        self.assertTrue({"DOC-006", "DOC-010", "DOC-017"}.issubset(novel))
        receipts = c["INDEX_ONLY"]["subsets"]["ANNUAL_ACCOUNTABILITY_RECEIPTS"]
        self.assertEqual(receipts["ids"], ["DOC-103", "DOC-104"])
        self.assertIn("not the substantive accounting statements", receipts["reason"])

    def test_overlap_prevents_reingestion(self) -> None:
        sup = self.obj["classes"]["SUPERSEDED_BY_STRONGER_CANONICAL_SOURCE"]["subsets"]
        monthly = sup["MONTHLY_REVENUE_EXPENSE"]
        self.assertEqual(monthly["count"], 10)
        self.assertIn("TASK_186_TCESP_REVENUE_LEDGER_2026", monthly["stronger_layers"])
        self.assertIn("TASK_187_TCESP_RICH_ACCOUNTING_LEDGER_2026", monthly["stronger_layers"])
        self.assertIn("F02_LOCAL_MONITORING_2026_JAN_MAY", monthly["stronger_layers"])
        planning = sup["PLANNING_2026"]
        self.assertEqual(planning["count"], 5)
        self.assertIn("TASK_189_LOA_SUBSTANTIVE_PLANNING_OVERLAY", planning["stronger_layers"])

    def test_rgf_is_authority_upgrade_not_fake_novelty(self) -> None:
        rgf = self.obj["classes"]["CORROBORATION_ONLY"]["subsets"]["RGF_LRF"]
        self.assertEqual(rgf["count"], 6)
        self.assertTrue(rgf["primary_source_upgrade_candidate"])
        self.assertEqual(rgf["known_existing_layer"], "MD_01_2_DERIVED_RGF_SYNTHESIS")

    def test_fundeb_portal_requires_fingerprint_before_ingest(self) -> None:
        fundeb = self.obj["classes"]["INDEX_ONLY"]["subsets"]["FUNDEB_25_EDUCACAO_PORTAL_REPORTS"]
        self.assertEqual(fundeb["count"], 50)
        self.assertEqual(fundeb["id_ranges"], ["DOC-020..DOC-040", "DOC-068..DOC-096"])
        self.assertIn("FINGERPRINT", fundeb["next_action"])

    def test_priority_and_guards(self) -> None:
        queue = self.obj["priority_queue"]
        self.assertEqual(queue[0]["bundle"], "ANNUAL_ACCOUNTING_2025")
        self.assertEqual(queue[0]["ids"], ["DOC-017", "DOC-010", "DOC-006"])
        guards = set(self.obj["guards"])
        for guard in {
            "PDF_NE_NOVELTY",
            "SAME_FACT_DIFFERENT_FILE_NE_NEW_FACT",
            "NO_DOUBLE_COUNTING",
            "OCR_NE_NUMERIC_TRUTH",
            "RECEIPT_NE_SUBSTANTIVE_ACCOUNTING_STATEMENT",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }:
            self.assertIn(guard, guards)
        self.assertTrue(all(value is False for value in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
