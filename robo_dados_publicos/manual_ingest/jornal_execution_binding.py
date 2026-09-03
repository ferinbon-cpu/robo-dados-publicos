from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JornalExecutionStop(ValueError):
    pass


def load_jornal_profile(path: str | Path) -> dict[str, Any]:
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    if profile.get("family") != "JORNAL_OFICIAL":
        raise JornalExecutionStop("STOP_JORNAL_BAD_FAMILY")
    if profile.get("recurrence_status") != "NOT_GLOBALLY_PROMOTED":
        raise JornalExecutionStop("STOP_JORNAL_RECURRENCE_OVERPROMOTED")
    if profile.get("schedule_authorized") is not False or profile.get("live_execution_authorized_by_task_069") is not False:
        raise JornalExecutionStop("STOP_JORNAL_LIVE_EFFECT_ENABLED")
    return profile


def evaluate_new_edition_candidate(candidate: dict[str, Any], profile: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    edition = candidate.get("edition")
    publication_date = str(candidate.get("publication_date") or "")
    checkpoint = profile["pinned_checkpoint"]
    highest = int(checkpoint["highest_edition"])
    frontier_date = str(checkpoint["frontier_publication_date"])

    if not isinstance(edition, int):
        reasons.append("MISSING_OR_INVALID_EDITION")
    elif edition <= highest:
        reasons.append("EDITION_NOT_GREATER_THAN_CHECKPOINT")
    if candidate.get("duplicate_edition") is True:
        reasons.append("DUPLICATE_EDITION")
    if not publication_date:
        reasons.append("MISSING_PUBLICATION_DATE")
    elif publication_date < frontier_date:
        reasons.append("PUBLICATION_DATE_OLDER_THAN_CHECKPOINT_FRONTIER")
    if candidate.get("family") != "JORNAL_OFICIAL":
        reasons.append("SOURCE_METADATA_NOT_JORNAL")
    if candidate.get("discovery_requests", 0) > profile["future_discovery_limits"]["max_requests"]:
        reasons.append("DISCOVERY_REQUEST_LIMIT_EXCEEDED")
    if candidate.get("discovery_pages", 0) > profile["future_discovery_limits"]["max_pages"]:
        reasons.append("DISCOVERY_PAGE_LIMIT_EXCEEDED")
    if candidate.get("authorization_enabled") is not True:
        reasons.append("SEPARATE_EXECUTION_AUTHORIZATION_MISSING")

    if reasons:
        return "STOP_TO_REVIEW", tuple(reasons)
    return "ELIGIBLE_FOR_BOUNDED_LIVE_JORNAL_GATE", ("ALL_BOUNDED_REQUIREMENTS_SATISFIED",)


def downstream_auto_promotion_allowed(profile: dict[str, Any]) -> bool:
    forbidden = set(profile.get("forbidden_effects", []))
    return not any(x in forbidden for x in ("SILVER_AUTO_PROMOTION", "GOLD_AUTO_PROMOTION", "PUBLICATION_AUTO"))
