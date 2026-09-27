import json
import unittest
from pathlib import Path


class TestM4DPromotion(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def load_json(self, relative_path):
        return json.loads((self.root / relative_path).read_text(encoding="utf-8"))

    def test_candidate_evidence_is_preserved_after_promotion(self):
        candidate = self.load_json("release_manifest_v01_0.5.9.json")
        active = self.load_json("release_manifest_v01_0.5.9_active.json")
        self.assertEqual("CANDIDATE", candidate["status"])
        self.assertEqual("ACTIVE", active["status"])
        self.assertEqual("0.5.9", active["promoted_from_candidate"])

    def test_live_gate_evidence_is_pinned(self):
        active = self.load_json("release_manifest_v01_0.5.9_active.json")
        gate = active["live_gate"]
        self.assertEqual("PASS_GITHUB_LIVE_GATE", gate["status"])
        self.assertEqual(32678624194, gate["workflow_run_id"])
        self.assertEqual(97476648260, gate["workflow_job_id"])
        self.assertEqual("REPLACED", gate["state_remote"])
        self.assertEqual("CREATED", gate["append_only_log"])

    def test_promotion_keeps_safety_gates_closed(self):
        active = self.load_json("release_manifest_v01_0.5.9_active.json")
        self.assertEqual("PROHIBITED", active["safety"]["financial_identity_auto_promotion"])
        self.assertEqual("EXPLICIT_SOURCE_INVENTORY_OPT_IN", active["safety"]["production_collection"])
        self.assertEqual("DISABLED", active["safety"]["workflow_schedule"])

    def test_tda_and_source_collection_remain_unresolved(self):
        active = self.load_json("release_manifest_v01_0.5.9_active.json")
        discovery = self.load_json("config/limeira_sources_discovery.json")
        tda = next(item for item in discovery["surfaces"] if item["source_id"] == "LIMEIRA_TDA_PORTAL")
        journal = next(item for item in discovery["surfaces"] if item["source_id"] == "LIMEIRA_JORNAL_OFICIAL")
        self.assertEqual("BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN", active["open_gates"]["tda_limeira"])
        self.assertEqual("NOT_CONFIGURED", active["open_gates"]["source_collection"])
        self.assertFalse(tda["production_collection_enabled"])
        self.assertFalse(journal["production_collection_enabled"])


if __name__ == "__main__":
    unittest.main()
