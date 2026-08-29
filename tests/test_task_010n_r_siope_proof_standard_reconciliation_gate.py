import copy
import json
import unittest

from scripts.github_task_010n_r_siope_proof_standard_reconciliation_gate import EVIDENCE, TASK_007, validate


class Task010NRProofStandardReconciliationGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.task_007 = json.loads(TASK_007.read_text(encoding="utf-8"))

    def test_pinned_evidence_passes(self):
        validate(copy.deepcopy(self.data), copy.deepcopy(self.task_007))

    def assert_rejected(self, mutate, message, documentary=False):
        data, task_007 = copy.deepcopy(self.data), copy.deepcopy(self.task_007)
        mutate(task_007 if documentary else data)
        with self.assertRaisesRegex(ValueError, message):
            validate(data, task_007)

    def test_rejects_premature_p1_or_p2_decision(self):
        self.assert_rejected(lambda d: d.update(decision="INTERNAL_BRIDGE_STANDARD_REQUIRED"), "revised decision")
        self.assert_rejected(lambda d: d["propositions"].update(P2_status="REQUIRED"), "prematurely fix P2")

    def test_rejects_missing_comparison_or_p1_criterion(self):
        self.assert_rejected(lambda d: d["comparison"].pop(), "comparison")
        self.assert_rejected(lambda d: d["p1_minimum_public_contract_evidence"].pop(), "P1 public-contract")

    def test_rejects_unproven_year_claim(self):
        self.assert_rejected(lambda d: d["years_satisfying_complete_p1_standard_in_repo"].append(2025), "no year")

    def test_rejects_task_007_drift_or_misrepresentation(self):
        self.assert_rejected(lambda d: d["field_definition_summary"].update(**{"2025_odata_alias_identity_proven_count": 10}), "TASK 007 documentary", documentary=True)
        self.assert_rejected(lambda d: d["task_007_evidence"].update(NUM_POPU_defined=True), "TASK 007 finding")

    def test_rejects_reverse_engineering_as_default(self):
        self.assert_rejected(lambda d: d["smallest_discriminating_evidence_class"].update(reverse_engineering_default=True), "official public contract")

    def test_rejects_network_drive_gold_or_guard_widening(self):
        self.assert_rejected(lambda d: d["scope"].update(network_requests=1), "scope")
        self.assert_rejected(lambda d: d["guards"].update(drive_write_authorized=True), "guards")
        self.assert_rejected(lambda d: d["scope"].update(gold_2025_computed=True), "scope")

    def test_rejects_any_canonical_state_change(self):
        for key in self.data["canonical_state"]:
            with self.subTest(key=key):
                self.assert_rejected(lambda d, key=key: d["canonical_state"].update({key: "DRIFT"}), "canonical state")

    def test_rejects_task_010o_as_next_gate(self):
        self.assert_rejected(lambda d: d.update(next_gate_recommended="TASK_010O"), "not open TASK 010O")


if __name__ == "__main__":
    unittest.main()
