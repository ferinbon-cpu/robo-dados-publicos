from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy, validate_policy

ROOT = Path(__file__).resolve().parents[1]
GATE_ID = "F02_KNOWN_FAMILY_BUNDLE_OFFLINE"


class F02KnownFamilyAutomationPolicyTests(unittest.TestCase):
    def test_adapter_is_registered_as_t0_offline_only(self):
        policy = load_policy(ROOT)
        structural = validate_policy(policy)
        self.assertEqual(structural["status"], "PASS_AUTOMATION_POLICY_STRUCTURE")
        gate = next(row for row in policy["gates"] if row["id"] == GATE_ID)
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertTrue(gate["auto_allowed"])
        self.assertEqual(gate["credential_capability"], "NONE")
        self.assertEqual(gate["current_triggers"], [])
        self.assertEqual(gate["invocation_surface"], "DIRECT_CLI_OR_CI_TEST_ONLY")
        self.assertTrue(gate["no_workflow_trigger"])
        self.assertFalse(gate["effects"]["source_network"])
        self.assertFalse(gate["effects"]["drive_reads"])
        self.assertFalse(gate["effects"]["drive_writes"])
        self.assertFalse(gate["effects"]["publication"])
        self.assertFalse(gate["remote_materialization_authorized"])
        self.assertFalse(gate["bronze_write_authorized"])
        self.assertFalse(gate["silver_write_authorized"])
        self.assertFalse(gate["gold_write_authorized"])
        self.assertFalse(gate["serving_authorized"])
        self.assertFalse(gate["schedule"])
        self.assertFalse(gate["recurrence"])

    def test_policy_evaluator_allows_only_the_offline_gate_semantics(self):
        decision = evaluate_gate(load_policy(ROOT), GATE_ID)
        self.assertEqual(decision["decision"], "AUTO_ALLOWED")
        self.assertEqual(decision["tier"], "T0_OFFLINE")
        self.assertEqual(
            decision["reason"],
            "OFFLINE_DETERMINISTIC_NO_REMOTE_EFFECTS",
        )


if __name__ == "__main__":
    unittest.main()
