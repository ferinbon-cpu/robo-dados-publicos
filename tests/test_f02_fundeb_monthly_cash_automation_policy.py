from __future__ import annotations

import json
import unittest
from pathlib import Path

from robo_dados_publicos.automation.policy import evaluate_gate, validate_policy

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
CUSTODY = ROOT / "docs/evidence/f02_fundeb_monthly_cash/F02_FUNDEB_MONTHLY_2026_JAN_MAR_SOURCE_CUSTODY.json"
AUTH = ROOT / "docs/evidence/f02_fundeb_monthly_cash/F02_FUNDEB_MONTHLY_2026_JAN_MAR_RUNTIME_AUTHORIZATION.json"


class F02FundebMonthlyCashPolicyTests(unittest.TestCase):
    def test_gate_is_manual_t0_and_policy_evaluator_blocks_auto(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        validate_policy(policy)
        gate = next(row for row in policy["gates"] if row["id"] == "F02_FUNDEB_MONTHLY_CASH_OFFLINE")
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertFalse(gate["auto_allowed"])
        self.assertTrue(gate["manual_execution_required"])
        self.assertTrue(gate["no_workflow_trigger"])
        self.assertEqual(gate["current_triggers"], [])
        decision = evaluate_gate(policy, gate["id"])
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["reason"], "POLICY_AUTO_ALLOWED_FALSE")

    def test_gate_contract_blocks_every_remote_and_financial_promotion(self):
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        self.assertEqual(gate["schema"], "F02_FUNDEB_MONTHLY_CASH_GATE_V1")
        self.assertFalse(gate["remote_drive_read_authorized"])
        self.assertTrue(gate["runtime_authorization_required"])
        self.assertTrue(all(gate["blocked_remote_effects"].values()))
        self.assertTrue(all(gate["semantic_blocks"].values()))

    def test_source_custody_pins_three_unique_months_and_legacy_is_reference_only(self):
        custody = json.loads(CUSTODY.read_text(encoding="utf-8"))
        self.assertEqual(custody["family"], "FUNDEB_MONTHLY_CASH_LOCAL")
        self.assertEqual([x["month"] for x in custody["sources"]], ["2026-01","2026-02","2026-03"])
        self.assertEqual(len({x["drive_file_id"] for x in custody["sources"]}), 3)
        self.assertEqual(len({x["sha256"] for x in custody["sources"]}), 3)
        self.assertEqual(
            custody["legacy_derived_reconciliation"]["status"],
            "DERIVED_REFERENCE_ONLY_NOT_SOURCE_OF_TRUTH",
        )
        self.assertTrue(custody["legacy_derived_reconciliation"]["observed_source_sha256_match_all_three"])

    def test_owner_phase_authorization_preserves_forbidden_effects(self):
        auth = json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertTrue(auth["authorized"])
        self.assertEqual(auth["batch_id"], "F02_FUNDEB_MONTHLY_CASH_2026_JAN_MAR")
        forbidden = set(auth["forbidden_effects"])
        for effect in (
            "DELETE","OVERWRITE","SERVING","LOOKER","PUBLICATION","SITE",
            "SCHEDULE","RECURRENCE","GOLD_PROMOTION",
            "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
        ):
            self.assertIn(effect, forbidden)


if __name__ == "__main__":
    unittest.main()
