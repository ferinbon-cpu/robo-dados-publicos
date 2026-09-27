from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
from typing import Any


ENTITY_TYPES = (
    "POLICY",
    "DOCUMENT",
    "PLAN",
    "PROGRAM",
    "ACTION",
    "BUDGET_EVENT",
    "EXPENSE",
    "CONTRACT",
    "PROVIDER",
    "DELIVERY",
    "ORGANIZATION",
    "TERRITORY",
    "INDICATOR",
)

RELATION_TYPES = (
    "MENTIONS",
    "ESTABLISHES",
    "REGULATES",
    "PLANS",
    "CONTAINS",
    "RESPONSIBLE_FOR",
    "AUTHORIZES",
    "ADJUSTS",
    "EXECUTES",
    "FINANCES",
    "PROVIDES",
    "DELIVERS_TO",
    "MEASURES",
    "CONTEXTUALIZES",
    "SUPPORTS",
    "CONTRADICTS",
    "DERIVED_FROM",
    "SUCCESSOR_OF",
    "OVERLAPS_WITH",
    "SAME_IDENTITY_AS",
)

ASSERTION_STATUSES = (
    "PROVEN",
    "CORROBORATED",
    "CANDIDATE",
    "UNKNOWN",
    "CONFLICTED",
    "REFUTED",
)

ID_PREFIXES = {
    "POLICY": "POLICY",
    "DOCUMENT": "DOC",
    "PLAN": "PLAN",
    "PROGRAM": "PROGRAM",
    "ACTION": "ACTION",
    "BUDGET_EVENT": "BUDGET_EVENT",
    "EXPENSE": "EXPENSE",
    "CONTRACT": "CONTRACT",
    "PROVIDER": "PROVIDER",
    "DELIVERY": "DELIVERY",
    "ORGANIZATION": "ORG",
    "TERRITORY": "TERRITORY",
    "INDICATOR": "INDICATOR",
}

LEGACY_FINANCIAL_IDENTITY = {
    "A": "PROVEN",
    "B": "CORROBORATED",
    "C": "CANDIDATE",
    "D": "UNKNOWN",
}

_ID_RE = re.compile(r"^[A-Z_]+:[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ResearchOntologyStop(RuntimeError):
    """Fail-closed structural validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ResearchOntologyStop(code)


def _validate_id(value: object, *, prefix: str, code: str) -> str:
    text = str(value or "")
    _require(bool(_ID_RE.fullmatch(text)), code)
    _require(text.startswith(prefix + ":"), code)
    return text


def _validate_date(value: object, *, code: str) -> str | None:
    if value is None:
        return None
    text = str(value)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise ResearchOntologyStop(code) from exc
    return text


def _validate_sha256(value: object, *, code: str, optional: bool = True) -> str | None:
    if value is None and optional:
        return None
    text = str(value or "")
    _require(bool(_SHA256_RE.fullmatch(text)), code)
    return text


def _validate_string_list(value: object, *, code: str, allow_empty: bool = True) -> list[str]:
    _require(isinstance(value, list), code)
    values = [str(item) for item in value]
    _require(all(item.strip() != "" for item in values), code)
    _require(len(values) == len(set(values)), code)
    if not allow_empty:
        _require(bool(values), code)
    return values


def validate_entity(record: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK093_ENTITY_OBJECT")
    entity_type = str(record.get("type") or "")
    _require(entity_type in ENTITY_TYPES, "TASK093_ENTITY_TYPE")
    entity_id = _validate_id(
        record.get("id"),
        prefix=ID_PREFIXES[entity_type],
        code="TASK093_ENTITY_ID",
    )
    label = str(record.get("label") or "").strip()
    _require(label != "", "TASK093_ENTITY_LABEL")

    aliases = _validate_string_list(
        record.get("aliases", []),
        code="TASK093_ENTITY_ALIASES",
    )
    valid_from = _validate_date(record.get("valid_from"), code="TASK093_ENTITY_VALID_FROM")
    valid_to = _validate_date(record.get("valid_to"), code="TASK093_ENTITY_VALID_TO")
    if valid_from is not None and valid_to is not None:
        _require(valid_from <= valid_to, "TASK093_ENTITY_TEMPORAL_ORDER")

    attributes = record.get("attributes", {})
    _require(isinstance(attributes, dict), "TASK093_ENTITY_ATTRIBUTES")

    return {
        "id": entity_id,
        "type": entity_type,
        "label": label,
        "aliases": aliases,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "attributes": deepcopy(attributes),
    }


def validate_evidence(record: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK093_EVIDENCE_OBJECT")
    evidence_id = _validate_id(
        record.get("evidence_id"),
        prefix="EVIDENCE",
        code="TASK093_EVIDENCE_ID",
    )
    source_entity_id = _validate_id(
        record.get("source_entity_id"),
        prefix="DOC",
        code="TASK093_EVIDENCE_SOURCE_ID",
    )
    locator = record.get("locator")
    _require(isinstance(locator, dict) and locator, "TASK093_EVIDENCE_LOCATOR")
    content_sha256 = _validate_sha256(
        record.get("content_sha256"),
        code="TASK093_EVIDENCE_CONTENT_SHA256",
        optional=True,
    )
    note = str(record.get("note") or "")
    return {
        "evidence_id": evidence_id,
        "source_entity_id": source_entity_id,
        "locator": deepcopy(locator),
        "content_sha256": content_sha256,
        "note": note,
    }


def _validate_assertion_status(record: dict[str, Any], *, prefix: str) -> tuple[str, list[str]]:
    status = str(record.get("status") or "")
    _require(status in ASSERTION_STATUSES, f"{prefix}_STATUS")
    evidence_ids = _validate_string_list(
        record.get("evidence_ids", []),
        code=f"{prefix}_EVIDENCE_IDS",
    )
    for evidence_id in evidence_ids:
        _validate_id(
            evidence_id,
            prefix="EVIDENCE",
            code=f"{prefix}_EVIDENCE_ID_FORMAT",
        )
    if status in {"PROVEN", "CORROBORATED"}:
        _require(bool(evidence_ids), f"{prefix}_EVIDENCE_REQUIRED")
    return status, evidence_ids


def validate_relation(record: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK093_RELATION_OBJECT")
    relation_id = _validate_id(
        record.get("relation_id"),
        prefix="REL",
        code="TASK093_RELATION_ID",
    )
    source_id = str(record.get("source_id") or "")
    target_id = str(record.get("target_id") or "")
    _require(bool(_ID_RE.fullmatch(source_id)), "TASK093_RELATION_SOURCE_ID")
    _require(bool(_ID_RE.fullmatch(target_id)), "TASK093_RELATION_TARGET_ID")
    _require(source_id != target_id, "TASK093_RELATION_SELF_LOOP")

    relation_type = str(record.get("relation_type") or "")
    _require(relation_type in RELATION_TYPES, "TASK093_RELATION_TYPE")
    status, evidence_ids = _validate_assertion_status(record, prefix="TASK093_RELATION")

    valid_from = _validate_date(record.get("valid_from"), code="TASK093_RELATION_VALID_FROM")
    valid_to = _validate_date(record.get("valid_to"), code="TASK093_RELATION_VALID_TO")
    if valid_from is not None and valid_to is not None:
        _require(valid_from <= valid_to, "TASK093_RELATION_TEMPORAL_ORDER")

    attributes = record.get("attributes", {})
    _require(isinstance(attributes, dict), "TASK093_RELATION_ATTRIBUTES")

    return {
        "relation_id": relation_id,
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "status": status,
        "evidence_ids": evidence_ids,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "attributes": deepcopy(attributes),
    }


def validate_claim(record: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK093_CLAIM_OBJECT")
    claim_id = _validate_id(
        record.get("claim_id"),
        prefix="CLAIM",
        code="TASK093_CLAIM_ID",
    )
    text = str(record.get("text") or "").strip()
    _require(text != "", "TASK093_CLAIM_TEXT")
    subject_ids = _validate_string_list(
        record.get("subject_ids", []),
        code="TASK093_CLAIM_SUBJECT_IDS",
        allow_empty=False,
    )
    _require(all(_ID_RE.fullmatch(item) for item in subject_ids), "TASK093_CLAIM_SUBJECT_ID_FORMAT")

    status, evidence_ids = _validate_assertion_status(record, prefix="TASK093_CLAIM")
    supporting = _validate_string_list(
        record.get("supporting_evidence_ids", []),
        code="TASK093_CLAIM_SUPPORTING_EVIDENCE",
    )
    contradicting = _validate_string_list(
        record.get("contradicting_evidence_ids", []),
        code="TASK093_CLAIM_CONTRADICTING_EVIDENCE",
    )
    for item in supporting + contradicting:
        _validate_id(item, prefix="EVIDENCE", code="TASK093_CLAIM_TYPED_EVIDENCE_ID")

    _require(set(supporting).issubset(evidence_ids), "TASK093_CLAIM_SUPPORT_NOT_IN_EVIDENCE")
    _require(set(contradicting).issubset(evidence_ids), "TASK093_CLAIM_CONTRADICTION_NOT_IN_EVIDENCE")

    if status == "CONFLICTED":
        _require(bool(supporting), "TASK093_CONFLICTED_SUPPORT_REQUIRED")
        _require(bool(contradicting), "TASK093_CONFLICTED_CONTRADICTION_REQUIRED")
    if status == "REFUTED":
        _require(bool(contradicting), "TASK093_REFUTED_CONTRADICTION_REQUIRED")
    if status == "PROVEN":
        _require(not contradicting, "TASK093_PROVEN_CANNOT_HAVE_CONTRADICTING_EVIDENCE")

    attributes = record.get("attributes", {})
    _require(isinstance(attributes, dict), "TASK093_CLAIM_ATTRIBUTES")
    return {
        "claim_id": claim_id,
        "text": text,
        "subject_ids": subject_ids,
        "status": status,
        "evidence_ids": evidence_ids,
        "supporting_evidence_ids": supporting,
        "contradicting_evidence_ids": contradicting,
        "attributes": deepcopy(attributes),
    }


def validate_research_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(bundle, dict), "TASK093_BUNDLE_OBJECT")
    _require(bundle.get("schema") == "RESEARCH_BUNDLE_V1", "TASK093_BUNDLE_SCHEMA")

    raw_entities = bundle.get("entities")
    raw_relations = bundle.get("relations")
    raw_claims = bundle.get("claims")
    raw_evidence = bundle.get("evidence")
    for value, code in (
        (raw_entities, "TASK093_BUNDLE_ENTITIES"),
        (raw_relations, "TASK093_BUNDLE_RELATIONS"),
        (raw_claims, "TASK093_BUNDLE_CLAIMS"),
        (raw_evidence, "TASK093_BUNDLE_EVIDENCE"),
    ):
        _require(isinstance(value, list), code)

    entities = [validate_entity(item) for item in raw_entities]
    relations = [validate_relation(item) for item in raw_relations]
    claims = [validate_claim(item) for item in raw_claims]
    evidence = [validate_evidence(item) for item in raw_evidence]

    entity_map = {item["id"]: item for item in entities}
    _require(len(entity_map) == len(entities), "TASK093_DUPLICATE_ENTITY_ID")
    relation_ids = [item["relation_id"] for item in relations]
    claim_ids = [item["claim_id"] for item in claims]
    evidence_ids = [item["evidence_id"] for item in evidence]
    _require(len(relation_ids) == len(set(relation_ids)), "TASK093_DUPLICATE_RELATION_ID")
    _require(len(claim_ids) == len(set(claim_ids)), "TASK093_DUPLICATE_CLAIM_ID")
    _require(len(evidence_ids) == len(set(evidence_ids)), "TASK093_DUPLICATE_EVIDENCE_ID")

    evidence_set = set(evidence_ids)
    for item in evidence:
        source = entity_map.get(item["source_entity_id"])
        _require(source is not None, "TASK093_EVIDENCE_SOURCE_MISSING")
        _require(source["type"] == "DOCUMENT", "TASK093_EVIDENCE_SOURCE_NOT_DOCUMENT")

    for relation in relations:
        _require(relation["source_id"] in entity_map, "TASK093_RELATION_SOURCE_MISSING")
        _require(relation["target_id"] in entity_map, "TASK093_RELATION_TARGET_MISSING")
        _require(set(relation["evidence_ids"]).issubset(evidence_set), "TASK093_RELATION_EVIDENCE_MISSING")

    for claim in claims:
        _require(set(claim["subject_ids"]).issubset(entity_map), "TASK093_CLAIM_SUBJECT_MISSING")
        _require(set(claim["evidence_ids"]).issubset(evidence_set), "TASK093_CLAIM_EVIDENCE_MISSING")

    return {
        "schema": "RESEARCH_BUNDLE_V1",
        "entities": entities,
        "relations": relations,
        "claims": claims,
        "evidence": evidence,
    }


def legacy_financial_identity_to_status(identity_class: str) -> str:
    try:
        return LEGACY_FINANCIAL_IDENTITY[str(identity_class).upper()]
    except KeyError as exc:
        raise ResearchOntologyStop("TASK093_UNKNOWN_LEGACY_FINANCIAL_IDENTITY") from exc


def load_ontology_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(data.get("schema") == "RESEARCH_ONTOLOGY_V1", "TASK093_CONTRACT_SCHEMA")
    _require(tuple(data.get("entity_types") or ()) == ENTITY_TYPES, "TASK093_CONTRACT_ENTITY_TYPES")
    _require(tuple(data.get("relation_types") or ()) == RELATION_TYPES, "TASK093_CONTRACT_RELATION_TYPES")
    _require(tuple(data.get("assertion_statuses") or ()) == ASSERTION_STATUSES, "TASK093_CONTRACT_STATUSES")
    _require(data.get("id_prefixes") == ID_PREFIXES, "TASK093_CONTRACT_PREFIXES")
    legacy = data.get("legacy_compatibility") or {}
    _require(
        legacy.get("financial_identity_classes") == LEGACY_FINANCIAL_IDENTITY,
        "TASK093_CONTRACT_LEGACY_IDENTITY",
    )
    remote = data.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK093_CONTRACT_REMOTE_EFFECT")
    return data
