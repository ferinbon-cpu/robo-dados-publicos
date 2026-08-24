from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ReconciliationExecutionGate:
    version: int
    gate: str
    allowed_targets: tuple[str, ...]
    limit: int
    required_selected: int
    initial_status: str
    selection_policy: str
    allowed_result_statuses: tuple[str, ...]
    financial_identity_auto_promotion: str


def load_reconciliation_execution_gate(path: str | Path) -> ReconciliationExecutionGate:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "version", "gate", "allowed_targets", "limit", "required_selected",
        "initial_status", "selection_policy", "allowed_result_statuses",
        "financial_identity_auto_promotion",
    }
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError("RECONCILIATION_GATE_FIELDS_MISSING: " + ",".join(missing))
    gate = ReconciliationExecutionGate(
        version=int(payload["version"]),
        gate=str(payload["gate"]),
        allowed_targets=tuple(str(x) for x in payload["allowed_targets"]),
        limit=int(payload["limit"]),
        required_selected=int(payload["required_selected"]),
        initial_status=str(payload["initial_status"]),
        selection_policy=str(payload["selection_policy"]),
        allowed_result_statuses=tuple(str(x) for x in payload["allowed_result_statuses"]),
        financial_identity_auto_promotion=str(payload["financial_identity_auto_promotion"]),
    )
    if gate.version != 1 or gate.gate != "M4E_FIRST_RECONCILIATION_EXECUTION_GATE":
        raise ValueError("RECONCILIATION_GATE_IDENTITY_INVALID")
    if gate.allowed_targets != ("LIMEIRA_CONTRATOS",):
        raise ValueError("RECONCILIATION_GATE_TARGET_SCOPE_INVALID")
    if gate.limit != 1 or gate.required_selected != 1:
        raise ValueError("RECONCILIATION_GATE_LIMIT_INVALID")
    if gate.initial_status != "READY_SEARCH":
        raise ValueError("RECONCILIATION_GATE_INITIAL_STATUS_INVALID")
    if gate.selection_policy != "ELIGIBLE_PRIORITY_DESC_TASK_ID_ASC":
        raise ValueError("RECONCILIATION_GATE_SELECTION_POLICY_INVALID")
    if set(gate.allowed_result_statuses) != {"MATCH_CANDIDATE", "NO_MATCH"}:
        raise ValueError("RECONCILIATION_GATE_RESULT_SCOPE_INVALID")
    if gate.financial_identity_auto_promotion != "PROHIBITED":
        raise ValueError("RECONCILIATION_GATE_IDENTITY_POLICY_INVALID")
    return gate
