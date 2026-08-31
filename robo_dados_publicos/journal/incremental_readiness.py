from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


IMMUTABLE_KNOWN_ITEM_FIELDS = (
    "edition",
    "publication_date",
    "document_url",
    "source_id",
    "logical_key",
)


@dataclass(frozen=True)
class IncrementalDecision:
    status: str
    new_items: tuple[dict, ...] = ()
    reason: str | None = None
    checkpoint_candidate: dict | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "new_items": [dict(item) for item in self.new_items],
            "new_item_count": len(self.new_items),
            "reason": self.reason,
            "checkpoint_candidate": self.checkpoint_candidate,
            "remote_effects_authorized": False,
            "checkpoint_mutation_performed": False,
        }


def _normalized_item(raw: dict) -> dict:
    item = dict(raw)
    try:
        edition = int(item["edition"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("BAD_EDITION") from exc
    if edition <= 0:
        raise ValueError("BAD_EDITION")

    publication_date = item.get("publication_date")
    if not isinstance(publication_date, str) or not publication_date:
        raise ValueError("BAD_PUBLICATION_DATE")
    try:
        date.fromisoformat(publication_date)
    except ValueError as exc:
        raise ValueError("BAD_PUBLICATION_DATE") from exc

    document_url = item.get("document_url")
    if not isinstance(document_url, str) or not document_url.startswith("https://"):
        raise ValueError("BAD_DOCUMENT_URL")

    expected_source_id = f"LIMEIRA_JO_{edition:05d}"
    expected_logical_key = f"limeira/jornal_oficial/edicao/{edition}"
    source_id = item.get("source_id", expected_source_id)
    logical_key = item.get("logical_key", expected_logical_key)
    if source_id != expected_source_id or logical_key != expected_logical_key:
        raise ValueError("BAD_CANONICAL_IDENTITY")

    return {
        "edition": edition,
        "publication_date": publication_date,
        "document_url": document_url,
        "source_id": source_id,
        "logical_key": logical_key,
    }


def _unique_items(items: Iterable[dict]) -> tuple[dict[int, dict], str | None]:
    out: dict[int, dict] = {}
    try:
        for raw in items:
            item = _normalized_item(raw)
            edition = item["edition"]
            if edition in out:
                return {}, "STOP_DUPLICATE_EDITION"
            out[edition] = item
    except (TypeError, ValueError):
        return {}, "STOP_BAD_ITEM_CONTRACT"
    return out, None


def plan_incremental_readiness(
    *,
    checkpoint_status: str,
    checkpoint_items: Iterable[dict],
    discovery_status: str,
    discovered_items: Iterable[dict],
    max_new_items: int = 8,
) -> dict:
    """Pure T0 planner for Jornal Oficial incremental readiness.

    The function never performs network, state mutation, persistence, publication,
    retry, cleanup, or scheduling. It only classifies a proposed discovery delta.
    """
    if checkpoint_status != "COMPLETE":
        return IncrementalDecision(
            "STOP_CHECKPOINT_NOT_COMPLETE",
            reason=f"checkpoint_status={checkpoint_status}",
        ).to_dict()
    if discovery_status != "PASS_DISCOVERY":
        return IncrementalDecision(
            "STOP_DISCOVERY_NOT_COMPLETE",
            reason=f"discovery_status={discovery_status}",
        ).to_dict()
    if not isinstance(max_new_items, int) or max_new_items < 1:
        return IncrementalDecision(
            "STOP_BAD_ITEM_CONTRACT",
            reason="max_new_items must be a positive integer",
        ).to_dict()

    checkpoint, checkpoint_error = _unique_items(checkpoint_items)
    if checkpoint_error:
        return IncrementalDecision(checkpoint_error, reason="checkpoint_items").to_dict()
    discovered, discovery_error = _unique_items(discovered_items)
    if discovery_error:
        return IncrementalDecision(discovery_error, reason="discovered_items").to_dict()
    if not checkpoint:
        return IncrementalDecision(
            "STOP_CHECKPOINT_NOT_COMPLETE",
            reason="completed checkpoint must contain at least one item",
        ).to_dict()

    missing = sorted(set(checkpoint) - set(discovered))
    if missing:
        return IncrementalDecision(
            "STOP_KNOWN_ITEM_MISSING",
            reason=f"missing_editions={missing}",
        ).to_dict()

    for edition, old in checkpoint.items():
        current = discovered[edition]
        if any(old[field] != current[field] for field in IMMUTABLE_KNOWN_ITEM_FIELDS):
            return IncrementalDecision(
                "STOP_KNOWN_ITEM_DRIFT",
                reason=f"edition={edition}",
            ).to_dict()

    new_editions = sorted(set(discovered) - set(checkpoint))
    if not new_editions:
        checkpoint_candidate = {
            "status": "COMPLETE",
            "known_editions": sorted(checkpoint),
            "advance_allowed": False,
            "advance_condition": "NO_CHANGE",
        }
        return IncrementalDecision(
            "NO_CHANGE_IDEMPOTENT",
            checkpoint_candidate=checkpoint_candidate,
        ).to_dict()

    checkpoint_max = max(checkpoint)
    non_monotonic = [edition for edition in new_editions if edition <= checkpoint_max]
    if non_monotonic:
        return IncrementalDecision(
            "STOP_NON_MONOTONIC_NEW_ITEM",
            reason=f"checkpoint_max={checkpoint_max};new_editions={non_monotonic}",
        ).to_dict()
    if len(new_editions) > max_new_items:
        return IncrementalDecision(
            "STOP_NEW_ITEM_BOUND_EXCEEDED",
            reason=f"new_item_count={len(new_editions)};max_new_items={max_new_items}",
        ).to_dict()

    new_items = tuple(discovered[edition] for edition in new_editions)
    checkpoint_candidate = {
        "status": "PROPOSED_ONLY",
        "known_editions": sorted(discovered),
        "previous_checkpoint_max": checkpoint_max,
        "candidate_checkpoint_max": max(new_editions),
        "advance_allowed": False,
        "advance_condition": "ONLY_AFTER_ALL_PROPOSED_NEW_ITEMS_COMPLETE_DOWNSTREAM_AND_FINAL_READBACK",
    }
    return IncrementalDecision(
        "NEW_ITEMS_APPEND_ONLY",
        new_items=new_items,
        checkpoint_candidate=checkpoint_candidate,
    ).to_dict()
