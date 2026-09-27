"""Fail-closed trust-boundary checks for M8 T1 read-only no-click execution."""
from __future__ import annotations

from typing import Any

from .policy import evaluate_gate, validate_policy


M8_GATE_ID = "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY"
EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
EXPECTED_REF = "refs/heads/main"


class TrustBoundaryError(RuntimeError):
    """Raised when the runtime context is not the protected trusted boundary."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise TrustBoundaryError(code)


def evaluate_m8_t1_trust_boundary(
    policy: dict[str, Any],
    *,
    repository: str,
    ref: str,
    event_name: str,
    ref_protected: bool,
    repository_private: bool,
) -> dict[str, Any]:
    """Validate that automatic M8 execution is inside the approved T1 boundary."""
    validate_policy(policy)
    decision = evaluate_gate(policy, M8_GATE_ID)

    _require(repository == EXPECTED_REPOSITORY, "STOP_M8_T1_UNTRUSTED_REPOSITORY")
    _require(event_name == "push", "STOP_M8_T1_UNTRUSTED_EVENT")
    _require(ref == EXPECTED_REF, "STOP_M8_T1_UNTRUSTED_REF")
    _require(ref_protected is True, "STOP_M8_T1_MAIN_NOT_PROTECTED")
    _require(repository_private is False, "STOP_M8_T1_REPOSITORY_NOT_PUBLIC")
    _require(decision.get("decision") == "AUTO_ALLOWED", "STOP_M8_T1_POLICY_NOT_AUTO_ALLOWED")
    _require(decision.get("tier") == "T1_REMOTE_READONLY", "STOP_M8_T1_POLICY_TIER")

    gate = next(row for row in policy["gates"] if row["id"] == M8_GATE_ID)
    effects = gate["effects"]
    _require(gate.get("credential_capability") == "READ_ONLY_PROVEN", "STOP_M8_T1_READONLY_NOT_PROVEN")
    _require(effects.get("source_get_count") == 0, "STOP_M8_T1_SOURCE_GET_NOT_ZERO")
    _require(effects.get("drive_write_count") == 0, "STOP_M8_T1_DRIVE_WRITE_NOT_ZERO")
    _require(effects.get("publication") is False, "STOP_M8_T1_PUBLICATION_ENABLED")
    _require(gate.get("human_authorization") == "OWNER_COMPLETED_PUBLIC_REPO_AND_ACTIVE_MAIN_RULESET_FOR_T1_NO_CLICK", "STOP_M8_T1_HUMAN_AUTHORIZATION_MISSING")

    trust = gate.get("trust_boundary_observation") or {}
    _require(trust.get("repository_visibility") == "public", "STOP_M8_T1_POLICY_REPO_VISIBILITY")
    _require(trust.get("main_protected") is True, "STOP_M8_T1_POLICY_MAIN_PROTECTION")
    _require(trust.get("ruleset_id") == 21728151, "STOP_M8_T1_POLICY_RULESET_ID")
    _require(trust.get("ruleset_name") == "main-protection-v1", "STOP_M8_T1_POLICY_RULESET_NAME")
    _require(trust.get("ruleset_enforcement") == "active", "STOP_M8_T1_POLICY_RULESET_NOT_ACTIVE")

    return {
        "status": "PASS_M8_T1_TRUST_BOUNDARY",
        "repository": repository,
        "ref": ref,
        "event_name": event_name,
        "ref_protected": ref_protected,
        "repository_private": repository_private,
        "policy_decision": decision["decision"],
        "tier": decision["tier"],
        "credential_capability": gate["credential_capability"],
        "ruleset_id": trust["ruleset_id"],
        "ruleset_name": trust["ruleset_name"],
        "source_get_count": 0,
        "drive_write_count": 0,
        "publication_authorized": False,
        "future_batch_execution_authorized": False,
    }
