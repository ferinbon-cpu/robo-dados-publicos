"""Fail-closed evaluator for repository automation policy.

The policy does not execute workflows and does not authorize remote effects.
It only answers whether the checked-in policy is internally consistent and
whether a named gate is eligible for automatic execution.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


POLICY_RELATIVE_PATH = Path("config/automation_policy.v1.json")
SCHEMA = "ROBO_DADOS_PUBLICOS_AUTOMATION_POLICY_V1"
AUTO_ALLOWED_TIERS = {"T0_OFFLINE", "T1_REMOTE_READONLY"}
MANUAL_ONLY_TIERS = {"T2_CREATE_ONLY", "T3_MUTATING_OR_PUBLICATION"}
READONLY_PROVEN = "READ_ONLY_PROVEN"
T1_HUMAN_AUTHORIZATION = "OWNER_COMPLETED_PUBLIC_REPO_AND_ACTIVE_MAIN_RULESET_FOR_T1_NO_CLICK"


class AutomationPolicyError(RuntimeError):
    """Raised when the automation policy is missing, ambiguous or unsafe."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AutomationPolicyError(code)


def load_policy(root: Path | str) -> dict[str, Any]:
    path = Path(root) / POLICY_RELATIVE_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AutomationPolicyError("STOP_AUTOMATION_POLICY_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise AutomationPolicyError("STOP_AUTOMATION_POLICY_INVALID_JSON") from exc
    _require(isinstance(data, dict), "STOP_AUTOMATION_POLICY_NOT_OBJECT")
    return data


def _gate_map(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = policy.get("gates")
    _require(isinstance(rows, list) and rows, "STOP_AUTOMATION_POLICY_GATES_INVALID")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        _require(isinstance(row, dict), "STOP_AUTOMATION_POLICY_GATE_NOT_OBJECT")
        gate_id = row.get("id")
        _require(isinstance(gate_id, str) and gate_id, "STOP_AUTOMATION_POLICY_GATE_ID_INVALID")
        _require(gate_id not in out, f"STOP_AUTOMATION_POLICY_DUPLICATE_GATE_{gate_id}")
        out[gate_id] = row
    return out


def validate_policy(policy: dict[str, Any]) -> dict[str, Any]:
    _require(policy.get("schema") == SCHEMA, "STOP_AUTOMATION_POLICY_SCHEMA")
    _require(policy.get("default_decision") == "BLOCK", "STOP_AUTOMATION_POLICY_DEFAULT_NOT_BLOCK")

    invariants = policy.get("policy_invariants")
    _require(isinstance(invariants, dict), "STOP_AUTOMATION_POLICY_INVARIANTS_INVALID")
    _require(invariants.get("agent_may_authorize_remote_execution") is False, "STOP_AGENT_REMOTE_AUTHORIZATION_ENABLED")
    _require(
        invariants.get("agent_may_lower_risk_tier_in_same_patch_that_enables_auto_execution") is False,
        "STOP_AGENT_SELF_RECLASSIFICATION_ENABLED",
    )
    _require(invariants.get("bronze_immutable") is True, "STOP_BRONZE_IMMUTABILITY_DISABLED")
    _require(invariants.get("publication_is_separate_gate") is True, "STOP_PUBLICATION_SEPARATION_DISABLED")
    _require(
        invariants.get("fail_closed_on_missing_duplicate_or_drifted_evidence") is True,
        "STOP_FAIL_CLOSED_DISABLED",
    )
    _require(invariants.get("future_batch_execution_authorized") is False, "STOP_FUTURE_BATCH_IMPLICITLY_AUTHORIZED")

    tiers = policy.get("tiers")
    _require(isinstance(tiers, dict), "STOP_AUTOMATION_POLICY_TIERS_INVALID")
    _require(AUTO_ALLOWED_TIERS | MANUAL_ONLY_TIERS <= set(tiers), "STOP_AUTOMATION_POLICY_TIER_SET")

    gates = _gate_map(policy)
    for gate_id, gate in gates.items():
        tier = gate.get("tier")
        _require(tier in tiers, f"STOP_AUTOMATION_POLICY_UNKNOWN_TIER_{gate_id}")
        auto_allowed = gate.get("auto_allowed")
        _require(isinstance(auto_allowed, bool), f"STOP_AUTOMATION_POLICY_AUTO_FLAG_{gate_id}")
        effects = gate.get("effects")
        _require(isinstance(effects, dict), f"STOP_AUTOMATION_POLICY_EFFECTS_{gate_id}")

        if tier in MANUAL_ONLY_TIERS:
            _require(auto_allowed is False, f"STOP_MANUAL_TIER_AUTO_ENABLED_{gate_id}")

        if auto_allowed:
            _require(tier in AUTO_ALLOWED_TIERS, f"STOP_AUTO_TIER_NOT_ELIGIBLE_{gate_id}")
            _require(effects.get("drive_writes", effects.get("drive_write_count", 0)) in (False, 0), f"STOP_AUTO_DRIVE_WRITE_{gate_id}")
            _require(effects.get("publication") is False, f"STOP_AUTO_PUBLICATION_{gate_id}")
            if tier == "T1_REMOTE_READONLY":
                _require(
                    gate.get("credential_capability") == READONLY_PROVEN,
                    f"STOP_AUTO_READONLY_CREDENTIAL_NOT_PROVEN_{gate_id}",
                )
                _require(
                    gate.get("human_authorization") == T1_HUMAN_AUTHORIZATION,
                    f"STOP_AUTO_T1_HUMAN_AUTHORIZATION_MISSING_{gate_id}",
                )
                trust = gate.get("trust_boundary_observation")
                _require(isinstance(trust, dict), f"STOP_AUTO_T1_TRUST_BOUNDARY_MISSING_{gate_id}")
                _require(trust.get("repository_visibility") == "public", f"STOP_AUTO_T1_REPOSITORY_NOT_PUBLIC_{gate_id}")
                _require(trust.get("main_protected") is True, f"STOP_AUTO_T1_MAIN_NOT_PROTECTED_{gate_id}")
                _require(trust.get("ruleset_enforcement") == "active", f"STOP_AUTO_T1_RULESET_NOT_ACTIVE_{gate_id}")

    return {
        "status": "PASS_AUTOMATION_POLICY_STRUCTURE",
        "gate_count": len(gates),
        "auto_gate_count": sum(1 for row in gates.values() if row["auto_allowed"]),
        "default_decision": policy["default_decision"],
    }


def evaluate_gate(policy: dict[str, Any], gate_id: str) -> dict[str, Any]:
    validate_policy(policy)
    gate = _gate_map(policy).get(gate_id)
    if gate is None:
        return {
            "gate_id": gate_id,
            "decision": "BLOCK",
            "reason": "UNKNOWN_GATE_DEFAULT_DENY",
        }

    tier = gate["tier"]
    if not gate["auto_allowed"]:
        return {
            "gate_id": gate_id,
            "tier": tier,
            "decision": "BLOCK",
            "reason": "POLICY_AUTO_ALLOWED_FALSE",
            "blockers": list(gate.get("blockers") or []),
        }

    if tier == "T0_OFFLINE":
        return {
            "gate_id": gate_id,
            "tier": tier,
            "decision": "AUTO_ALLOWED",
            "reason": "OFFLINE_DETERMINISTIC_NO_REMOTE_EFFECTS",
        }

    if tier == "T1_REMOTE_READONLY" and gate.get("credential_capability") == READONLY_PROVEN:
        return {
            "gate_id": gate_id,
            "tier": tier,
            "decision": "AUTO_ALLOWED",
            "reason": "READONLY_CAPABILITY_PROVEN_AND_POLICY_ENABLED",
        }

    return {
        "gate_id": gate_id,
        "tier": tier,
        "decision": "BLOCK",
        "reason": "FAIL_CLOSED_UNHANDLED_POLICY_STATE",
    }
