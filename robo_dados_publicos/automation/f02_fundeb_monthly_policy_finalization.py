from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess
from typing import Any


class F02FundebMonthlyPolicyFinalizationStop(ValueError):
    """Fail-closed stop for F02 monthly FUNDEB policy finalization evidence."""


GATE_ID = "F02_FUNDEB_MONTHLY_CASH_OFFLINE"
CI_GATE_ID = "F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_EVIDENCE_CI"
EXPECTED_IMPLEMENTATION_PR = 376
CI_OWNER_AUTH_RELATIVE_PATH = Path(
    "docs/evidence/F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_CI_OWNER_AUTHORIZATION_0.8.0.json"
)
CI_WORKFLOW_RELATIVE_PATH = Path(
    ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml"
)
EVIDENCE_RELATIVE_PATH = Path(
    "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json"
)
PREFINALIZATION_STATUS = "REGISTERED_MANUAL_T0_PENDING_IMPLEMENTATION_PR_376"
FINAL_STATUS = "REGISTERED_MANUAL_T0_REMOTE_CLOSED"
IMPLEMENTATION_BLOCKER = "IMPLEMENTATION_PR_376_MUST_BE_MERGED_BEFORE_MANUAL_EXECUTION"


def _stop(code: str, detail: str | None = None) -> None:
    suffix = f": {detail}" if detail else ""
    raise F02FundebMonthlyPolicyFinalizationStop(
        f"STOP_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_{code}{suffix}"
    )


def load_json(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise F02FundebMonthlyPolicyFinalizationStop(
            f"STOP_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_JSON_READ: {path}"
        ) from exc
    if not isinstance(value, dict):
        _stop("JSON_NOT_OBJECT", str(path))
    return value


def _git(repo_root: str | Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-C", str(Path(repo_root)), *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise F02FundebMonthlyPolicyFinalizationStop(
            "STOP_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_GIT_TIMEOUT"
        ) from exc


def verify_git_ancestor(repo_root: str | Path, commit_sha: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        _stop("IMPLEMENTATION_MERGE_SHA")
    exists = _git(repo_root, "cat-file", "-e", f"{commit_sha}^{{commit}}")
    if exists.returncode != 0:
        _stop("IMPLEMENTATION_COMMIT_OBJECT_MISSING", commit_sha)
    ancestor = _git(repo_root, "merge-base", "--is-ancestor", commit_sha, "HEAD")
    if ancestor.returncode == 1:
        _stop("IMPLEMENTATION_MERGE_NOT_ANCESTOR", commit_sha)
    if ancestor.returncode != 0:
        _stop("GIT_ANCESTRY_CHECK_FAILED", ancestor.stderr.strip())


def _policy_gate(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("schema") != "ROBO_DADOS_PUBLICOS_AUTOMATION_POLICY_V1":
        _stop("POLICY_SCHEMA")
    gates = policy.get("gates")
    if not isinstance(gates, list):
        _stop("POLICY_GATES")
    matches = [row for row in gates if isinstance(row, dict) and row.get("id") == GATE_ID]
    if len(matches) != 1:
        _stop("POLICY_GATE_CARDINALITY", str(len(matches)))
    return matches[0]


def _validate_remote_closed_manual_policy_gate(policy_gate: dict[str, Any]) -> None:
    if policy_gate.get("tier") != "T0_OFFLINE":
        _stop("POLICY_TIER")
    if policy_gate.get("auto_allowed") is not False:
        _stop("AUTO_ENABLED")
    if policy_gate.get("manual_execution_required") is not True:
        _stop("MANUAL_EXECUTION_NOT_REQUIRED")
    if policy_gate.get("no_workflow_trigger") is not True:
        _stop("WORKFLOW_TRIGGER_ALLOWED")
    if policy_gate.get("current_triggers") != []:
        _stop("TRIGGER_DRIFT")
    effects = policy_gate.get("effects")
    if not isinstance(effects, dict):
        _stop("POLICY_EFFECTS")
    for key in ("source_network", "drive_reads", "drive_writes", "publication"):
        if effects.get(key) is not False:
            _stop("REMOTE_EFFECT_ENABLED", key)


def _workflow_paths(text: str) -> list[str]:
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


def validate_ci_gate_install(policy: dict[str, Any], *, repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    gates = policy.get("gates")
    if not isinstance(gates, list):
        _stop("POLICY_GATES")
    matches = [row for row in gates if isinstance(row, dict) and row.get("id") == CI_GATE_ID]
    if len(matches) != 1:
        _stop("CI_GATE_CARDINALITY", str(len(matches)))
    gate = matches[0]
    if gate.get("tier") != "T0_OFFLINE":
        _stop("CI_GATE_TIER")
    if gate.get("auto_allowed") is not True:
        _stop("CI_GATE_AUTO_DISABLED")
    if gate.get("credential_capability") != "NONE":
        _stop("CI_GATE_CREDENTIAL_CAPABILITY")
    if gate.get("effects") != {
        "source_network": False,
        "drive_reads": False,
        "drive_writes": False,
        "publication": False,
    }:
        _stop("CI_GATE_EFFECTS")
    if gate.get("current_triggers") != [
        "pull_request:main:path-filtered",
        "workflow_dispatch",
    ]:
        _stop("CI_GATE_TRIGGERS")
    if gate.get("permissions") != {"contents": "read"}:
        _stop("CI_GATE_PERMISSIONS")
    if gate.get("persist_credentials") is not False:
        _stop("CI_GATE_PERSIST_CREDENTIALS")
    if gate.get("secrets") != []:
        _stop("CI_GATE_SECRETS")
    if gate.get("blockers") != []:
        _stop("CI_GATE_BLOCKERS")
    if gate.get("repository_checkout_read_only") is not True:
        _stop("CI_GATE_REPOSITORY_READ_BOUNDARY")
    if gate.get("owner_authorization_evidence") != str(CI_OWNER_AUTH_RELATIVE_PATH):
        _stop("CI_GATE_AUTH_EVIDENCE_PATH")
    if gate.get("owner_authorization_comment_id") != 5534958543:
        _stop("CI_GATE_AUTH_COMMENT")

    auth = load_json(root / CI_OWNER_AUTH_RELATIVE_PATH)
    if auth.get("schema") != "F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_CI_OWNER_AUTHORIZATION_V1":
        _stop("CI_AUTH_SCHEMA")
    if auth.get("status") != "AUTHORIZED_T0_READONLY_CI_GATE" or auth.get("authorized") is not True:
        _stop("CI_AUTH_STATUS")
    if auth.get("gate_id") != CI_GATE_ID:
        _stop("CI_AUTH_GATE_ID")
    record = auth.get("independent_github_owner_record")
    if not isinstance(record, dict):
        _stop("CI_AUTH_GITHUB_RECORD")
    if record.get("pr_number") != 380 or record.get("comment_id") != 5534958543:
        _stop("CI_AUTH_GITHUB_RECORD_PIN")
    if record.get("author_login") != "ferinbon-cpu":
        _stop("CI_AUTH_OWNER_LOGIN")
    boundary = auth.get("authorization_boundary")
    if not isinstance(boundary, dict) or any(value is not False for value in boundary.values()):
        _stop("CI_AUTH_BOUNDARY")

    workflow_path = root / CI_WORKFLOW_RELATIVE_PATH
    try:
        workflow_text = workflow_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise F02FundebMonthlyPolicyFinalizationStop(
            "STOP_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_CI_WORKFLOW_READ"
        ) from exc
    expected_paths = gate.get("path_filter")
    if not isinstance(expected_paths, list) or _workflow_paths(workflow_text) != expected_paths:
        _stop("CI_WORKFLOW_PATH_FILTER_DRIFT")
    required_fragments = (
        "permissions:\n  contents: read",
        "uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
        "uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
        "persist-credentials: false",
        "fetch-depth: 0",
        "python -m unittest discover -s tests -p 'test_f02_fundeb_monthly_cash_policy_finalization.py' -v",
        "python scripts/validate_f02_fundeb_monthly_policy_finalization.py",
    )
    for fragment in required_fragments:
        if fragment not in workflow_text:
            _stop("CI_WORKFLOW_REQUIRED_FRAGMENT", fragment)
    for forbidden in (
        "contents: write",
        "pull-requests: write",
        "secrets:",
        "pull_request_target",
        "repository_dispatch",
        "workflow_run",
        "schedule:",
        "git push",
        "gh pr",
    ):
        if forbidden in workflow_text:
            _stop("CI_WORKFLOW_FORBIDDEN_FRAGMENT", forbidden)

    return {
        "status": "PASS_F02_FUNDEB_MONTHLY_FINALIZATION_CI_GATE_INSTALL",
        "gate_id": CI_GATE_ID,
        "owner_authorization_comment_id": 5534958543,
        "workflow_paths_exact": True,
        "repository_read_only": True,
        "remote_effects": 0,
    }


def validate_prefinalization_install(
    policy: dict[str, Any], gate_contract: dict[str, Any]
) -> dict[str, Any]:
    """Validate the deliberately non-executable state used while installing this CI gate."""
    policy_gate = _policy_gate(policy)
    _validate_remote_closed_manual_policy_gate(policy_gate)

    if gate_contract.get("schema") != "F02_FUNDEB_MONTHLY_CASH_GATE_V1":
        _stop("GATE_SCHEMA")
    if gate_contract.get("status") != PREFINALIZATION_STATUS:
        _stop("PREFINALIZATION_GATE_STATUS")
    policy_blockers = list(policy_gate.get("blockers") or [])
    contract_blockers = list(gate_contract.get("blockers") or [])
    if policy_blockers != contract_blockers:
        _stop("PREFINALIZATION_BLOCKER_PARITY")

    for label, row in (("policy", policy_gate), ("contract", gate_contract)):
        if row.get("implementation_pr_required") != EXPECTED_IMPLEMENTATION_PR:
            _stop("IMPLEMENTATION_PR_PIN_DRIFT", label)
        if row.get("implementation_merge_required_before_manual_execution") is not True:
            _stop("PREFINALIZATION_BLOCKER_FLAG_MISSING", label)
        blockers = set(row.get("blockers") or [])
        if IMPLEMENTATION_BLOCKER not in blockers:
            _stop("PREFINALIZATION_IMPLEMENTATION_BLOCKER_MISSING", label)
    return {
        "status": "PASS_F02_FUNDEB_MONTHLY_POLICY_PREFINALIZATION_INSTALL",
        "implementation_pr": EXPECTED_IMPLEMENTATION_PR,
        "manual_execution_authorized": False,
        "auto_allowed": False,
        "remote_effects": 0,
    }


def validate_finalization(
    evidence: dict[str, Any],
    policy: dict[str, Any],
    gate_contract: dict[str, Any],
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Validate finalization and perform the Git object/ancestry proof internally."""
    if evidence.get("schema") != "F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_V2":
        _stop("EVIDENCE_SCHEMA")
    if evidence.get("status") != "READY_FOR_MANUAL_RUNTIME_AUTHORIZATION_ONLY":
        _stop("EVIDENCE_STATUS")
    if evidence.get("implementation_pr") != EXPECTED_IMPLEMENTATION_PR:
        _stop("IMPLEMENTATION_PR")

    merge_sha = str(evidence.get("implementation_merge_sha") or "").lower()
    if not re.fullmatch(r"[0-9a-f]{40}", merge_sha):
        _stop("IMPLEMENTATION_MERGE_SHA")

    verification = evidence.get("verification_contract")
    if not isinstance(verification, dict):
        _stop("VERIFICATION_CONTRACT")
    if verification.get("method") != "LOCAL_GIT_OBJECT_AND_ANCESTRY_PLUS_CROSS_FILE_PIN_EQUALITY":
        _stop("VERIFICATION_METHOD")
    if verification.get("full_git_history_required") is not True:
        _stop("FULL_HISTORY_REQUIREMENT")
    if verification.get("network_required_after_checkout") is not False:
        _stop("NETWORK_REQUIRED_AFTER_CHECKOUT")
    if verification.get("github_signature_claimed_by_this_evidence") is not False:
        _stop("UNVERIFIABLE_SIGNATURE_CLAIM")

    # This proof is not caller-supplied. It is an inseparable part of finalization.
    verify_git_ancestor(repo_root, merge_sha)

    policy_gate = _policy_gate(policy)
    _validate_remote_closed_manual_policy_gate(policy_gate)

    if gate_contract.get("schema") != "F02_FUNDEB_MONTHLY_CASH_GATE_V1":
        _stop("GATE_SCHEMA")
    if gate_contract.get("status") != FINAL_STATUS:
        _stop("GATE_STATUS")

    for label, row in (("policy", policy_gate), ("contract", gate_contract)):
        if row.get("implementation_pr_required") != EXPECTED_IMPLEMENTATION_PR:
            _stop("IMPLEMENTATION_PR_PIN_DRIFT", label)
        if row.get("implementation_pr_merged") != EXPECTED_IMPLEMENTATION_PR:
            _stop("IMPLEMENTATION_MERGED_PIN_DRIFT", label)
        if "implementation_merge_sha" not in row or not str(row.get("implementation_merge_sha") or "").strip():
            _stop("IMPLEMENTATION_SHA_PIN_MISSING", label)
        if row.get("implementation_merge_sha") != merge_sha:
            _stop("IMPLEMENTATION_SHA_PIN_DRIFT", label)
        if row.get("implementation_merge_required_before_manual_execution") != False:
            _stop("IMPLEMENTATION_BLOCKER_NOT_FINALIZED", label)

    policy_blockers = list(policy_gate.get("blockers") or [])
    contract_blockers = list(gate_contract.get("blockers") or [])
    if policy_blockers != contract_blockers:
        _stop("FINALIZATION_BLOCKER_PARITY")
    blockers = set(policy_blockers)
    if IMPLEMENTATION_BLOCKER in blockers:
        _stop("SATISFIED_BLOCKER_STILL_PRESENT")
    for required in (
        "EXPLICIT_OWNER_RUNTIME_AUTHORIZATION_REQUIRED",
        "LOCAL_SNAPSHOT_MATERIALIZATION_MUST_BE_BOUNDED",
        "SILVER_PERSISTENCE_REQUIRES_SEPARATE_CREATE_ONLY_EXECUTION",
    ):
        if required not in blockers:
            _stop("REQUIRED_BLOCKER_MISSING", required)

    expected_effects = evidence.get("gate_effects")
    if not isinstance(expected_effects, dict) or any(value is not False for value in expected_effects.values()):
        _stop("EVIDENCE_EFFECT_BOUNDARY")

    forbidden = set(evidence.get("still_forbidden") or [])
    for item in (
        "DELETE", "OVERWRITE", "SERVING", "LOOKER", "PUBLICATION", "SITE",
        "SCHEDULE", "RECURRENCE", "GOLD_PROMOTION",
        "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
    ):
        if item not in forbidden:
            _stop("FORBIDDEN_EFFECT_MISSING", item)

    return {
        "status": "PASS_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION",
        "implementation_pr": EXPECTED_IMPLEMENTATION_PR,
        "implementation_merge_sha": merge_sha,
        "implementation_ancestor_verified": True,
        "auto_allowed": False,
        "remote_effects": 0,
    }


def validate_repository_state(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    policy = load_json(root / "config/automation_policy.v1.json")
    gate = load_json(root / "config/f02_fundeb_monthly_cash_gate.v1.json")
    ci_gate = validate_ci_gate_install(policy, repo_root=root)
    evidence_path = root / EVIDENCE_RELATIVE_PATH

    if not evidence_path.exists():
        result = validate_prefinalization_install(policy, gate)
        result["ci_gate"] = ci_gate
        return result

    evidence = load_json(evidence_path)
    result = validate_finalization(evidence, policy, gate, repo_root=root)
    result["ci_gate"] = ci_gate
    return result
