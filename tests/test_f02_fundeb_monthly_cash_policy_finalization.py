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
    verify_git_ancestor,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
WORKFLOW = ROOT / ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml"
MERGE_SHA = "48c2f7624dba3f46b61f09659f15d798b836c0ef"
GATE_ID = "F02_FUNDEB_MONTHLY_CASH_OFFLINE"
CI_GATE_ID = "F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_EVIDENCE_CI"
IMPLEMENTATION_BLOCKER = "IMPLEMENTATION_PR_376_MUST_BE_MERGED_BEFORE_MANUAL_EXECUTION"
REMAINING_BLOCKERS = [
    "EXPLICIT_OWNER_RUNTIME_AUTHORIZATION_REQUIRED",
    "LOCAL_SNAPSHOT_MATERIALIZATION_MUST_BE_BOUNDED",
    "SILVER_PERSISTENCE_REQUIRES_SEPARATE_CREATE_ONLY_EXECUTION",
]


def evidence() -> dict:
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


def workflow_paths(text: str) -> list[str]:
    lines = text.splitlines()
    active = False
    observed: list[str] = []
    for line in lines:
        if line.strip() == "paths:":
            active = True
            continue
        if not active:
            continue
        stripped = line.strip()
        if stripped.startswith('- "') and stripped.endswith('"'):
            observed.append(stripped[3:-1])
            continue
        if stripped and not stripped.startswith("#"):
            break
    return observed


def actual_policy_and_gate() -> tuple[dict, dict]:
    return load_json(POLICY), load_json(GATE)


def finalized_copies() -> tuple[dict, dict]:
    policy, gate = actual_policy_and_gate()
    policy = copy.deepcopy(policy)
    gate = copy.deepcopy(gate)
    policy_gate = next(row for row in policy["gates"] if row.get("id") == GATE_ID)
    for row in (policy_gate, gate):
        row["implementation_pr_required"] = 376
        row["implementation_pr_merged"] = 376
        row["implementation_merge_sha"] = MERGE_SHA
        row["implementation_merge_required_before_manual_execution"] = False
        row["blockers"] = list(REMAINING_BLOCKERS)
    gate["status"] = "REGISTERED_MANUAL_T0_REMOTE_CLOSED"
    return policy, gate


class F02FundebMonthlyPolicyFinalizationValidatorTests(unittest.TestCase):
    def test_actual_prefinalization_is_valid_but_not_executable(self):
        policy, gate = actual_policy_and_gate()
        result = validate_prefinalization_install(policy, gate)
        self.assertEqual(
            result["status"],
            "PASS_F02_FUNDEB_MONTHLY_POLICY_PREFINALIZATION_INSTALL",
        )
        self.assertFalse(result["manual_execution_authorized"])
        self.assertFalse(result["auto_allowed"])
        self.assertEqual(result["remote_effects"], 0)

    def test_prefinalization_requires_same_implementation_blocker_in_policy_and_contract(self):
        policy, gate = actual_policy_and_gate()
        bad_policy = copy.deepcopy(policy)
        policy_gate = next(row for row in bad_policy["gates"] if row.get("id") == GATE_ID)
        policy_gate["blockers"].remove(IMPLEMENTATION_BLOCKER)
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "PREFINALIZATION_IMPLEMENTATION_BLOCKER_MISSING: policy",
        ):
            validate_prefinalization_install(bad_policy, gate)

        bad_gate = copy.deepcopy(gate)
        bad_gate["blockers"].remove(IMPLEMENTATION_BLOCKER)
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "PREFINALIZATION_IMPLEMENTATION_BLOCKER_MISSING: contract",
        ):
            validate_prefinalization_install(policy, bad_gate)

    def test_actual_prefinalization_cannot_pass_finalization(self):
        policy, gate = actual_policy_and_gate()
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "GATE_STATUS"):
            validate_finalization(
                evidence(), policy, gate, implementation_ancestor_verified=True
            )

    def test_simulated_post_379_state_passes_only_when_policy_and_contract_both_pin_merge(self):
        policy, gate = finalized_copies()
        result = validate_finalization(
            evidence(), policy, gate, implementation_ancestor_verified=True
        )
        self.assertEqual(result["status"], "PASS_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION")
        self.assertEqual(result["implementation_merge_sha"], MERGE_SHA)
        self.assertFalse(result["auto_allowed"])
        self.assertEqual(result["remote_effects"], 0)

        policy_missing, gate_ok = finalized_copies()
        policy_gate = next(row for row in policy_missing["gates"] if row.get("id") == GATE_ID)
        del policy_gate["implementation_merge_sha"]
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "IMPLEMENTATION_SHA_PIN_MISSING: policy",
        ):
            validate_finalization(
                evidence(), policy_missing, gate_ok, implementation_ancestor_verified=True
            )

        policy_ok, gate_missing = finalized_copies()
        del gate_missing["implementation_merge_sha"]
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "IMPLEMENTATION_SHA_PIN_MISSING: contract",
        ):
            validate_finalization(
                evidence(), policy_ok, gate_missing, implementation_ancestor_verified=True
            )

    def test_auto_remote_and_ancestry_drift_fail_closed(self):
        policy, gate = finalized_copies()
        bad = copy.deepcopy(policy)
        next(row for row in bad["gates"] if row.get("id") == GATE_ID)["auto_allowed"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "AUTO_ENABLED"):
            validate_finalization(evidence(), bad, gate, implementation_ancestor_verified=True)

        bad = copy.deepcopy(policy)
        next(row for row in bad["gates"] if row.get("id") == GATE_ID)["effects"]["drive_writes"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "REMOTE_EFFECT_ENABLED"):
            validate_finalization(evidence(), bad, gate, implementation_ancestor_verified=True)

        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "IMPLEMENTATION_ANCESTRY_NOT_VERIFIED",
        ):
            validate_finalization(evidence(), policy, gate, implementation_ancestor_verified=False)

    def test_git_ancestor_check_accepts_ancestor_and_rejects_missing_or_nonancestor(self):
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
            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "IMPLEMENTATION_MERGE_NOT_ANCESTOR",
            ):
                verify_git_ancestor(repo, first)

    def test_workflow_paths_match_canonical_policy_path_filter_exactly(self):
        policy = load_json(POLICY)
        ci_gate = next(row for row in policy["gates"] if row.get("id") == CI_GATE_ID)
        observed = workflow_paths(WORKFLOW.read_text(encoding="utf-8"))
        self.assertEqual(observed, ci_gate["path_filter"])
        self.assertEqual(
            observed,
            [
                "config/automation_policy.v1.json",
                "config/f02_fundeb_monthly_cash_gate.v1.json",
                "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json",
                "robo_dados_publicos/automation/f02_fundeb_monthly_policy_finalization.py",
                "scripts/validate_f02_fundeb_monthly_policy_finalization.py",
                "tests/test_f02_fundeb_monthly_cash_policy_finalization.py",
            ],
        )

    def test_policy_path_trigger_cannot_loop_because_workflow_is_readonly(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('config/automation_policy.v1.json', text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("fetch-depth: 0", text)
        for forbidden in (
            "contents: write",
            "pull-requests: write",
            "git push",
            "gh pr",
            "repository_dispatch",
            "workflow_run",
            "schedule:",
            "pull_request_target",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
