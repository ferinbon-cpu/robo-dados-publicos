import copy
import json
import unittest

from scripts.github_task_010n_r_e_siope_public_contract_semantic_evidence_gate import (
    EVIDENCE,
    TASK_007,
    TASK_009,
    validate,
)


class Task010NREPublicContractSemanticEvidenceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.task_007 = json.loads(TASK_007.read_text(encoding="utf-8"))
        cls.task_009 = json.loads(TASK_009.read_text(encoding="utf-8"))

    def test_pinned_evidence_passes(self):
        validate(copy.deepcopy(self.data), copy.deepcopy(self.task_007), copy.deepcopy(self.task_009))

    def assert_rejected(self, mutate, message, target="data"):
        data = copy.deepcopy(self.data)
        task_007 = copy.deepcopy(self.task_007)
        task_009 = copy.deepcopy(self.task_009)
        obj = {"data": data, "task_007": task_007, "task_009": task_009}[target]
        mutate(obj)
        with self.assertRaisesRegex(ValueError, message):
            validate(data, task_007, task_009)

    def test_rejects_semantic_promotion(self):
        self.assert_rejected(lambda d: d.update(decision="PUBLIC_CONTRACT_EVIDENCE_COMPLETE_OFFLINE"), "decision")
        self.assert_rejected(lambda d: d["summary"].update(proven_count=10, partial_count=1), "summary")

    def test_rejects_matrix_drift_or_proven_alias(self):
        self.assert_rejected(lambda d: d["matrix"].pop(), "matrix")
        self.assert_rejected(lambda d: d["matrix"][1].update(status="PROVEN"), "PARTIAL")

    def test_rejects_task_007_overclaim(self):
        self.assert_rejected(
            lambda d: d["field_definition_summary"].update(**{"2025_odata_alias_identity_proven_count": 10}),
            "alias identity",
            target="task_007",
        )

    def test_rejects_task_009_s1_s2_promotion(self):
        self.assert_rejected(
            lambda d: d["question_results"]["S2_FINANCIAL_ALIAS_BRIDGE"].update(status="PROVEN"),
            "S1/S2",
            target="task_009",
        )

    def test_rejects_edu_equals_mde(self):
        self.assert_rejected(lambda d: d["edu_guard"].update(EDU_equals_MDE_authorized=True), "EDU=MDE")

    def test_rejects_remote_or_reverse_engineering_authorization(self):
        self.assert_rejected(lambda d: d["smallest_next_remote_evidence_class"].update(remote_execution_authorized_here=True), "remote execution")
        self.assert_rejected(lambda d: d["smallest_next_remote_evidence_class"].update(internal_reverse_engineering_default=True), "reverse engineering")
        self.assert_rejected(lambda d: d["guards"].update(remote_network_authorized=True), "guards")

    def test_rejects_any_canonical_state_change(self):
        for key in self.data["canonical_state"]:
            with self.subTest(key=key):
                self.assert_rejected(lambda d, key=key: d["canonical_state"].update({key: "DRIFT"}), "canonical state")

    def test_rejects_task_010o_as_next_gate(self):
        self.assert_rejected(lambda d: d.update(next_gate="TASK_010O"), "next gate")


if __name__ == "__main__":
    unittest.main()
