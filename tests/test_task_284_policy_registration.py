from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.automation.policy import (
    AutomationPolicyError,
    evaluate_gate,
    load_policy,
    validate_policy,
)

ROOT = Path(__file__).resolve().parents[1]
GATE_ID = "TASK284_TDA_NAMESPACE_ACQUISITION"


class Task284PolicyRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy(ROOT)
        self.gate = next(g for g in self.policy["gates"] if g["id"] == GATE_ID)

    def test_policy_structure_accepts_consumed_manual_t1_registration(self):
        self.assertEqual(validate_policy(self.policy)["status"], "PASS_AUTOMATION_POLICY_STRUCTURE")
        self.assertEqual(self.gate["tier"], "T1_REMOTE_READONLY")
        self.assertFalse(self.gate["auto_allowed"])
        self.assertEqual(self.gate["credential_capability"], "NONE")
        self.assertTrue(self.gate["manual_execution_required"])
        self.assertTrue(self.gate["owner_authorization_required"])
        self.assertTrue(self.gate["authorization_consumed"])
        self.assertFalse(self.gate["new_session_or_retry_authorized"])
        self.assertEqual(self.gate["current_triggers"], [])
        self.assertFalse(self.gate["workflow_added"])
        self.assertTrue(self.gate["no_workflow_trigger"])
        self.assertFalse(self.gate["task_runtime_auto_execution"])
        self.assertFalse(self.gate["effects"]["drive_writes"])
        self.assertFalse(self.gate["effects"]["publication"])
        self.assertIn("READ_ONLY_CREDENTIAL_NOT_PROVEN", self.gate["blockers"])
        self.assertIn("AUTHORIZATION_CONSUMED", self.gate["blockers"])

    def test_gate_is_blocked_for_automatic_execution(self):
        decision = evaluate_gate(self.policy, GATE_ID)
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["reason"], "POLICY_AUTO_ALLOWED_FALSE")

    def test_enabling_auto_without_proven_readonly_credential_fails_closed(self):
        policy = deepcopy(self.policy)
        gate = next(g for g in policy["gates"] if g["id"] == GATE_ID)
        gate["auto_allowed"] = True
        with self.assertRaisesRegex(
            AutomationPolicyError,
            "STOP_AUTO_READONLY_CREDENTIAL_NOT_PROVEN",
        ):
            evaluate_gate(policy, GATE_ID)

    def test_policy_points_to_existing_contract_and_historical_result(self):
        self.assertTrue((ROOT / self.gate["contract"]).is_file())
        self.assertTrue((ROOT / self.gate["historical_result"]).is_file())


if __name__ == "__main__":
    unittest.main()
