from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/task217c_discovery_canonization.v1.json"


class TestTask217CDiscoveryCanonization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(CFG.read_text(encoding="utf-8"))

    def test_runtime_identity_is_pinned(self):
        self.assertEqual(self.cfg["schema"], "TASK217C_DISCOVERY_CANONIZATION_V1")
        self.assertEqual(self.cfg["issue"], 680)
        self.assertEqual(
            self.cfg["runtime"]["implementation_sha"],
            "993f8a07516bae641461221959552e6e2950a8d1",
        )
        self.assertEqual(self.cfg["runtime"]["run_id"], 34292251773)
        self.assertEqual(
            self.cfg["runtime"]["result_sha256"],
            "7c31c9791793c889a8c76e27bcf0d6b6b26f23a3b6bec07fbd95d8c1fba29510",
        )
        self.assertEqual(self.cfg["runtime"]["conclusion"], "success")

    def test_month_distribution_sums_to_99(self):
        counts = self.cfg["scope"]["monthly_document_counts"]
        self.assertEqual(list(counts.values()), [12,12,12,12,12,12,10,12,5])
        self.assertEqual(sum(counts.values()), 99)
        self.assertEqual(self.cfg["scope"]["document_count"], 99)
        self.assertEqual(self.cfg["scope"]["index_pages"], 9)
        self.assertEqual(self.cfg["scope"]["estimated_remote_gets"], 18)
        self.assertEqual(self.cfg["scope"]["document_downloads"], 0)

    def test_existing_12_are_excluded_from_new_redigest_scope(self):
        existing = self.cfg["existing_corpus"]["editions"]
        self.assertEqual(existing, list(range(7304, 7316)))
        self.assertEqual(len(existing), 12)
        self.assertEqual(self.cfg["redigest_scope"]["new_document_count"], 87)
        self.assertEqual(
            self.cfg["scope"]["document_count"]
            - self.cfg["existing_corpus"]["overlap_with_discovery_count"],
            self.cfg["redigest_scope"]["new_document_count"],
        )

    def test_discovery_does_not_promote_answerability(self):
        self.assertEqual(
            self.cfg["answerability"]["INFRA_Q2"],
            "BLOCKED_PENDING_DOCUMENT_REDIGEST",
        )
        self.assertEqual(self.cfg["answerability"]["contextual_paths_before"], 33)
        self.assertEqual(self.cfg["answerability"]["contextual_paths_after"], 33)
        self.assertTrue(
            self.cfg["redigest_scope"]["document_download_requires_separate_authorization"]
        )
        self.assertTrue(all(v is False for v in self.cfg["remote_effects_of_canonization"].values()))


if __name__ == "__main__":
    unittest.main()
