import json
import unittest
from pathlib import Path


class TestM5Promotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent.parent
        cls.current = json.loads((cls.root / "release_manifest_v01.json").read_text(encoding="utf-8"))
        cls.active = json.loads((cls.root / "release_manifest_v01_0.6.3_active.json").read_text(encoding="utf-8"))
        cls.candidate = json.loads((cls.root / "release_manifest_v01_0.6.3.json").read_text(encoding="utf-8"))
        cls.qa = json.loads((cls.root / "QA_SOFTWARE_V01_0.6.3_ACTIVE.json").read_text(encoding="utf-8"))

    def test_candidate_evidence_is_preserved_after_promotion(self):
        # The immutable 0.6.3 promotion evidence must remain preserved even
        # after a later candidate is opened. The mutable current manifest may
        # legitimately point to that newer candidate.
        self.assertEqual("0.6.3", self.current["current_active"])
        self.assertEqual("release_manifest_v01_0.6.3_active.json", self.current["active_manifest"])
        self.assertEqual("release_manifest_v01_0.6.3.json", self.current["preserved_candidate_manifest"])
        self.assertEqual("0.6.3", self.candidate["version"])
        self.assertEqual("CANDIDATE", self.candidate["status"])
        self.assertEqual("0.6.3", self.active["version"])
        self.assertEqual("ACTIVE", self.active["status"])
        self.assertEqual("0.6.3", self.active["promoted_from_candidate"])

    def test_live_observability_gate_is_pinned(self):
        gate = self.active["live_gate"]
        self.assertEqual("PASS_M5_OBSERVABILITY_RUNTIME_GATE", gate["status"])
        self.assertEqual("PASS_GITHUB_LIVE_GATE", gate["runtime_gate"])
        self.assertEqual(32782732233, gate["github_run"])
        self.assertEqual("7/7 PASS", gate["runtime_checks"])
        self.assertEqual("HEALTHY", gate["overall_health"])
        self.assertEqual("PASS", gate["privacy_status"])
        self.assertFalse(gate["secret_values_exposed"])
        self.assertFalse(gate["remote_identifiers_exposed"])

    def test_artifact_and_safety_are_recorded(self):
        artifact = self.active["artifact"]
        safety = self.active["safety"]
        self.assertEqual("observability-report-32782732233", artifact["name"])
        self.assertEqual(6, artifact["file_count"])
        self.assertEqual("PASS_NO_SECRET_TOKEN_REMOTE_ID_OR_SHA_KEYS", artifact["sanitization_review"])
        self.assertEqual("DISABLED_IN_WORKFLOW", safety["source_collection_rerun"])
        self.assertEqual("DISABLED_IN_WORKFLOW", safety["source_processing_rerun"])
        self.assertEqual("DISABLED_IN_WORKFLOW", safety["reconciliation_rerun"])
        self.assertEqual("DISABLED", safety["workflow_schedule"])
        self.assertEqual("PROHIBITED", safety["financial_identity_auto_promotion"])

    def test_next_gate_recorded_by_m5_is_product_design_not_automatic_expansion(self):
        # Check the immutable M5 release artifacts, not the mutable current
        # roadmap pointer, which advances when 0.7.0 work begins.
        self.assertEqual("M6_PRODUCT_MINIMAL_OUTPUT_DESIGN_0_7_0", self.active["next_action"])
        self.assertEqual("NOT_IMPLEMENTED", self.active["open_gates"]["minimal_product_output"])
        self.assertEqual("NOT_CONFIGURED", self.active["open_gates"]["recurring_source_inventory"])
        self.assertEqual("M6_PRODUCT_MINIMAL_OUTPUT_DESIGN_0_7_0", self.qa["next_gate"])


if __name__ == "__main__":
    unittest.main()
