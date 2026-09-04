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
    ascii_like = "".join(ch for ch in normalized if not unicodedata.combining(ch)).upper()
    return re.sub(r"[^A-Z0-9]+", " ", ascii_like).strip()


def validate_controller_contract(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("mode") != "T0_OFFLINE_ROUTING_CONTROLLER":
        raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_BAD_MODE")
    for key in ("content_read_authorized", "drive_write_authorized", "bronze_write_authorized", "silver_write_authorized", "gold_write_authorized", "serving_authorized", "publication_authorized"):
        if raw.get(key) is not False:
            raise DriveIngestionStop(f"STOP_DRIVE_CONTROLLER_REMOTE_EFFECT_ENABLED:{key}")
    if raw.get("allowed_input_surface") != "DRIVE_METADATA_ONLY":
        raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_NON_METADATA_INPUT")
    families = raw.get("known_document_families")
    if not isinstance(families, dict) or not families:
        raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_NO_DOCUMENT_FAMILIES")
    match_order = raw.get("family_match_order")
    if match_order is not None:
        if not isinstance(match_order, list) or len(match_order) != len(set(match_order)):
            raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_BAD_MATCH_ORDER")
        if set(match_order) != set(families):
            raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_MATCH_ORDER_FAMILY_DRIFT")
    default_routes = raw.get("family_default_routes")
    if default_routes is not None:
        if set(default_routes) != set(families):
            raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_DEFAULT_ROUTE_FAMILY_DRIFT")
        if {r for r in default_routes.values() if r not in {"AUTO_INGEST", "REVIEW", "QUARANTINE"}}:
            raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_BAD_DEFAULT_ROUTE")
    for rule in raw.get("primary_family_rules", []):
        if rule.get("primary_family") not in families or not _fold(str(rule.get("title_prefix") or "")):
            raise DriveIngestionStop("STOP_DRIVE_CONTROLLER_BAD_PRIMARY_FAMILY_RULE")
    return raw


def load_controller_contract(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_controller_contract(raw)


def _family_matches(title: str, contract: dict[str, Any]) -> list[str]:
    folded = _fold(title)
    families = contract["known_document_families"]
    order = contract.get("family_match_order") or list(families)
    return [family for family in order if any(re.search(r"(^|[^A-Z0-9])" + re.escape(_fold(term)) + r"([^A-Z0-9]|$)", folded) for term in families[family])]


def _declared_primary_family(title: str, matches: list[str], contract: dict[str, Any]) -> str | None:
    folded = _fold(title)
    for rule in contract.get("primary_family_rules", []):
        prefix = _fold(str(rule.get("title_prefix") or ""))
        primary = str(rule.get("primary_family") or "")
        if prefix and folded.startswith(prefix) and primary in matches:
            return primary
    return None


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
    matches = _family_matches(title, contract)
    if not matches:
        return RoutingDecision(file_id, title, None, "QUARANTINE", ("UNRECOGNIZED_FAMILY",))
    primary = _declared_primary_family(title, matches, contract) if len(matches) > 1 else None
    if len(matches) > 1 and primary is None:
        return RoutingDecision(file_id, title, None, "REVIEW", ("MULTIPLE_FAMILY_MATCHES",))
    family = primary or matches[0]
    if not file_id:
        return RoutingDecision(None, title, family, "REVIEW", ("MISSING_STABLE_FILE_ID",))
    if mime and mime not in set(contract["supported_mime_types"]):
        return RoutingDecision(file_id, title, family, "REVIEW", ("KNOWN_FAMILY_UNSUPPORTED_MIME",))
    default_route = contract.get("family_default_routes", {}).get(family, "AUTO_INGEST")
    role_reason = ("PRIMARY_FAMILY_RULE_APPLIED",) if primary else ()
    if default_route == "REVIEW":
        return RoutingDecision(file_id, title, family, "REVIEW", role_reason + ("KNOWN_FAMILY_METADATA_MATCH", "KNOWN_FAMILY_REQUIRES_SUPERVISED_REVIEW"))
    if default_route == "QUARANTINE":
        return RoutingDecision(file_id, title, family, "QUARANTINE", role_reason + ("KNOWN_FAMILY_POLICY_QUARANTINE",))
    return RoutingDecision(file_id, title, family, "AUTO_INGEST", role_reason + ("KNOWN_FAMILY_METADATA_MATCH", "EXECUTION_AUTH_REQUIRED"))


def route_inventory(records: list[dict[str, Any]], contract: dict[str, Any]) -> list[RoutingDecision]:
    seen_ids: set[str] = set(); seen_titles: set[str] = set(); out: list[RoutingDecision] = []
    for record in records:
        decision = classify_metadata(record, contract); folded_title = _fold(decision.title)
        if decision.file_id and decision.file_id in seen_ids:
            out.append(RoutingDecision(decision.file_id, decision.title, decision.family, "REVIEW", ("DUPLICATE_METADATA_FILE_ID",)))
        elif folded_title and folded_title in seen_titles and decision.route == "AUTO_INGEST":
            out.append(RoutingDecision(decision.file_id, decision.title, decision.family, "REVIEW", ("POSSIBLE_DUPLICATE_WITHOUT_HASH",)))
        else: out.append(decision)
        if decision.file_id: seen_ids.add(decision.file_id)
        if folded_title: seen_titles.add(folded_title)
    return out


def summarize_routes(decisions: list[RoutingDecision]) -> dict[str, int]:
    summary = {"AUTO_INGEST": 0, "REVIEW": 0, "QUARANTINE": 0}
    for item in decisions: summary[item.route] += 1
    return summary
