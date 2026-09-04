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
    validate_ci_gate_install,
    validate_finalization,
    validate_prefinalization_install,
    validate_repository_state,
    verify_git_ancestor,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
WORKFLOW = ROOT / ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml"
CI_AUTH = ROOT / "docs/evidence/F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_CI_OWNER_AUTHORIZATION_0.8.0.json"
GATE_ID = "F02_FUNDEB_MONTHLY_CASH_OFFLINE"
CI_GATE_ID = "F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_EVIDENCE_CI"
IMPLEMENTATION_BLOCKER = "IMPLEMENTATION_PR_376_MUST_BE_MERGED_BEFORE_MANUAL_EXECUTION"
REMAINING_BLOCKERS = [
    "EXPLICIT_OWNER_RUNTIME_AUTHORIZATION_REQUIRED",
    "LOCAL_SNAPSHOT_MATERIALIZATION_MUST_BE_BOUNDED",
    "SILVER_PERSISTENCE_REQUIRES_SEPARATE_CREATE_ONLY_EXECUTION",
]


def evidence(merge_sha: str) -> dict:
    return {
        "schema": "F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_V2",
        "status": "READY_FOR_MANUAL_RUNTIME_AUTHORIZATION_ONLY",
        "implementation_pr": 376,
        "implementation_merge_sha": merge_sha,
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


def install_ci_gate_files(root: Path) -> None:
    (root / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (root / "docs/evidence").mkdir(parents=True, exist_ok=True)
    (root / ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml").write_text(
        WORKFLOW.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "docs/evidence/F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_CI_OWNER_AUTHORIZATION_0.8.0.json").write_text(
        CI_AUTH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def actual_policy_and_gate() -> tuple[dict, dict]:
    return load_json(POLICY), load_json(GATE)


def finalized_copies(merge_sha: str) -> tuple[dict, dict]:
    policy, gate = actual_policy_and_gate()
    policy = copy.deepcopy(policy)
    gate = copy.deepcopy(gate)
    policy_gate = next(row for row in policy["gates"] if row.get("id") == GATE_ID)
    for row in (policy_gate, gate):
        row["implementation_pr_required"] = 376
        row["implementation_pr_merged"] = 376
        row["implementation_merge_sha"] = merge_sha
        row["implementation_merge_required_before_manual_execution"] = False
        row["blockers"] = list(REMAINING_BLOCKERS)
    gate["status"] = "REGISTERED_MANUAL_T0_REMOTE_CLOSED"
    return policy, gate


def prefinalized_copies() -> tuple[dict, dict]:
    policy, gate = actual_policy_and_gate()
    policy = copy.deepcopy(policy)
    gate = copy.deepcopy(gate)
    policy_gate = next(row for row in policy["gates"] if row.get("id") == GATE_ID)
    for row in (policy_gate, gate):
        row["implementation_pr_required"] = 376
        row.pop("implementation_pr_merged", None)
        row.pop("implementation_merge_sha", None)
        row.pop("policy_finalization_evidence", None)
        row["implementation_merge_required_before_manual_execution"] = True
        row["blockers"] = [IMPLEMENTATION_BLOCKER, *REMAINING_BLOCKERS]
    gate["status"] = "REGISTERED_MANUAL_T0_PENDING_IMPLEMENTATION_PR_376"
    return policy, gate


def init_repo(root: Path) -> str:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "F02 Test"], check=True)
    (root / "anchor.txt").write_text("implementation\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "anchor.txt"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "implementation"], check=True)
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def commit_state(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "state"], check=True)


def workflow_paths(text: str) -> list[str]:
    active = False
    result: list[str] = []
    for line in text.splitlines():
        if line.strip() == "paths:":
            active = True
            continue
        if not active:
            continue
        stripped = line.strip()
        if stripped.startswith('- "') and stripped.endswith('"'):
            result.append(stripped[3:-1])
            continue
        if stripped and not stripped.startswith("#"):
            break
    return result


class F02FundebMonthlyPolicyFinalizationValidatorTests(unittest.TestCase):
    def test_ci_gate_is_registered_and_workflow_filter_matches_policy_exactly(self):
        policy = load_json(POLICY)
        result = validate_ci_gate_install(policy, repo_root=ROOT)
        self.assertEqual(
            result["status"],
            "PASS_F02_FUNDEB_MONTHLY_FINALIZATION_CI_GATE_INSTALL",
        )
        self.assertEqual(result["owner_authorization_comment_id"], 5534958543)
        ci_gate = next(row for row in policy["gates"] if row.get("id") == CI_GATE_ID)
        self.assertEqual(ci_gate["tier"], "T0_OFFLINE")
        self.assertTrue(ci_gate["auto_allowed"])
        self.assertEqual(ci_gate["effects"], {
            "source_network": False,
            "drive_reads": False,
            "drive_writes": False,
            "publication": False,
        })
        self.assertEqual(
            workflow_paths(WORKFLOW.read_text(encoding="utf-8")),
            ci_gate["path_filter"],
        )

    def test_policy_path_trigger_is_readonly_and_cannot_self_loop(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('config/automation_policy.v1.json', text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("fetch-depth: 0", text)
        for forbidden in (
            "contents: write", "pull-requests: write", "git push", "gh pr",
            "repository_dispatch", "workflow_run", "schedule:", "pull_request_target",
        ):
            self.assertNotIn(forbidden, text)

    def test_ci_gate_missing_blockers_and_path_filter_drift_fail_closed(self):
        policy = load_json(POLICY)

        bad_policy = copy.deepcopy(policy)
        bad_ci = next(row for row in bad_policy["gates"] if row.get("id") == CI_GATE_ID)
        del bad_ci["blockers"]
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "CI_GATE_BLOCKERS",
        ):
            validate_ci_gate_install(bad_policy, repo_root=ROOT)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            install_ci_gate_files(root)
            workflow = root / ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml"
            text = workflow.read_text(encoding="utf-8")
            text = text.replace(
                '      - "config/automation_policy.v1.json"\n',
                '      - "UNEXPECTED_PATH"\n',
                1,
            )
            workflow.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "CI_WORKFLOW_PATH_FILTER_DRIFT",
            ):
                validate_ci_gate_install(policy, repo_root=root)

    def test_synthetic_prefinalization_is_safe_but_nonexecuting_and_blocker_is_symmetric(self):
        policy, gate = prefinalized_copies()
        result = validate_prefinalization_install(policy, gate)
        self.assertEqual(result["status"], "PASS_F02_FUNDEB_MONTHLY_POLICY_PREFINALIZATION_INSTALL")
        self.assertFalse(result["manual_execution_authorized"])
        policy_gate = next(row for row in policy["gates"] if row.get("id") == GATE_ID)
        self.assertIn(IMPLEMENTATION_BLOCKER, policy_gate["blockers"])
        self.assertIn(IMPLEMENTATION_BLOCKER, gate["blockers"])

    def test_ci_gate_missing_or_malformed_workflow_and_auth_drift_fail_closed(self):
        policy = load_json(POLICY)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs/evidence").mkdir(parents=True)
            (root / "docs/evidence/F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_CI_OWNER_AUTHORIZATION_0.8.0.json").write_text(
                CI_AUTH.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "CI_WORKFLOW_READ",
            ):
                validate_ci_gate_install(policy, repo_root=root)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            install_ci_gate_files(root)
            workflow = root / ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml"
            workflow.write_text("name: malformed\non:\n  pull_request:\n", encoding="utf-8")
            with self.assertRaises(F02FundebMonthlyPolicyFinalizationStop):
                validate_ci_gate_install(policy, repo_root=root)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            install_ci_gate_files(root)
            auth_path = root / "docs/evidence/F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_CI_OWNER_AUTHORIZATION_0.8.0.json"
            auth = json.loads(auth_path.read_text(encoding="utf-8"))
            auth["independent_github_owner_record"]["comment_id"] = 0
            auth_path.write_text(json.dumps(auth), encoding="utf-8")
            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "CI_AUTH_GITHUB_RECORD_PIN",
            ):
                validate_ci_gate_install(policy, repo_root=root)

    def test_blocker_parity_drift_fails_in_prefinalization_and_finalization(self):
        policy, gate = prefinalized_copies()
        bad_gate = copy.deepcopy(gate)
        bad_gate["blockers"] = list(bad_gate["blockers"]) + ["DRIFT"]
        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "PREFINALIZATION_BLOCKER_PARITY",
        ):
            validate_prefinalization_install(policy, bad_gate)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            merge_sha = init_repo(root)
            final_policy, final_gate = finalized_copies(merge_sha)
            final_gate["blockers"] = list(final_gate["blockers"]) + ["DRIFT"]
            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "FINALIZATION_BLOCKER_PARITY",
            ):
                validate_finalization(
                    evidence(merge_sha),
                    final_policy,
                    final_gate,
                    repo_root=root,
                )

    def test_finalization_performs_real_ancestry_proof_internally(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            merge_sha = init_repo(root)
            policy, gate = finalized_copies(merge_sha)
            result = validate_finalization(
                evidence(merge_sha), policy, gate, repo_root=root
            )
            self.assertTrue(result["implementation_ancestor_verified"])
            self.assertEqual(result["implementation_merge_sha"], merge_sha)

            missing = "0" * 40
            policy_missing, gate_missing = finalized_copies(missing)
            with self.assertRaisesRegex(
                F02FundebMonthlyPolicyFinalizationStop,
                "IMPLEMENTATION_COMMIT_OBJECT_MISSING",
            ):
                validate_finalization(
                    evidence(missing), policy_missing, gate_missing, repo_root=root
                )

    def test_repository_state_with_evidence_and_prefinal_gate_fails_closed_after_ancestry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            merge_sha = init_repo(root)
            policy, gate = finalized_copies(merge_sha)
            gate["status"] = "REGISTERED_MANUAL_T0_PENDING_IMPLEMENTATION_PR_376"
            (root / "config").mkdir(parents=True)
            (root / "docs/evidence").mkdir(parents=True)
            (root / "config/automation_policy.v1.json").write_text(json.dumps(policy), encoding="utf-8")
            (root / "config/f02_fundeb_monthly_cash_gate.v1.json").write_text(json.dumps(gate), encoding="utf-8")
            install_ci_gate_files(root)
            (root / "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json").write_text(
                json.dumps(evidence(merge_sha)), encoding="utf-8"
            )
            commit_state(root)
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "GATE_STATUS"):
                validate_repository_state(root)

    def test_repository_state_finalized_transition_passes_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            merge_sha = init_repo(root)
            policy, gate = finalized_copies(merge_sha)
            (root / "config").mkdir(parents=True)
            (root / "docs/evidence").mkdir(parents=True)
            (root / "config/automation_policy.v1.json").write_text(json.dumps(policy), encoding="utf-8")
            (root / "config/f02_fundeb_monthly_cash_gate.v1.json").write_text(json.dumps(gate), encoding="utf-8")
            install_ci_gate_files(root)
            (root / "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json").write_text(
                json.dumps(evidence(merge_sha)), encoding="utf-8"
            )
            commit_state(root)
            result = validate_repository_state(root)
            self.assertEqual(result["status"], "PASS_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION")
            self.assertTrue(result["implementation_ancestor_verified"])

    def test_finalization_requires_merge_sha_in_policy_and_contract_and_remote_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            merge_sha = init_repo(root)
            policy, gate = finalized_copies(merge_sha)
            policy_gate = next(row for row in policy["gates"] if row.get("id") == GATE_ID)

            bad_policy = copy.deepcopy(policy)
            del next(row for row in bad_policy["gates"] if row.get("id") == GATE_ID)["implementation_merge_sha"]
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "IMPLEMENTATION_SHA_PIN_MISSING: policy"):
                validate_finalization(evidence(merge_sha), bad_policy, gate, repo_root=root)

            bad_gate = copy.deepcopy(gate)
            del bad_gate["implementation_merge_sha"]
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "IMPLEMENTATION_SHA_PIN_MISSING: contract"):
                validate_finalization(evidence(merge_sha), policy, bad_gate, repo_root=root)

            bad_policy = copy.deepcopy(policy)
            next(row for row in bad_policy["gates"] if row.get("id") == GATE_ID)["effects"]["drive_writes"] = True
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "REMOTE_EFFECT_ENABLED"):
                validate_finalization(evidence(merge_sha), bad_policy, gate, repo_root=root)

            self.assertFalse(policy_gate["auto_allowed"])
            self.assertEqual(policy_gate["current_triggers"], [])

    def test_verify_git_ancestor_rejects_nonancestor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = init_repo(root)
            subprocess.run(["git", "-C", str(root), "checkout", "--orphan", "other"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(root), "rm", "-rf", "."], check=True, capture_output=True)
            (root / "other.txt").write_text("other\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "other.txt"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "other"], check=True)
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "IMPLEMENTATION_MERGE_NOT_ANCESTOR"):
                verify_git_ancestor(root, first)


if __name__ == "__main__":
    unittest.main()
