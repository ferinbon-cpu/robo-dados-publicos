from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/task217e_partial_redigest_adjudication.v1.json"


class TestTask217EPartialRedigestAdjudication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(CFG.read_text(encoding="utf-8"))

    def test_runtime_and_partial_counts_are_pinned(self):
        self.assertEqual(self.cfg["runtime"]["run_id"], 34294353045)
        self.assertEqual(self.cfg["observed"]["target_documents"], 87)
        self.assertEqual(self.cfg["observed"]["document_download_count"], 80)
        self.assertEqual(self.cfg["observed"]["failure_count"], 12)
        self.assertEqual(self.cfg["observed"]["raw_exact_alias_infrastructure_event_count"], 7)
        self.assertEqual(self.cfg["observed"]["generic_unassigned_school_infrastructure_event_count"], 1)

    def test_adjudication_keeps_one_true_event_and_rejects_six_homonyms(self):
        adj = self.cfg["manual_deterministic_adjudication"]
        self.assertEqual(adj["true_named_school_infrastructure_event_count"], 1)
        self.assertEqual(adj["rejected_non_school_homonym_event_count"], 6)
        event = adj["true_events"][0]
        self.assertEqual(event["event_id"], "JOEV_fab1a3c79f589f7ccc18")
        self.assertEqual(event["school_code"], "35295061")
        self.assertEqual(event["contract_number"], "42/2026")
        rejected = {row["event_id"]: row["adjudication"] for row in adj["rejected_events"]}
        self.assertEqual(len(rejected), 6)
        self.assertTrue(all(value.startswith("REJECT_NON_SCHOOL_") for value in rejected.values()))

    def test_twelve_uncovered_documents_are_exact_and_unique(self):
        rows = self.cfg["uncovered_documents"]
        self.assertEqual(len(rows), 12)
        editions = [row["edition"] for row in rows]
        self.assertEqual(len(set(editions)), 12)
        self.assertEqual(
            editions,
            [7243,7253,7265,7270,7271,7287,7294,7316,7317,7318,7319,7320],
        )
        self.assertTrue(all(row["url"].startswith("https://ecrie.com.br/") for row in rows))

    def test_partial_positive_evidence_does_not_promote_exhaustive_question(self):
        ans = self.cfg["answerability"]
        self.assertTrue(ans["positive_partial_evidence_exists"])
        self.assertTrue(ans["complete_scope_required"])
        self.assertEqual(ans["contextual_paths_before"], 33)
        self.assertEqual(ans["contextual_paths_after"], 33)
        self.assertEqual(
            ans["status"],
            "BLOCKED_PARTIAL_SCOPE_12_DOCUMENTS_UNCOVERED",
        )
        self.assertFalse(
            self.cfg["failure_semantics"]["per_edition_stop_code_preserved_in_task217d_artifact"]
        )
        self.assertFalse(self.cfg["failure_semantics"]["individual_failure_cause_may_be_inferred"])


if __name__ == "__main__":
    unittest.main()
