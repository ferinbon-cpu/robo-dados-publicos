from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.automation.f02_fundeb_monthly_policy_finalization import (
    F02FundebMonthlyPolicyFinalizationStop,
    load_json,
    validate_finalization,
    validate_prefinalization_install,
    validate_repository_state,
    verify_git_ancestor,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
ACTUAL_GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
WORKFLOW = ROOT / ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml"
MERGE_SHA = "48c2f7624dba3f46b61f09659f15d798b836c0ef"


def evidence():
    return {
        "schema": "F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_V2",
        "status": "READY_FOR_MANUAL_RUNTIME_AUTHORIZATION_ONLY",
        "implementation_pr": 376,
        "implementation_merge_sha": MERGE_SHA,
        "verification_contract": {
            "method": "LOCAL_GIT_OBJECT_AND_ANCESTRY_PLUS_CROSS_FILE_PIN_EQUALITY",
            "full_git_history_required": True,
            "network_required_after_checkout": False,
            "github_signature_claimed_by_this_evidence": False,
        },
        "gate_effects": {
            "auto_allowed": False,
            "workflow_trigger": False,
            "source_network": False,
            "drive_read": False,
            "drive_write": False,
            "publication": False,
            "schedule": False,
            "recurrence": False,
        },
        "still_forbidden": [
            "DELETE", "OVERWRITE", "SERVING", "LOOKER", "PUBLICATION", "SITE",
            "SCHEDULE", "RECURRENCE", "GOLD_PROMOTION",
            "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
        ],
    }


def execution_gate(*, finalized: bool = True):
    gate = {
        "id": "F02_FUNDEB_MONTHLY_CASH_OFFLINE",
        "tier": "T0_OFFLINE",
        "auto_allowed": False,
        "manual_execution_required": True,
        "no_workflow_trigger": True,
        "current_triggers": [],
        "effects": {
            "source_network": False,
            "drive_reads": False,
            "drive_writes": False,
            "publication": False,
        },
        "implementation_pr_required": 376,
        "implementation_merge_required_before_manual_execution": not finalized,
        "blockers": [
            "EXPLICIT_OWNER_RUNTIME_AUTHORIZATION_REQUIRED",
            "LOCAL_SNAPSHOT_MATERIALIZATION_MUST_BE_BOUNDED",
            "SILVER_PERSISTENCE_REQUIRES_SEPARATE_CREATE_ONLY_EXECUTION",
        ],
    }
    if finalized:
        gate.update({
            "implementation_pr_merged": 376,
            "implementation_merge_sha": MERGE_SHA,
        })
    else:
        gate["blockers"].insert(0, "IMPLEMENTATION_PR_376_MUST_BE_MERGED_BEFORE_MANUAL_EXECUTION")
    return gate


def policy(*, finalized: bool = True):
    return {
        "schema": "ROBO_DADOS_PUBLICOS_AUTOMATION_POLICY_V1",
        "gates": [execution_gate(finalized=finalized)],
    }


def gate_contract(*, finalized: bool = True):
    gate = execution_gate(finalized=finalized)
    gate.update({
        "schema": "F02_FUNDEB_MONTHLY_CASH_GATE_V1",
        "status": (
            "REGISTERED_MANUAL_T0_REMOTE_CLOSED"
            if finalized
            else "REGISTERED_MANUAL_T0_PENDING_IMPLEMENTATION_PR_376"
        ),
    })
    return gate


class F02FundebMonthlyPolicyFinalizationValidatorTests(unittest.TestCase):
    def test_prefinalization_install_is_valid_but_not_executable(self):
        result = validate_prefinalization_install(
            policy(finalized=False), gate_contract(finalized=False)
        )
        self.assertEqual(
            result["status"],
            "PASS_F02_FUNDEB_MONTHLY_POLICY_PREFINALIZATION_INSTALL",
        )
        self.assertFalse(result["manual_execution_authorized"])
        self.assertFalse(result["auto_allowed"])
        self.assertEqual(result["remote_effects"], 0)

    def test_repository_lifecycle_accepts_missing_evidence_only_in_prefinalization(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config").mkdir(parents=True)
            (root / "docs/evidence").mkdir(parents=True)
            (root / "config/automation_policy.v1.json").write_text(
                json.dumps(policy(finalized=False)), encoding="utf-8"
            )
            (root / "config/f02_fundeb_monthly_cash_gate.v1.json").write_text(
                json.dumps(gate_contract(finalized=False)), encoding="utf-8"
            )
            result = validate_repository_state(root)
        self.assertEqual(
            result["status"],
            "PASS_F02_FUNDEB_MONTHLY_POLICY_PREFINALIZATION_INSTALL",
        )

    def test_synthetic_finalization_passes_only_with_ancestor_proof(self):
        result = validate_finalization(
            evidence(), policy(), gate_contract(), implementation_ancestor_verified=True
        )
        self.assertEqual(result["status"], "PASS_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION")
        self.assertTrue(result["implementation_ancestor_verified"])
        self.assertFalse(result["auto_allowed"])
        self.assertEqual(result["remote_effects"], 0)
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "IMPLEMENTATION_ANCESTRY_NOT_VERIFIED",
        ):
            validate_finalization(
                evidence(), policy(), gate_contract(), implementation_ancestor_verified=False
            )

    def test_current_repository_prefinalization_state_passes_install_lifecycle(self):
        actual_policy = load_json(POLICY)
        actual_gate = load_json(ACTUAL_GATE)
        result = validate_prefinalization_install(actual_policy, actual_gate)
        self.assertEqual(
            result["status"],
            "PASS_F02_FUNDEB_MONTHLY_POLICY_PREFINALIZATION_INSTALL",
        )
        self.assertFalse(result["manual_execution_authorized"])

    def test_missing_merge_sha_and_pin_auto_remote_drift_fail_closed(self):
        missing_sha = evidence()
        del missing_sha["implementation_merge_sha"]
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "IMPLEMENTATION_MERGE_SHA"):
            validate_finalization(missing_sha, policy(), gate_contract(), implementation_ancestor_verified=True)

        bad_gate = gate_contract()
        bad_gate["implementation_merge_sha"] = "0" * 40
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "IMPLEMENTATION_SHA_PIN_DRIFT"):
            validate_finalization(evidence(), policy(), bad_gate, implementation_ancestor_verified=True)

        bad_policy = policy()
        bad_policy["gates"][0]["auto_allowed"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "AUTO_ENABLED"):
            validate_finalization(evidence(), bad_policy, gate_contract(), implementation_ancestor_verified=True)

        bad_policy = policy()
        bad_policy["gates"][0]["effects"]["drive_writes"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "REMOTE_EFFECT_ENABLED"):
            validate_finalization(evidence(), bad_policy, gate_contract(), implementation_ancestor_verified=True)

    def test_missing_or_invalid_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "JSON_READ"):
                load_json(missing)
            invalid = Path(td) / "invalid.json"
            invalid.write_text("{bad", encoding="utf-8")
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "JSON_READ"):
                load_json(invalid)

    def test_git_ancestor_check_accepts_ancestor_rejects_missing_and_nonancestor(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "F02 Test"], check=True)
            (repo / "a.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "first"], check=True)
            first = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            (repo / "a.txt").write_text("two\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-am", "second"], check=True)
            verify_git_ancestor(repo, first)

            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "IMPLEMENTATION_COMMIT_OBJECT_MISSING",
            ):
                verify_git_ancestor(repo, "0" * 40)

            subprocess.run(["git", "-C", str(repo), "checkout", "--orphan", "other"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "rm", "-rf", "."], check=True, capture_output=True)
            (repo / "b.txt").write_text("other\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "b.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "other"], check=True)
            other = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "IMPLEMENTATION_MERGE_NOT_ANCESTOR",
            ):
                verify_git_ancestor(repo, first)
            self.assertRegex(other, r"^[0-9a-f]{40}$")

    def test_workflow_paths_match_canonical_policy_filter_exactly(self):
        raw = json.loads(POLICY.read_text(encoding="utf-8"))
        ci_gate = next(
            row for row in raw["gates"]
            if row.get("id") == "F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_EVIDENCE_CI"
        )
        expected = ci_gate["path_filter"]
        text = WORKFLOW.read_text(encoding="utf-8")
        for path in expected:
            self.assertEqual(text.count(f'- "{path}"'), 1, path)
        self.assertEqual(
            expected,
            [
                "config/automation_policy.v1.json",
                "config/f02_fundeb_monthly_cash_gate.v1.json",
                "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json",
                "robo_dados_publicos/automation/f02_fundeb_monthly_policy_finalization.py",
                "scripts/validate_f02_fundeb_monthly_policy_finalization.py",
                "tests/test_f02_fundeb_monthly_cash_policy_finalization.py",
            ],
        )

    def test_workflow_is_full_history_readonly_and_lifecycle_aware(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("fetch-depth: 0", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("Validate prefinalization install or finalized pinned implementation", text)
        self.assertNotIn("test -f docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json", text)


if __name__ == "__main__":
    unittest.main()
