from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess
from typing import Any


class F02FundebMonthlyPolicyFinalizationStop(ValueError):
    """Fail-closed stop for F02 monthly FUNDEB policy finalization evidence."""


GATE_ID = "F02_FUNDEB_MONTHLY_CASH_OFFLINE"
EXPECTED_IMPLEMENTATION_PR = 376


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


def git_head_parents(repo_root: str | Path) -> tuple[str, ...]:
    cp = subprocess.run(
        ["git", "-C", str(Path(repo_root)), "show", "-s", "--format=%P", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        _stop("GIT_HEAD_PARENTS_UNAVAILABLE", cp.stderr.strip())
    parents = tuple(part for part in cp.stdout.strip().split() if part)
    if not parents or any(not re.fullmatch(r"[0-9a-f]{40}", part) for part in parents):
        _stop("GIT_HEAD_PARENTS_INVALID")
    return parents


def validate_finalization(
    evidence: dict[str, Any],
    policy: dict[str, Any],
    gate_contract: dict[str, Any],
    *,
    head_parents: tuple[str, ...],
) -> dict[str, Any]:
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
    if verification.get("method") != "LOCAL_GIT_IMMEDIATE_PARENT_PLUS_CROSS_FILE_PIN_EQUALITY":
        _stop("VERIFICATION_METHOD")
    if verification.get("required_parent_of_validation_head") is not True:
        _stop("PARENT_PROOF_DISABLED")
    if verification.get("network_required") is not False:
        _stop("NETWORK_REQUIRED")
    if verification.get("github_signature_claimed_by_this_evidence") is not False:
        _stop("UNVERIFIABLE_SIGNATURE_CLAIM")
    if merge_sha not in head_parents:
        _stop("IMPLEMENTATION_MERGE_NOT_HEAD_PARENT", merge_sha)

    if policy.get("schema") != "ROBO_DADOS_PUBLICOS_AUTOMATION_POLICY_V1":
        _stop("POLICY_SCHEMA")
    gates = policy.get("gates")
    if not isinstance(gates, list):
        _stop("POLICY_GATES")
    matches = [row for row in gates if isinstance(row, dict) and row.get("id") == GATE_ID]
    if len(matches) != 1:
        _stop("POLICY_GATE_CARDINALITY", str(len(matches)))
    policy_gate = matches[0]

    if gate_contract.get("schema") != "F02_FUNDEB_MONTHLY_CASH_GATE_V1":
        _stop("GATE_SCHEMA")
    if gate_contract.get("status") != "REGISTERED_MANUAL_T0_REMOTE_CLOSED":
        _stop("GATE_STATUS")

    for label, row in (("policy", policy_gate), ("contract", gate_contract)):
        if row.get("implementation_pr_required") != EXPECTED_IMPLEMENTATION_PR:
            _stop("IMPLEMENTATION_PR_PIN_DRIFT", label)
        if row.get("implementation_pr_merged") != EXPECTED_IMPLEMENTATION_PR:
            _stop("IMPLEMENTATION_MERGED_PIN_DRIFT", label)
        if row.get("implementation_merge_sha") != merge_sha:
            _stop("IMPLEMENTATION_SHA_PIN_DRIFT", label)
        if row.get("implementation_merge_required_before_manual_execution") is not False:
            _stop("IMPLEMENTATION_BLOCKER_NOT_FINALIZED", label)

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

    blockers = set(policy_gate.get("blockers") or [])
    if "IMPLEMENTATION_PR_376_MUST_BE_MERGED_BEFORE_MANUAL_EXECUTION" in blockers:
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
        "head_parent_match": True,
        "auto_allowed": False,
        "remote_effects": 0,
    }


def validate_repository_state(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root)
    evidence = load_json(root / "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_0.8.0.json")
    policy = load_json(root / "config/automation_policy.v1.json")
    gate = load_json(root / "config/f02_fundeb_monthly_cash_gate.v1.json")
    return validate_finalization(
        evidence,
        policy,
        gate,
        head_parents=git_head_parents(root),
    )
