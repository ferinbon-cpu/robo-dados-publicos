"""Fail-closed T0 implementation boundary for a future bounded Jornal proof."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from .incremental_readiness import plan_incremental_readiness
from .real_checkpoint import validate_real_checkpoint

EXPECTED_INTEGRITY = "64e78c27a2c233468d76bc94c5719a35ed68ff7455cfac36d958d922c4ece5db"
ALLOWED_DOCUMENT_HOSTS = frozenset({"ecrie.com.br"})


class DiscoveryTransport(Protocol):
    """Injected discovery only; implementations must declare network capability."""

    network_capable: bool

    def discover(self) -> dict: ...


def stop(code: str, **details: object) -> dict:
    return {
        "status": code,
        "remote_effects": 0,
        "downstream_authorized": False,
        "checkpoint_advance_authorized": False,
        "checkpoint_unchanged": True,
        **details,
    }


def load_pinned_checkpoint(path: Path) -> tuple[dict | None, dict]:
    """Load and validate the only operational baseline, without any fallback."""
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, stop("STOP_CHECKPOINT_MISSING")
    except (OSError, json.JSONDecodeError):
        return None, stop("STOP_CHECKPOINT_MALFORMED")
    validation = validate_real_checkpoint(snapshot)
    if validation["status"] != "PASS_REAL_CHECKPOINT_PINNED":
        return None, stop(validation["status"])
    if validation.get("canonical_payload_sha256") != EXPECTED_INTEGRITY:
        return None, stop("STOP_CHECKPOINT_INTEGRITY_NOT_CANONICAL")
    return snapshot, validation


def _validate_discovery_items(items: object) -> str | None:
    if not isinstance(items, list):
        return "STOP_BAD_ITEM_CONTRACT"
    editions: set[int] = set()
    source_ids: set[str] = set()
    logical_keys: set[str] = set()
    for raw in items:
        if not isinstance(raw, dict):
            return "STOP_BAD_ITEM_CONTRACT"
        edition = raw.get("edition")
        source_id = raw.get("source_id")
        logical_key = raw.get("logical_key")
        url = raw.get("document_url")
        if isinstance(edition, bool) or not isinstance(edition, int) or edition <= 0:
            return "STOP_BAD_ITEM_CONTRACT"
        if edition in editions:
            return "STOP_DUPLICATE_EDITION"
        if source_id in source_ids:
            return "STOP_DUPLICATE_SOURCE_ID"
        if logical_key in logical_keys:
            return "STOP_DUPLICATE_LOGICAL_KEY"
        if source_id != f"LIMEIRA_JO_{edition:05d}":
            return "STOP_SOURCE_ID_EDITION_MISMATCH"
        if logical_key != f"limeira/jornal_oficial/edicao/{edition}":
            return "STOP_LOGICAL_KEY_EDITION_MISMATCH"
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme != "https":
            return "STOP_DOCUMENT_URL_NOT_HTTPS"
        if parsed.hostname not in ALLOWED_DOCUMENT_HOSTS:
            return "STOP_DOCUMENT_HOST_NOT_ALLOWED"
        editions.add(edition); source_ids.add(source_id); logical_keys.add(logical_key)
    return None


def evaluate_discovery(*, checkpoint: dict, discovery: dict, max_new_items: int = 8) -> dict:
    """Pure composition of TASK 022 validation and TASK 020 semantics."""
    validation = validate_real_checkpoint(checkpoint)
    if validation["status"] != "PASS_REAL_CHECKPOINT_PINNED":
        return stop(validation["status"])
    if validation.get("canonical_payload_sha256") != EXPECTED_INTEGRITY:
        return stop("STOP_CHECKPOINT_INTEGRITY_NOT_CANONICAL")
    if not isinstance(discovery, dict) or discovery.get("status") != "PASS_DISCOVERY":
        return stop("STOP_DISCOVERY_NOT_COMPLETE")
    if discovery.get("complete") is not True:
        return stop("STOP_DISCOVERY_INCOMPLETE")
    pages = discovery.get("pages_requested")
    requests = discovery.get("request_count")
    if isinstance(pages, bool) or not isinstance(pages, int) or not 1 <= pages <= 8:
        return stop("STOP_PAGINATION_BOUNDARY_EXCEEDED")
    if isinstance(requests, bool) or not isinstance(requests, int) or not 1 <= requests <= 8:
        return stop("STOP_REQUEST_BUDGET_EXCEEDED")
    if discovery.get("automatic_retry") is not False:
        return stop("STOP_AUTOMATIC_RETRY_PROHIBITED")
    error = _validate_discovery_items(discovery.get("items"))
    if error:
        return stop(error)
    decision = plan_incremental_readiness(
        checkpoint_status=checkpoint["checkpoint_status"],
        checkpoint_items=checkpoint["items"],
        discovery_status=discovery["status"],
        discovered_items=discovery["items"],
        max_new_items=max_new_items,
    )
    if decision["status"].startswith("STOP_"):
        return stop(decision["status"], reason=decision.get("reason"))
    outcome = (
        "PASS_LIVE_INCREMENTAL_NO_CHANGE_IDEMPOTENT"
        if decision["status"] == "NO_CHANGE_IDEMPOTENT"
        else "PASS_LIVE_INCREMENTAL_NEW_ITEMS_DETECTED_EXECUTION_NOT_AUTHORIZED"
    )
    return {
        **decision,
        "boundary_outcome": outcome,
        "remote_effects": 0,
        "downstream_authorized": False,
        "checkpoint_advance_authorized": False,
        "checkpoint_unchanged": True,
    }


def validate_live_authorization(authorization: dict | None, *, expected_sha: str) -> dict:
    """Validate a future authorization shape; test fixtures never authorize live I/O."""
    if not authorization:
        return stop("STOP_LIVE_PROOF_NOT_AUTHORIZED")
    if authorization.get("task") == "TASK_018" or authorization.get("task_018_authorization_reused") is True:
        return stop("STOP_TASK_018_AUTHORIZATION_REUSE")
    if authorization.get("synthetic_test_only") is True:
        return stop("STOP_SYNTHETIC_AUTHORIZATION_NOT_OPERATIONAL")
    required = {
        "task": "TASK_023_LIVE_PROOF_AUTHORIZATION",
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "branch": "main",
        "implementation_sha": expected_sha,
        "source": "LIMEIRA_JORNAL_OFICIAL",
        "operation": "BOUNDED_DISCOVERY_READ_ONLY",
        "max_requests": 8,
        "attempt_count": 1,
        "owner_authorized": True,
        "downstream_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        return stop("STOP_LIVE_AUTHORIZATION_CONTRACT_MISMATCH")
    return {"status": "PASS_LIVE_AUTHORIZATION", "max_requests": 8}


def run_proof(*, checkpoint: dict, transport: DiscoveryTransport, authorization: dict | None,
              expected_sha: str, offline_test_mode: bool = False) -> dict:
    """Invoke only an injected transport after authorization; fake-only in T0 tests."""
    checkpoint_result = validate_real_checkpoint(checkpoint)
    if checkpoint_result["status"] != "PASS_REAL_CHECKPOINT_PINNED":
        return stop(checkpoint_result["status"])
    if checkpoint_result.get("canonical_payload_sha256") != EXPECTED_INTEGRITY:
        return stop("STOP_CHECKPOINT_INTEGRITY_NOT_CANONICAL")
    if offline_test_mode:
        if getattr(transport, "network_capable", True) or not authorization or authorization.get("synthetic_test_only") is not True:
            return stop("STOP_OFFLINE_TEST_TRANSPORT_CONTRACT")
    else:
        auth_result = validate_live_authorization(authorization, expected_sha=expected_sha)
        if auth_result["status"] != "PASS_LIVE_AUTHORIZATION":
            return auth_result
    return evaluate_discovery(checkpoint=checkpoint, discovery=transport.discover())


def request_prohibited_effects(*, downstream: bool = False, checkpoint_advance: bool = False,
                               schedule: bool = False, recurrence: bool = False) -> dict:
    if downstream:
        return stop("STOP_DOWNSTREAM_EXECUTION_NOT_AUTHORIZED")
    if checkpoint_advance:
        return stop("STOP_CHECKPOINT_ADVANCE_NOT_AUTHORIZED")
    if schedule:
        return stop("STOP_SCHEDULE_NOT_AUTHORIZED")
    if recurrence:
        return stop("STOP_RECURRENCE_NOT_AUTHORIZED")
    return stop("STOP_NO_OPERATION_REQUESTED")
