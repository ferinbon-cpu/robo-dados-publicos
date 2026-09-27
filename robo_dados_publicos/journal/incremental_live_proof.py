"""Pure offline trust boundary for a future bounded Jornal live proof.

This module deliberately has no transport, storage, or workflow integration.
"""
from __future__ import annotations

from typing import Iterable

from .incremental_readiness import plan_incremental_readiness


def evaluate_live_proof_design(
    *,
    checkpoint_status: str,
    checkpoint_items: Iterable[dict],
    checkpoint_real_snapshot_pinned: bool,
    discovery_status: str,
    discovered_items: Iterable[dict],
    max_new_items: int = 8,
) -> dict:
    """Classify fixture inputs while refusing an unpinned operational checkpoint."""
    if not checkpoint_real_snapshot_pinned:
        return _blocked("STOP_REAL_CHECKPOINT_NOT_PINNED")
    decision = plan_incremental_readiness(
        checkpoint_status=checkpoint_status,
        checkpoint_items=checkpoint_items,
        discovery_status=discovery_status,
        discovered_items=discovered_items,
        max_new_items=max_new_items,
    )
    return _boundary_result(decision)


def request_live_proof_execution(*, authorization: dict | None) -> dict:
    """Fail closed until a later task supplies a distinct SHA-pinned authorization."""
    if not authorization:
        return _blocked("STOP_LIVE_PROOF_NOT_AUTHORIZED")
    if authorization.get("task_018_authorization_reused") is True:
        return _blocked("STOP_TASK_018_AUTHORIZATION_REUSE")
    if not authorization.get("owner_authorized") or not authorization.get("implementation_sha"):
        return _blocked("STOP_LIVE_PROOF_NOT_AUTHORIZED")
    # TASK 021 is design-only: even a shaped authorization cannot activate it.
    return _blocked("STOP_TASK_021_DESIGN_ONLY")


def request_downstream_execution(*, planner_status: str) -> dict:
    """Never turn a planner proposal into collection or persistence."""
    return _blocked(
        "STOP_DOWNSTREAM_EXECUTION_NOT_AUTHORIZED",
        planner_status=planner_status,
    )


def _boundary_result(decision: dict) -> dict:
    result = dict(decision)
    result.update(
        {
            "boundary_outcome": (
                "NEW_ITEMS_DETECTED_EXECUTION_NOT_AUTHORIZED"
                if decision["status"] == "NEW_ITEMS_APPEND_ONLY"
                else decision["status"]
            ),
            "remote_effects": 0,
            "downstream_execution": False,
            "collection_authorized": False,
            "persistence_authorized": False,
            "checkpoint_advance_authorized": False,
        }
    )
    return result


def _blocked(status: str, **extra: object) -> dict:
    result = {
        "status": status,
        "remote_effects": 0,
        "downstream_execution": False,
        "collection_authorized": False,
        "persistence_authorized": False,
        "checkpoint_advance_authorized": False,
    }
    result.update(extra)
    return result
