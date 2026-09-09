from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/task217f2_recovery_canonization.v1.json"


class TestTask217F2RecoveryCanonization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(CFG.read_text(encoding="utf-8"))

    def test_runtime_result_is_pinned(self):
        self.assertEqual(self.cfg["runtime"]["run_id"], 34299660362)
        self.assertEqual(self.cfg["observed"]["validated_download_count"], 8)
        self.assertEqual(self.cfg["observed"]["failure_count"], 4)
        self.assertEqual(self.cfg["runtime"]["embedded_result_sha256"], "64ee897c321d45cd9ef7aa780320c57526af09e9cb81fd2800168cef6ae282f8")

    def test_exact_four_remaining_are_size_stops(self):
        self.assertEqual(
            [row["edition"] for row in self.cfg["failures"]],
            [7243,7253,7270,7287],
        )
        self.assertTrue(all(row["stop_code"] == "TASK217F_DOCUMENT_BYTES" for row in self.cfg["failures"]))

    def test_no_promotion_until_full_scope(self):
        ans = self.cfg["answerability"]
        self.assertEqual(ans["INFRA_Q2"], "BLOCKED_FOUR_OVERSIZED_DOCUMENTS_UNCOVERED")
        self.assertEqual(ans["contextual_paths_before"], 33)
        self.assertEqual(ans["contextual_paths_after"], 33)
        self.assertTrue(ans["full_scope_required"])

    def test_abstract_generic_events_are_rejected(self):
        sem = self.cfg["semantic_adjudication"]
        self.assertEqual(sem["raw_generic_events"], 3)
        self.assertEqual(sem["physical_school_infrastructure_generic_events_after_guard"], 0)
        self.assertEqual(len(sem["rejected_abstract_phrases"]), 3)


if __name__ == "__main__":
    unittest.main()
