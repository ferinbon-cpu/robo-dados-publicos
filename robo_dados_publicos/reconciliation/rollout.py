from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Iterable


class ReconciliationRolloutError(RuntimeError):
    """Raised when a persisted reconciliation plan cannot be selected safely."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ReconciliationRolloutError(code)


def _stable_key(row: dict) -> tuple:
    try:
        priority = int(row["priority"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ReconciliationRolloutError("STOP_ROLLOUT_INVALID_PRIORITY") from exc
    for key in ("origin_event_id", "target_source", "task_id"):
        _require(isinstance(row.get(key), str) and bool(row[key]), f"STOP_ROLLOUT_INVALID_{key.upper()}")
    return (-priority, row["origin_event_id"], row["target_source"], row["task_id"])


def _task_sha256(row: dict) -> str:
    material = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(material.encode("utf-8")).hexdigest()


def parse_pinned_plan(raw: bytes, *, expected_sha256: str) -> tuple[list[dict], str]:
    """Validate exact plan bytes and return rows only when the plan is canonical.

    This function performs no network or filesystem access. The caller must supply
    the exact bytes obtained by a separately authorized read.
    """

    _require(isinstance(raw, bytes), "STOP_ROLLOUT_PLAN_BYTES_REQUIRED")
    expected = str(expected_sha256 or "").lower()
    _require(bool(re.fullmatch(r"[0-9a-f]{64}", expected)), "STOP_ROLLOUT_EXPECTED_SHA256_INVALID")
    actual = sha256(raw).hexdigest()
    _require(actual == expected, "STOP_ROLLOUT_PLAN_SHA256_MISMATCH")

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ReconciliationRolloutError("STOP_ROLLOUT_PLAN_NOT_UTF8") from exc

    rows: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReconciliationRolloutError(f"STOP_ROLLOUT_INVALID_JSONL_LINE_{line_number}") from exc
        _require(isinstance(row, dict), f"STOP_ROLLOUT_NON_OBJECT_LINE_{line_number}")
        _stable_key(row)
        _require(isinstance(row.get("status"), str) and bool(row["status"]), "STOP_ROLLOUT_INVALID_STATUS")
        rows.append(row)

    _require(bool(rows), "STOP_ROLLOUT_EMPTY_PLAN")
    task_ids = [row["task_id"] for row in rows]
    _require(len(task_ids) == len(set(task_ids)), "STOP_ROLLOUT_DUPLICATE_TASK_ID")
    _require(rows == sorted(rows, key=_stable_key), "STOP_ROLLOUT_PLAN_NOT_CANONICAL_ORDER")
    return rows, actual


def select_next_ready_task(
    raw: bytes,
    *,
    expected_sha256: str,
    target_source: str,
    consumed_task_ids: Iterable[str] = (),
) -> dict:
    """Select exactly one remaining READY_SEARCH task from a pinned canonical plan."""

    target = str(target_source or "")
    _require(bool(target), "STOP_ROLLOUT_TARGET_SOURCE_REQUIRED")
    rows, actual_sha = parse_pinned_plan(raw, expected_sha256=expected_sha256)

    consumed = {str(value) for value in consumed_task_ids if str(value)}
    known_ids = {row["task_id"] for row in rows}
    missing_consumed = sorted(consumed - known_ids)
    _require(not missing_consumed, "STOP_ROLLOUT_CONSUMED_TASK_NOT_IN_PINNED_PLAN")

    eligible = [row for row in rows if row.get("status") == "READY_SEARCH" and row.get("target_source") == target]
    remaining = [row for row in eligible if row["task_id"] not in consumed]
    _require(bool(remaining), "STOP_ROLLOUT_NO_REMAINING_READY_TASK")

    selected = remaining[0]
    return {
        "status": "PASS_RECONCILIATION_NEXT_TASK_SELECTED",
        "plan_sha256": actual_sha,
        "plan_tasks": len(rows),
        "target_source": target,
        "eligible_ready_tasks": len(eligible),
        "consumed_task_ids": sorted(consumed),
        "remaining_ready_tasks": len(remaining),
        "selected_task_id": selected["task_id"],
        "selected_task_sha256": _task_sha256(selected),
        "selected_task": selected,
        "remote_effects": {
            "source_network": 0,
            "drive_reads": 0,
            "drive_writes": 0,
            "state_registry_writes": 0,
            "queue_writes": 0,
            "serving_writes": 0,
            "publications": 0,
        },
    }
