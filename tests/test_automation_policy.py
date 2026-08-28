import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy, validate_policy


ROOT = Path(__file__).resolve().parents[1]


class TestAutomationPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy(ROOT)

    def test_policy_is_default_deny_and_structurally_valid(self):
        result = validate_policy(self.policy)
        self.assertEqual("PASS_AUTOMATION_POLICY_STRUCTURE", result["status"])
        self.assertEqual("BLOCK", result["default_decision"])
        self.assertGreaterEqual(result["gate_count"], 4)

    def test_offline_ci_is_auto_allowed(self):
        decision = evaluate_gate(self.policy, "CI_OFFLINE")
        self.assertEqual("AUTO_ALLOWED", decision["decision"])
        self.assertEqual("T0_OFFLINE", decision["tier"])

    def test_m8_no_click_is_still_blocked_until_first_live_readonly_proof(self):
        decision = evaluate_gate(self.policy, "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY")
        self.assertEqual("BLOCK", decision["decision"])
        self.assertEqual("T1_REMOTE_READONLY", decision["tier"])
        self.assertIn("FIRST_LIVE_M8_READONLY_PRODUCT_GATE_NOT_YET_PROVEN", decision["blockers"])
        self.assertIn("CURRENT_WORKFLOW_REQUIRES_MANUAL_CONFIRMATION", decision["blockers"])

    def test_persistence_and_publication_are_not_auto_allowed(self):
        for gate_id in ("ACTIVE_RUNTIME_PERSISTENCE", "PRODUCT_OUTPUT_PUBLICATION"):
            with self.subTest(gate_id=gate_id):
                decision = evaluate_gate(self.policy, gate_id)
                self.assertEqual("BLOCK", decision["decision"])

    def test_unknown_gate_fails_closed(self):
        decision = evaluate_gate(self.policy, "UNKNOWN_GATE")
        self.assertEqual("BLOCK", decision["decision"])
        self.assertEqual("UNKNOWN_GATE_DEFAULT_DENY", decision["reason"])

    def test_m8_workflow_uses_only_dedicated_readonly_secrets_and_remains_manual(self):
        workflow = (ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-gate.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("confirm_m8_siope_historical_gold_product_output_readonly", workflow)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_ID }}", workflow)
        self.assertIn("GOOGLE_DRIVE_CLIENT_SECRET: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_SECRET }}", workflow)
        self.assertIn("GOOGLE_DRIVE_REFRESH_TOKEN: ${{ secrets.GOOGLE_DRIVE_READONLY_REFRESH_TOKEN }}", workflow)
        self.assertNotIn("${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}", workflow)
        self.assertNotIn("${{ secrets.GOOGLE_DRIVE_CLIENT_SECRET }}", workflow)
        self.assertNotIn("${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}", workflow)
        self.assertNotIn("workflow_call:", workflow)

    def test_runtime_capability_proof_precedes_drive_read_step(self):
        workflow = (ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-gate.yml").read_text(encoding="utf-8")
        proof = "python scripts/github_m8_readonly_credential_capability_gate.py"
        live = "- name: Reler 9 Gold e gerar bundle local"
        self.assertIn(proof, workflow)
        self.assertIn(live, workflow)
        self.assertLess(workflow.index(proof), workflow.index(live))

    def test_policy_gate_runs_offline_and_reports_m8_block(self):
        cp = subprocess.run(
            [sys.executable, str(ROOT / "scripts/github_automation_policy_gate.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cp.returncode, cp.stderr or cp.stdout)
        result = json.loads(cp.stdout.strip())
        self.assertEqual("PASS_AUTOMATION_POLICY_OFFLINE", result["status"])
        self.assertEqual("BLOCK", result["m8_no_click_decision"])
        self.assertTrue(result["current_m8_readonly_secret_wired"])
        self.assertTrue(result["readonly_runtime_capability_proof_step_present"])
        self.assertEqual(0, result["drive_write_count"])
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
