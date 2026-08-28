import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy, validate_policy


ROOT = Path(__file__).resolve().parents[1]
M8_WRAPPER = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-gate.yml"
M8_REUSABLE = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-reusable.yml"


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

    def test_m8_no_click_is_blocked_after_live_proof_until_trust_boundary_review(self):
        decision = evaluate_gate(self.policy, "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY")
        self.assertEqual("BLOCK", decision["decision"])
        self.assertEqual("T1_REMOTE_READONLY", decision["tier"])
        self.assertNotIn("FIRST_LIVE_M8_READONLY_PRODUCT_GATE_NOT_YET_PROVEN", decision["blockers"])
        self.assertIn("CURRENT_MANUAL_WRAPPER_REQUIRES_EXPLICIT_CONFIRMATION", decision["blockers"])
        self.assertIn("MAIN_BRANCH_NOT_PROTECTED_FOR_SECRET_BEARING_AUTOMATION", decision["blockers"])
        self.assertIn("NO_CLICK_REQUIRES_TRUSTED_ORCHESTRATOR_REVIEW", decision["blockers"])

    def test_m8_policy_pins_exact_first_live_proof_and_reusable_worker(self):
        gate = next(g for g in self.policy["gates"] if g["id"] == "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY")
        proof = gate["live_proof"]
        self.assertEqual("READONLY_EXACT_SCOPE_FIRST_LIVE_GATE_PROVEN", gate["credential_capability"])
        self.assertEqual(
            ".github/workflows/m8-siope-historical-gold-product-output-readonly-reusable.yml",
            gate["reusable_workflow"],
        )
        self.assertEqual(["workflow_call"], gate["reusable_contract_triggers"])
        self.assertEqual("PRESENT_EXPLICIT_SECRETS_NO_SECRETS_INHERIT_NO_AUTO_CALLER", gate["reusable_worker_status"])
        self.assertEqual(33136736495, proof["run_id"])
        self.assertEqual(98738273929, proof["job_id"])
        self.assertEqual("8f80edcae45a373f85b84c03880842363661d870", proof["head_sha"])
        self.assertEqual(9672319372, proof["artifact_id"])
        self.assertEqual("sha256:a3afeed9c1449ab4806127024d044d177e76e8097894786b0e68bbbfffc60b51", proof["artifact_digest"])
        self.assertEqual("https://www.googleapis.com/auth/drive.readonly", proof["oauth_scope"])
        self.assertEqual(9, proof["drive_lookup_count"])
        self.assertEqual(9, proof["drive_download_count"])
        self.assertEqual(0, proof["drive_write_count"])
        self.assertEqual(0, proof["source_get_count"])
        self.assertFalse(proof["publication"])

    def test_persistence_and_publication_are_not_auto_allowed(self):
        for gate_id in ("ACTIVE_RUNTIME_PERSISTENCE", "PRODUCT_OUTPUT_PUBLICATION"):
            with self.subTest(gate_id=gate_id):
                decision = evaluate_gate(self.policy, gate_id)
                self.assertEqual("BLOCK", decision["decision"])

    def test_unknown_gate_fails_closed(self):
        decision = evaluate_gate(self.policy, "UNKNOWN_GATE")
        self.assertEqual("BLOCK", decision["decision"])
        self.assertEqual("UNKNOWN_GATE_DEFAULT_DENY", decision["reason"])

    def test_m8_manual_wrapper_has_only_dispatch_and_explicit_secret_mapping(self):
        workflow = M8_WRAPPER.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("confirm_m8_siope_historical_gold_product_output_readonly", workflow)
        self.assertNotIn("workflow_call:", workflow)
        for forbidden in ("schedule:", "workflow_run:", "pull_request:", "push:"):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("uses: ./.github/workflows/m8-siope-historical-gold-product-output-readonly-reusable.yml", workflow)
        self.assertNotIn("secrets: inherit", workflow)
        for name in (
            "GOOGLE_DRIVE_READONLY_CLIENT_ID",
            "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
            "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
        ):
            self.assertIn(f"{name}: ${{{{ secrets.{name} }}}}", workflow)

    def test_m8_reusable_worker_has_only_workflow_call_and_explicit_secret_contract(self):
        reusable = M8_REUSABLE.read_text(encoding="utf-8")
        self.assertIn("workflow_call:", reusable)
        self.assertNotIn("workflow_dispatch:", reusable)
        for forbidden in ("schedule:", "workflow_run:", "pull_request:", "push:"):
            self.assertNotIn(forbidden, reusable)
        self.assertIn("permissions:\n  contents: read", reusable)
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
        self.assertNotIn("${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}", reusable)
        self.assertNotIn("${{ secrets.GOOGLE_DRIVE_CLIENT_SECRET }}", reusable)
        self.assertNotIn("${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}", reusable)

    def test_runtime_capability_proof_precedes_drive_read_step_in_reusable_worker(self):
        reusable = M8_REUSABLE.read_text(encoding="utf-8")
        proof = "python scripts/github_m8_readonly_credential_capability_gate.py"
        live = "- name: Reler 9 Gold e gerar bundle local"
        self.assertIn(proof, reusable)
        self.assertIn(live, reusable)
        self.assertLess(reusable.index(proof), reusable.index(live))

    def test_policy_gate_runs_offline_and_reports_m8_block_with_reusable_ready(self):
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
        self.assertTrue(result["m8_first_live_proof_pinned"])
        self.assertEqual(33136736495, result["m8_first_live_run_id"])
        self.assertEqual("READONLY_EXACT_SCOPE_FIRST_LIVE_GATE_PROVEN", result["m8_credential_capability"])
        self.assertTrue(result["m8_reusable_worker_present"])
        self.assertTrue(result["m8_reusable_explicit_secrets"])
        self.assertFalse(result["m8_secrets_inherit"])
        self.assertFalse(result["m8_automatic_secret_bearing_trigger_present"])
        self.assertIn("MAIN_BRANCH_NOT_PROTECTED_FOR_SECRET_BEARING_AUTOMATION", result["m8_blockers"])
        self.assertEqual(0, result["drive_write_count"])
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
