from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.automation.f02_fundeb_monthly_policy_finalization import (
    F02FundebMonthlyPolicyFinalizationStop,
    load_json,
    validate_finalization,
    validate_repository_state,
    verify_git_ancestor,
)
from robo_dados_publicos.automation.policy import evaluate_gate, validate_policy

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
AUTH = ROOT / "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_OWNER_AUTHORIZATION_0.8.0.json"
FINALIZATION = ROOT / "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json"
SCRIPT = ROOT / "scripts/validate_f02_fundeb_monthly_policy_finalization.py"
IMPLEMENTATION_MERGE = "48c2f7624dba3f46b61f09659f15d798b836c0ef"


class F02FundebMonthlyCashPolicyFinalizationTests(unittest.TestCase):
    def test_policy_registers_manual_gate_but_auto_evaluator_still_blocks(self):
        policy = load_json(POLICY)
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
        self.assertEqual(gate["implementation_merge_sha"], IMPLEMENTATION_MERGE)
        self.assertTrue(all(value is False for value in gate["effects"].values()))
        decision = evaluate_gate(policy, gate["id"])
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["reason"], "POLICY_AUTO_ALLOWED_FALSE")

    def test_contract_blocks_remote_effects_and_preserves_manual_boundary(self):
        gate = load_json(GATE)
        self.assertEqual(gate["schema"], "F02_FUNDEB_MONTHLY_CASH_GATE_V1")
        self.assertEqual(gate["status"], "REGISTERED_MANUAL_T0_REMOTE_CLOSED")
        self.assertFalse(gate["implementation_merge_required_before_manual_execution"])
        self.assertEqual(gate["implementation_pr_required"], 376)
        self.assertFalse(gate["remote_drive_read_authorized"])
        self.assertTrue(gate["runtime_authorization_required"])
        self.assertTrue(all(gate["blocked_remote_effects"].values()))
        self.assertTrue(all(gate["semantic_blocks"].values()))

    def test_finalization_evidence_is_v2_and_contains_no_unverifiable_signature_claim(self):
        evidence = load_json(FINALIZATION)
        self.assertEqual(evidence["schema"], "F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_V2")
        self.assertEqual(evidence["implementation_merge_sha"], IMPLEMENTATION_MERGE)
        verification = evidence["verification_contract"]
        self.assertEqual(
            verification["method"],
            "LOCAL_GIT_OBJECT_AND_ANCESTRY_PLUS_CROSS_FILE_PIN_EQUALITY",
        )
        self.assertTrue(verification["full_git_history_required"])
        self.assertFalse(verification["network_required_after_checkout"])
        self.assertFalse(verification["github_signature_claimed_by_this_evidence"])
        self.assertNotIn("implementation_merge_verified", evidence)
        self.assertNotIn("github_signature_verified", evidence)

    def test_real_repository_state_validates_against_git_ancestry(self):
        result = validate_repository_state(ROOT)
        self.assertEqual(result["status"], "PASS_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION")
        self.assertEqual(result["implementation_merge_sha"], IMPLEMENTATION_MERGE)
        self.assertTrue(result["implementation_ancestor_verified"])
        self.assertFalse(result["auto_allowed"])
        self.assertEqual(result["remote_effects"], 0)

    def test_validation_cli_passes_on_real_repository_state(self):
        cp = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        payload = json.loads(cp.stdout)
        self.assertEqual(payload["status"], "PASS_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION")
        self.assertTrue(payload["implementation_ancestor_verified"])

    def test_missing_or_invalid_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "JSON_READ"):
                load_json(missing)
            bad = Path(td) / "bad.json"
            bad.write_text("{bad-json", encoding="utf-8")
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "JSON_READ"):
                load_json(bad)

    def test_wrong_or_missing_git_commit_fails_closed(self):
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "IMPLEMENTATION_COMMIT_OBJECT_MISSING",
        ):
            verify_git_ancestor(ROOT, "0" * 40)

    def test_cross_file_merge_sha_drift_fails_closed(self):
        evidence = load_json(FINALIZATION)
        policy = load_json(POLICY)
        gate = load_json(GATE)
        bad = copy.deepcopy(gate)
        bad["implementation_merge_sha"] = "0" * 40
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "IMPLEMENTATION_SHA_PIN_DRIFT",
        ):
            validate_finalization(
                evidence,
                policy,
                bad,
                implementation_ancestor_verified=True,
            )

    def test_remote_or_auto_effect_drift_fails_closed(self):
        evidence = load_json(FINALIZATION)
        policy = load_json(POLICY)
        gate = load_json(GATE)
        bad_policy = copy.deepcopy(policy)
        row = next(g for g in bad_policy["gates"] if g["id"] == "F02_FUNDEB_MONTHLY_CASH_OFFLINE")
        row["auto_allowed"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "AUTO_ENABLED"):
            validate_finalization(
                evidence,
                bad_policy,
                gate,
                implementation_ancestor_verified=True,
            )
        bad_policy = copy.deepcopy(policy)
        row = next(g for g in bad_policy["gates"] if g["id"] == "F02_FUNDEB_MONTHLY_CASH_OFFLINE")
        row["effects"]["drive_writes"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "REMOTE_EFFECT_ENABLED"):
            validate_finalization(
                evidence,
                bad_policy,
                gate,
                implementation_ancestor_verified=True,
            )

    def test_satisfied_blocker_removed_but_required_blockers_remain(self):
        policy = load_json(POLICY)
        gate = next(g for g in policy["gates"] if g["id"] == "F02_FUNDEB_MONTHLY_CASH_OFFLINE")
        blockers = set(gate["blockers"])
        self.assertNotIn("IMPLEMENTATION_PR_376_MUST_BE_MERGED_BEFORE_MANUAL_EXECUTION", blockers)
        self.assertIn("EXPLICIT_OWNER_RUNTIME_AUTHORIZATION_REQUIRED", blockers)
        self.assertIn("LOCAL_SNAPSHOT_MATERIALIZATION_MUST_BE_BOUNDED", blockers)
        self.assertIn("SILVER_PERSISTENCE_REQUIRES_SEPARATE_CREATE_ONLY_EXECUTION", blockers)

    def test_owner_policy_authorization_is_not_runtime_execution_authorization(self):
        auth = load_json(AUTH)
        self.assertEqual(auth["status"], "AUTHORIZED_POLICY_CHANGE")
        self.assertTrue(auth["runtime_authorization_is_separate"])
        self.assertTrue(auth["runtime_authorization_must_be_ephemeral_and_exact_sha_pinned"])
        self.assertIn("AUTO_EXECUTION", auth["explicitly_not_authorized"])
        self.assertIn("SILVER_WRITE_BY_THIS_POLICY_CHANGE", auth["explicitly_not_authorized"])


if __name__ == "__main__":
    unittest.main()
