from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


class IngestionExecutionStop(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionDecision:
    allowed: bool
    state: str
    reasons: tuple[str, ...]


def load_execution_policy(path: str | Path) -> dict[str, Any]:
    policy = json.loads(Path(path).read_text(encoding="utf-8"))
    if policy.get("mode") != "FAIL_CLOSED_EXECUTION_POLICY":
        raise IngestionExecutionStop("STOP_BAD_EXECUTION_POLICY_MODE")
    if "OVERWRITE_EXISTING_BRONZE" not in policy.get("forbidden_automatic_effects", []):
        raise IngestionExecutionStop("STOP_EXECUTION_POLICY_ALLOWS_BRONZE_OVERWRITE")
    return policy


def decide_execution(record: dict[str, Any], route: str, family: str | None, policy: dict[str, Any]) -> ExecutionDecision:
    reasons: list[str] = []
    if not record.get("folder_scope_authorized", False):
        reasons.append("FOLDER_SCOPE_NOT_AUTHORIZED")
    if route != "AUTO_INGEST":
        reasons.append("ROUTE_NOT_AUTO_INGEST")
    if not family:
        reasons.append("UNKNOWN_FAMILY")
    if not record.get("id"):
        reasons.append("MISSING_STABLE_FILE_ID")
    if record.get("content_hydrated") is True:
        reasons.append("CONTENT_HYDRATED_DURING_METADATA_PHASE")
    if record.get("unresolved_duplicate_signal") is True:
        reasons.append("UNRESOLVED_DUPLICATE_SIGNAL")
    if reasons:
        return ExecutionDecision(False, "BLOCKED", tuple(reasons))
    return ExecutionDecision(True, "ELIGIBLE_FOR_AUTHORIZED_CONTENT_HASH_BRONZE", ("ALL_EXECUTION_PREREQUISITES_SATISFIED",))


def promotion_after_ingest(*, schema_valid: bool, qa_valid: bool, reconciliation_valid: bool) -> str:
    if not schema_valid:
        return "STOP_BEFORE_SILVER_SCHEMA_DRIFT"
    if not qa_valid:
        return "SILVER_ONLY_QA_NOT_VALID"
    if not reconciliation_valid:
        return "SILVER_ONLY_RECONCILIATION_NOT_VALID"
    return "ELIGIBLE_FOR_SEPARATE_GOLD_GATE"
