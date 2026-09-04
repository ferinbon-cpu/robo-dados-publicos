from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.research.ontology import (
    ASSERTION_STATUSES,
    validate_research_bundle,
)


QUERY_TYPES = (
    "CLAIM_AUDIT",
    "INSTITUTIONALIZATION_MATRIX",
    "EVIDENCE_GAPS",
    "POLICY_STATUS_PACKET",
)

DEFAULT_ALLOWED_CLAIM_STATUSES = (
    "PROVEN",
    "CORROBORATED",
    "CANDIDATE",
    "UNKNOWN",
    "CONFLICTED",
    "REFUTED",
)


class ResearchQueryStop(RuntimeError):
    """Fail-closed deterministic research-query validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ResearchQueryStop(code)


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def validate_query_spec(spec: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(spec, dict), "TASK099_QUERY_OBJECT")
    query_id = str(spec.get("query_id") or "").strip()
    _require(query_id != "", "TASK099_QUERY_ID")
    query_type = str(spec.get("query_type") or "")
    _require(query_type in QUERY_TYPES, "TASK099_QUERY_TYPE")
    subject_id = str(spec.get("subject_id") or "").strip()
    _require(subject_id != "", "TASK099_SUBJECT_ID")

    raw_statuses = spec.get("allowed_claim_statuses", list(DEFAULT_ALLOWED_CLAIM_STATUSES))
    _require(isinstance(raw_statuses, list) and raw_statuses, "TASK099_ALLOWED_STATUSES")
    statuses = [str(value) for value in raw_statuses]
    _require(len(statuses) == len(set(statuses)), "TASK099_DUPLICATE_STATUS")
    _require(all(value in ASSERTION_STATUSES for value in statuses), "TASK099_INVALID_STATUS")

    include_evidence = spec.get("include_evidence", True)
    include_unknown_gaps = spec.get("include_unknown_gaps", True)
    _require(isinstance(include_evidence, bool), "TASK099_INCLUDE_EVIDENCE")
    _require(isinstance(include_unknown_gaps, bool), "TASK099_INCLUDE_UNKNOWN_GAPS")

    return {
        "query_id": query_id,
        "query_type": query_type,
        "subject_id": subject_id,
        "allowed_claim_statuses": statuses,
        "include_evidence": include_evidence,
        "include_unknown_gaps": include_unknown_gaps,
    }


def _index_bundle(bundle: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validated = validate_research_bundle(bundle)
    entities = {item["id"]: item for item in validated["entities"]}
    evidence = {item["evidence_id"]: item for item in validated["evidence"]}
    return validated, {"entities": entities, "evidence": evidence}


def _claim_packet(
    claim: dict[str, Any],
    *,
    evidence_index: dict[str, Any],
    entity_index: dict[str, Any],
    include_evidence: bool,
) -> dict[str, Any]:
    packet = {
        "claim_id": claim["claim_id"],
        "text": claim["text"],
        "status": claim["status"],
        "subject_ids": list(claim["subject_ids"]),
        "attributes": deepcopy(claim.get("attributes") or {}),
        "evidence_ids": list(claim["evidence_ids"]),
        "supporting_evidence_ids": list(claim["supporting_evidence_ids"]),
        "contradicting_evidence_ids": list(claim["contradicting_evidence_ids"]),
    }
    if include_evidence:
        evidence_packets = []
        for evidence_id in claim["evidence_ids"]:
            evidence = evidence_index[evidence_id]
            source = entity_index[evidence["source_entity_id"]]
            evidence_packets.append(
                {
                    "evidence_id": evidence_id,
                    "source_document_id": evidence["source_entity_id"],
                    "source_document_label": source["label"],
                    "source_role": (source.get("attributes") or {}).get("source_role"),
                    "locator": deepcopy(evidence["locator"]),
                    "content_sha256": evidence.get("content_sha256"),
                    "note": evidence.get("note", ""),
                }
            )
        packet["evidence"] = evidence_packets
    return packet


def _claims_for_subject(
    bundle: dict[str, Any],
    *,
    subject_id: str,
    statuses: set[str],
    evidence_index: dict[str, Any],
    entity_index: dict[str, Any],
    include_evidence: bool,
) -> list[dict[str, Any]]:
    selected = []
    for claim in bundle["claims"]:
        if subject_id not in claim["subject_ids"]:
            continue
        if claim["status"] not in statuses:
            continue
        selected.append(
            _claim_packet(
                claim,
                evidence_index=evidence_index,
                entity_index=entity_index,
                include_evidence=include_evidence,
            )
        )
    return sorted(selected, key=lambda item: item["claim_id"])


def _matrix_packet(matrix: dict[str, Any], *, include_unknown_gaps: bool) -> dict[str, Any]:
    _require(isinstance(matrix, dict) and matrix, "TASK099_MATRIX_REQUIRED")
    dimensions = []
    gaps = []
    for name in sorted(matrix):
        raw = matrix[name]
        if isinstance(raw, dict):
            status = str(raw.get("status") or "")
            detail = deepcopy(raw)
        else:
            status = str(raw or "")
            detail = {"status": status}
        _require(status in ASSERTION_STATUSES, f"TASK099_MATRIX_STATUS_{name.upper()}")
        dimensions.append({"dimension": name, **detail})
        if status in {"UNKNOWN", "CANDIDATE", "CONFLICTED"}:
            gaps.append({"dimension": name, "status": status, "detail": detail})
    return {
        "dimensions": dimensions,
        "gaps": gaps if include_unknown_gaps else [],
    }


def _historical_packets(
    historical_planning: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if historical_planning is None:
        return [], []
    _require(
        historical_planning.get("schema") == "EITI_HISTORICAL_PLANNING_CROSSWALK_V1",
        "TASK099_HISTORICAL_SCHEMA",
    )
    gaps = historical_planning.get("acquisition_gaps")
    negative = historical_planning.get("bounded_negative_evidence")
    _require(isinstance(gaps, list), "TASK099_HISTORICAL_GAPS")
    _require(isinstance(negative, list), "TASK115_HISTORICAL_NEGATIVE_EVIDENCE")
    for item in negative:
        _require(isinstance(item, dict), "TASK115_HISTORICAL_NEGATIVE_ITEM")
        _require(bool(str(item.get("period") or "").strip()), "TASK115_HISTORICAL_NEGATIVE_PERIOD")
        _require(item.get("status") == "BOUNDED_NO_CANDIDATES", "TASK115_HISTORICAL_NEGATIVE_STATUS")
        _require(type(item.get("pages_ocr_scanned")) is int, "TASK115_HISTORICAL_NEGATIVE_COVERAGE")
        _require(type(item.get("ontology_term_count")) is int, "TASK115_HISTORICAL_NEGATIVE_TERMS")
        _require(type(item.get("candidate_count")) is int, "TASK115_HISTORICAL_NEGATIVE_CANDIDATES")
        limitations = item.get("limitations")
        _require(isinstance(limitations, list) and limitations, "TASK115_HISTORICAL_NEGATIVE_LIMITATIONS")
    return deepcopy(gaps), deepcopy(negative)


def execute_research_query(
    bundle: dict[str, Any],
    spec: dict[str, Any],
    *,
    institutionalization_matrix: dict[str, Any] | None = None,
    historical_planning: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = validate_query_spec(spec)
    validated_bundle, indexes = _index_bundle(bundle)
    entity_index = indexes["entities"]
    evidence_index = indexes["evidence"]
    _require(query["subject_id"] in entity_index, "TASK099_SUBJECT_NOT_FOUND")

    claims = _claims_for_subject(
        validated_bundle,
        subject_id=query["subject_id"],
        statuses=set(query["allowed_claim_statuses"]),
        evidence_index=evidence_index,
        entity_index=entity_index,
        include_evidence=query["include_evidence"],
    )

    matrix_packet = {"dimensions": [], "gaps": []}
    historical_gaps: list[dict[str, Any]] = []
    historical_negative: list[dict[str, Any]] = []
    if query["query_type"] in {
        "INSTITUTIONALIZATION_MATRIX",
        "EVIDENCE_GAPS",
        "POLICY_STATUS_PACKET",
    }:
        matrix_packet = _matrix_packet(
            institutionalization_matrix or {},
            include_unknown_gaps=query["include_unknown_gaps"],
        )
    if query["query_type"] in {"EVIDENCE_GAPS", "POLICY_STATUS_PACKET"}:
        historical_gaps, historical_negative = _historical_packets(historical_planning)

    unresolved_claims = [
        {
            "claim_id": item["claim_id"],
            "text": item["text"],
            "status": item["status"],
        }
        for item in claims
        if item["status"] in {"UNKNOWN", "CANDIDATE", "CONFLICTED"}
    ]

    core = {
        "schema": "RESEARCH_QUERY_RESULT_V1",
        "query": query,
        "subject": deepcopy(entity_index[query["subject_id"]]),
        "claims": claims,
        "institutionalization_dimensions": matrix_packet["dimensions"],
        "institutionalization_gaps": matrix_packet["gaps"],
        "historical_acquisition_gaps": historical_gaps,
        "historical_bounded_negative_evidence": historical_negative,
        "unresolved_claims": unresolved_claims,
        "claim_count": len(claims),
        "evidence_reference_count": sum(len(item["evidence_ids"]) for item in claims),
        "status_promotions_performed": 0,
        "financial_identity_created": False,
        "causal_effect_created": False,
        "natural_language_generation_performed": False,
    }
    return {
        **core,
        "result_sha256": sha256(_canonical_bytes(core)).hexdigest(),
    }


def load_query_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(data.get("schema") == "RESEARCH_QUERY_V1", "TASK099_CONTRACT_SCHEMA")
    _require(tuple(data.get("query_types") or ()) == QUERY_TYPES, "TASK099_CONTRACT_QUERY_TYPES")
    _require(
        tuple(data.get("default_allowed_claim_statuses") or ())
        == DEFAULT_ALLOWED_CLAIM_STATUSES,
        "TASK099_CONTRACT_STATUSES",
    )
    remote = data.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK099_CONTRACT_REMOTE_EFFECT")
    return data
