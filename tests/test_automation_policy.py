import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.automation.policy import AutomationPolicyError, evaluate_gate, load_policy, validate_policy


ROOT = Path(__file__).resolve().parents[1]
M8_WRAPPER = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-gate.yml"
M8_REUSABLE = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-reusable.yml"
M8_AUTO = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-auto.yml"


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

    def test_m8_t1_is_auto_allowed_only_after_readonly_and_human_trust_boundary(self):
        decision = evaluate_gate(self.policy, "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY")
        self.assertEqual("AUTO_ALLOWED", decision["decision"])
        self.assertEqual("T1_REMOTE_READONLY", decision["tier"])
        gate = next(g for g in self.policy["gates"] if g["id"] == "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY")
        self.assertEqual("READ_ONLY_PROVEN", gate["credential_capability"])
        self.assertEqual("OWNER_COMPLETED_PUBLIC_REPO_AND_ACTIVE_MAIN_RULESET_FOR_T1_NO_CLICK", gate["human_authorization"])
        self.assertEqual([], gate["blockers"])
        trust = gate["trust_boundary_observation"]
        self.assertEqual("public", trust["repository_visibility"])
        self.assertTrue(trust["main_protected"])
        self.assertEqual(21728151, trust["ruleset_id"])
        self.assertEqual("main-protection-v1", trust["ruleset_name"])
        self.assertEqual("active", trust["ruleset_enforcement"])
        self.assertEqual(["Audit full Git history safely", "Validar sem Drive"], trust["required_status_checks"])

    def test_m8_auto_fails_closed_without_human_authorization(self):
        policy = copy.deepcopy(self.policy)
        gate = next(g for g in policy["gates"] if g["id"] == "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY")
        gate.pop("human_authorization")
        with self.assertRaisesRegex(AutomationPolicyError, "STOP_AUTO_T1_HUMAN_AUTHORIZATION_MISSING"):
            validate_policy(policy)

    def test_m8_auto_fails_closed_without_public_protected_ruleset(self):
        for field, value, code in (
            ("repository_visibility", "private", "STOP_AUTO_T1_REPOSITORY_NOT_PUBLIC"),
            ("main_protected", False, "STOP_AUTO_T1_MAIN_NOT_PROTECTED"),
            ("ruleset_enforcement", "disabled", "STOP_AUTO_T1_RULESET_NOT_ACTIVE"),
        ):
            with self.subTest(field=field):
                policy = copy.deepcopy(self.policy)
                gate = next(g for g in policy["gates"] if g["id"] == "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY")
                gate["trust_boundary_observation"][field] = value
                with self.assertRaisesRegex(AutomationPolicyError, code):
                    validate_policy(policy)

    def test_persistence_and_publication_are_not_auto_allowed(self):
        for gate_id in ("ACTIVE_RUNTIME_PERSISTENCE", "PRODUCT_OUTPUT_PUBLICATION"):
            with self.subTest(gate_id=gate_id):
                decision = evaluate_gate(self.policy, gate_id)
                self.assertEqual("BLOCK", decision["decision"])

    def test_unknown_gate_fails_closed(self):
        decision = evaluate_gate(self.policy, "UNKNOWN_GATE")
        self.assertEqual("BLOCK", decision["decision"])
        self.assertEqual("UNKNOWN_GATE_DEFAULT_DENY", decision["reason"])

    def test_manual_wrapper_remains_manual_backstop(self):
        workflow = M8_WRAPPER.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        for forbidden in ("workflow_call:", "schedule:", "workflow_run:", "pull_request:", "push:"):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("secrets: inherit", workflow)

    def test_reusable_worker_is_workflow_call_only_and_exact_readonly_secrets(self):
        reusable = M8_REUSABLE.read_text(encoding="utf-8")
        self.assertIn("workflow_call:", reusable)
        for forbidden in ("workflow_dispatch:", "schedule:", "workflow_run:", "pull_request:", "push:"):
            self.assertNotIn(forbidden, reusable)
        self.assertNotIn("secrets: inherit", reusable)
        for name in (
            "GOOGLE_DRIVE_READONLY_CLIENT_ID",
            "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
            "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
        ):
            self.assertIn(f"      {name}:\n        required: true", reusable)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_ID }}", reusable)
        self.assertIn("GOOGLE_DRIVE_CLIENT_SECRET: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_SECRET }}", reusable)
        self.assertIn("GOOGLE_DRIVE_REFRESH_TOKEN: ${{ secrets.GOOGLE_DRIVE_READONLY_REFRESH_TOKEN }}", reusable)

    def test_auto_orchestrator_is_push_main_bounded_and_secretless_before_trust_gate(self):
        automatic = M8_AUTO.read_text(encoding="utf-8")
        self.assertIn("push:", automatic)
        self.assertIn("      - main", automatic)
        self.assertIn("paths:", automatic)
        self.assertIn("docs/evidence/M8_T1_NO_CLICK_ACTIVATION_0.8.0.json", automatic)
        self.assertIn("docs/evidence/M7_SIOPE_*.json", automatic)
        for forbidden in ("workflow_dispatch:", "workflow_run:", "pull_request:", "schedule:", "secrets: inherit"):
            self.assertNotIn(forbidden, automatic)
        self.assertIn("permissions:\n  contents: read", automatic)
        self.assertIn("needs: trust-boundary", automatic)
        self.assertIn("python scripts/github_automation_policy_gate.py", automatic)
        self.assertIn("python scripts/github_m8_t1_no_click_trust_boundary_gate.py", automatic)
        self.assertIn("${{ github.ref_protected }}", automatic)
        for name in (
            "GOOGLE_DRIVE_READONLY_CLIENT_ID",
            "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
            "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
        ):
            self.assertIn(f"{name}: ${{{{ secrets.{name} }}}}", automatic)

    def test_runtime_capability_proof_precedes_drive_read_step_in_reusable_worker(self):
        reusable = M8_REUSABLE.read_text(encoding="utf-8")
        proof = "python scripts/github_m8_readonly_credential_capability_gate.py"
        live = "- name: Reler 9 Gold e gerar bundle local"
        self.assertLess(reusable.index(proof), reusable.index(live))

    def test_policy_gate_reports_m8_auto_allowed_and_trust_boundary(self):
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
        self.assertEqual("AUTO_ALLOWED", result["m8_no_click_decision"])
        self.assertEqual("READ_ONLY_PROVEN", result["m8_credential_capability"])
        self.assertTrue(result["m8_automatic_secret_bearing_trigger_present"])
        self.assertTrue(result["m8_trust_boundary_public"])
        self.assertTrue(result["m8_trust_boundary_main_protected"])
        self.assertEqual(21728151, result["m8_ruleset_id"])
        self.assertTrue(result["m8_ruleset_active"])
        self.assertEqual(0, result["drive_write_count"])
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
