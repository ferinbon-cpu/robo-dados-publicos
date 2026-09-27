from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any


@dataclass(frozen=True)
class ReviewItem:
    file_id: str | None
    title: str
    family: str | None
    reason: str
    priority: int
    action: str
    state: str = "OPEN"


def load_review_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("ordering") != "ASCENDING_PRIORITY_THEN_TITLE_THEN_FILE_ID":
        raise ValueError("STOP_BAD_REVIEW_ORDERING")
    return data


def build_review_item(decision: dict[str, Any], contract: dict[str, Any]) -> ReviewItem:
    reasons = list(decision.get("reasons") or [])
    known = contract["reason_actions"]
    ranked = [(known[r]["priority"], r) for r in reasons if r in known]
    if not ranked:
        reason = "MATURITY_NOT_EXECUTION_READY"
    else:
        _, reason = min(ranked)
    rule = known[reason]
    return ReviewItem(
        decision.get("file_id"),
        str(decision.get("title") or ""),
        decision.get("family"),
        reason,
        int(rule["priority"]),
        str(rule["action"]),
    )


def order_review_queue(items: list[ReviewItem]) -> list[ReviewItem]:
    return sorted(items, key=lambda x: (x.priority, x.title.casefold(), x.file_id or ""))


def can_resolve_to_auto(*, family_known: bool, maturity_ready: bool, rule_version: str | None, provenance_recorded: bool) -> bool:
    return bool(family_known and maturity_ready and rule_version and provenance_recorded)
