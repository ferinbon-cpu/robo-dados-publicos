from __future__ import annotations

import json
import unittest
from pathlib import Path

from robo_dados_publicos.automation.policy import evaluate_gate, validate_policy

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
AUTH = ROOT / "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_OWNER_AUTHORIZATION_0.8.0.json"


class F02FundebMonthlyCashPolicyFinalizationTests(unittest.TestCase):
    def test_policy_registers_manual_gate_but_auto_evaluator_still_blocks(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        validate_policy(policy)
        matches = [g for g in policy["gates"] if g["id"] == "F02_FUNDEB_MONTHLY_CASH_OFFLINE"]
        self.assertEqual(len(matches), 1)
        gate = matches[0]
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertFalse(gate["auto_allowed"])
        self.assertTrue(gate["manual_execution_required"])
        self.assertTrue(gate["no_workflow_trigger"])
        self.assertEqual(gate["current_triggers"], [])
        self.assertFalse(gate["implementation_merge_required_before_manual_execution"])
        self.assertEqual(gate["implementation_pr_required"], 376)
        self.assertEqual(gate["implementation_pr_merged"], 376)
        self.assertEqual(gate["implementation_merge_sha"], "48c2f7624dba3f46b61f09659f15d798b836c0ef")
        self.assertTrue(all(value is False for value in gate["effects"].values()))
        decision = evaluate_gate(policy, gate["id"])
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["reason"], "POLICY_AUTO_ALLOWED_FALSE")

    def test_contract_blocks_remote_effects_and_requires_implementation_merge(self):
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        self.assertEqual(gate["schema"], "F02_FUNDEB_MONTHLY_CASH_GATE_V1")
        self.assertEqual(gate["status"], "REGISTERED_MANUAL_T0_REMOTE_CLOSED")
        self.assertFalse(gate["implementation_merge_required_before_manual_execution"])
        self.assertEqual(gate["implementation_pr_required"], 376)
        self.assertFalse(gate["remote_drive_read_authorized"])
        self.assertTrue(all(gate["blocked_remote_effects"].values()))
        self.assertTrue(all(gate["semantic_blocks"].values()))

    def test_owner_policy_authorization_is_not_runtime_execution_authorization(self):
        auth = json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertEqual(auth["status"], "AUTHORIZED_POLICY_CHANGE")
        self.assertTrue(auth["runtime_authorization_is_separate"])
        self.assertTrue(auth["runtime_authorization_must_be_ephemeral_and_exact_sha_pinned"])
        self.assertIn(
            "MANUAL_EXECUTION_BEFORE_IMPLEMENTATION_PR_376_MERGE",
            auth["explicitly_not_authorized"],
        )
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        gate = next(g for g in policy["gates"] if g["id"] == "F02_FUNDEB_MONTHLY_CASH_OFFLINE")
        self.assertNotIn(
            "IMPLEMENTATION_PR_376_MUST_BE_MERGED_BEFORE_MANUAL_EXECUTION",
            gate["blockers"],
        )
        self.assertIn("AUTO_EXECUTION", auth["explicitly_not_authorized"])
        self.assertIn("SILVER_WRITE_BY_THIS_POLICY_CHANGE", auth["explicitly_not_authorized"])


if __name__ == "__main__":
    unittest.main()
