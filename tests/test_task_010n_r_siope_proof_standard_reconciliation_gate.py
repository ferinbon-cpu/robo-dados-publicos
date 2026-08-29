import copy
import json
import unittest

from scripts.github_task_010n_r_siope_proof_standard_reconciliation_gate import EVIDENCE, validate


class Task010NRProofStandardReconciliationGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_pinned_evidence_passes(self):
        validate(copy.deepcopy(self.data))

    def assert_rejected(self, mutate, message):
        data = copy.deepcopy(self.data)
        mutate(data)
        with self.assertRaisesRegex(ValueError, message):
            validate(data)

    def test_rejects_alternative_decision(self):
        self.assert_rejected(lambda d: d.update(decision="UNIFORM_PUBLIC_CONTRACT_STANDARD_JUSTIFIED"), "decision")

    def test_rejects_missing_comparison_regime(self):
        self.assert_rejected(lambda d: d["comparison"].pop(), "comparison")

    def test_rejects_incomplete_bridge_standard(self):
        self.assert_rejected(lambda d: d["bridge_minimum_fields"].pop(), "bridge evidence")

    def test_rejects_network_or_drive_effect(self):
        self.assert_rejected(lambda d: d["scope"].update(network_requests=1), "scope")
        self.assert_rejected(lambda d: d["guards"].update(drive_write_authorized=True), "guards")

    def test_rejects_gold_or_2025_promotion(self):
        self.assert_rejected(lambda d: d["scope"].update(gold_2025_computed=True), "scope")
        self.assert_rejected(lambda d: d["canonical_state"].update(year_2025="PROVEN"), "canonical state")

    def test_rejects_historical_downgrade_or_series_expansion(self):
        self.assert_rejected(lambda d: d["canonical_state"].update(historical_2016_2024="DOWNGRADED"), "canonical state")
        self.assert_rejected(lambda d: d["canonical_state"].update(closed_annual_series="2016-2025"), "canonical state")

    def test_rejects_2026_release_or_task_010o_change(self):
        self.assert_rejected(lambda d: d["canonical_state"].update(year_2026="PROVEN"), "canonical state")
        self.assert_rejected(lambda d: d["canonical_state"].update(release_0_8_0="RELEASED"), "canonical state")
        self.assert_rejected(lambda d: d.update(next_gate_recommended="TASK_010O"), "010O")


if __name__ == "__main__":
    unittest.main()
