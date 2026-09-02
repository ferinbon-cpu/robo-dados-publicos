from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import unicodedata
from typing import Any


class DriveIngestionStop(ValueError):
    pass


@dataclass(frozen=True)
class RoutingDecision:
    file_id: str | None
    title: str
    family: str | None
    route: str
    reasons: tuple[str, ...]


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).upper()


def load_controller_contract(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("mode") != "T0_OFFLINE_ROUTING_CONTROLLER":
        raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_BAD_MODE")
    for key in ("content_read_authorized", "drive_write_authorized", "bronze_write_authorized", "silver_write_authorized", "gold_write_authorized", "serving_authorized", "publication_authorized"):
        if raw.get(key) is not False:
            raise DriveIngestionStop(f"STOP_DRIVE_CONTROLLER_REMOTE_EFFECT_ENABLED:{key}")
    if raw.get("allowed_input_surface") != "DRIVE_METADATA_ONLY":
        raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_NON_METADATA_INPUT")
    return raw


def classify_metadata(record: dict[str, Any], contract: dict[str, Any]) -> RoutingDecision:
    if record.get("content_hydrated") is True:
        return RoutingDecision(record.get("id"), str(record.get("title") or ""), None, "QUARANTINE", ("CONTENT_HYDRATED_DURING_METADATA_PHASE",))
    file_id = record.get("id")
    title = str(record.get("title") or "").strip()
    mime = str(record.get("mime_type") or "").strip()
    if not title:
        return RoutingDecision(file_id, title, None, "QUARANTINE", ("MALFORMED_METADATA",))
    if record.get("in_authorized_scope") is False:
        return RoutingDecision(file_id, title, None, "QUARANTINE", ("SOURCE_OUTSIDE_AUTHORIZED_FOLDER_SCOPE",))

    folded = _fold(title)
    matches: list[str] = []
    for family, terms in contract["known_document_families"].items():
        if any(re.search(r"(^|[^A-Z0-9])" + re.escape(_fold(term)) + r"([^A-Z0-9]|$)", folded) for term in terms):
            matches.append(family)

    if not matches:
        return RoutingDecision(file_id, title, None, "QUARANTINE", ("UNRECOGNIZED_FAMILY",))
    if len(matches) > 1:
        return RoutingDecision(file_id, title, None, "REVIEW", ("MULTIPLE_FAMILY_MATCHES",))
    family = matches[0]
    if not file_id:
        return RoutingDecision(None, title, family, "REVIEW", ("MISSING_STABLE_FILE_ID",))
    if mime and mime not in set(contract["supported_mime_types"]):
        return RoutingDecision(file_id, title, family, "REVIEW", ("KNOWN_FAMILY_UNSUPPORTED_MIME",))
    return RoutingDecision(file_id, title, family, "AUTO_INGEST", ("KNOWN_FAMILY_METADATA_MATCH", "EXECUTION_AUTH_REQUIRED",))


def route_inventory(records: list[dict[str, Any]], contract: dict[str, Any]) -> list[RoutingDecision]:
    seen: set[str] = set()
    out: list[RoutingDecision] = []
    for record in records:
        decision = classify_metadata(record, contract)
        if decision.file_id and decision.file_id in seen:
            out.append(RoutingDecision(decision.file_id, decision.title, decision.family, "REVIEW", ("DUPLICATE_METADATA_FILE_ID",)))
        else:
            out.append(decision)
            if decision.file_id:
                seen.add(decision.file_id)
    return out


def summarize_routes(decisions: list[RoutingDecision]) -> dict[str, int]:
    summary = {"AUTO_INGEST": 0, "REVIEW": 0, "QUARANTINE": 0}
    for item in decisions:
        summary[item.route] += 1
    return summary
