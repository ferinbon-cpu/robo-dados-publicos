from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.research.evidence_semantics import (
    validate_negative_evidence,
    validate_semantic_evidence,
)
from robo_dados_publicos.research.ontology import validate_research_bundle


class EitiCrosswalkStop(RuntimeError):
    """Fail-closed EITI-Limeira crosswalk validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EitiCrosswalkStop(code)


def _rows_from_csv_text(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))


def _by(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    values: dict[str, dict[str, str]] = {}
    for row in rows:
        value = str(row.get(key) or "")
        _require(value != "" and value not in values, f"TASK096_DUPLICATE_OR_MISSING_{key.upper()}")
        values[value] = row
    return values


def validate_eiti_crosswalk(
    data: dict[str, Any],
    *,
    legacy_edges_csv: str,
    graph_qa_csv: str,
) -> dict[str, Any]:
    _require(isinstance(data, dict), "TASK096_OBJECT")
    _require(data.get("schema") == "EITI_LIMEIRA_RESEARCH_CROSSWALK_V1", "TASK096_SCHEMA")
    _require(
        data.get("mode") == "T0_OFFLINE_EXISTING_REPOSITORY_EVIDENCE_ONLY",
        "TASK096_MODE",
    )

    provenance = data.get("provenance_scope") or {}
    _require(provenance.get("repository_only") is True, "TASK096_REPOSITORY_ONLY")
    for key in ("new_drive_reads", "new_public_network_reads", "new_source_acquisition"):
        _require(provenance.get(key) == 0, f"TASK096_PROVENANCE_{key.upper()}")

    effects = data.get("effects") or {}
    _require(effects and all(value == 0 for value in effects.values()), "TASK096_REMOTE_EFFECT")

    bundle = validate_research_bundle(data.get("research_bundle") or {})
    entity_map = {item["id"]: item for item in bundle["entities"]}
    relation_map = {item["relation_id"]: item for item in bundle["relations"]}
    claim_map = {item["claim_id"]: item for item in bundle["claims"]}
    evidence_map = {item["evidence_id"]: item for item in bundle["evidence"]}

    _require("POLICY:EITI_LIMEIRA" in entity_map, "TASK096_POLICY_ENTITY")
    _require(entity_map["POLICY:EITI_LIMEIRA"]["type"] == "POLICY", "TASK096_POLICY_TYPE")

    semantic_raw = data.get("semantic_evidence")
    _require(isinstance(semantic_raw, list) and semantic_raw, "TASK096_SEMANTIC_EVIDENCE")
    semantic = [validate_semantic_evidence(item) for item in semantic_raw]
    semantic_map = {item["evidence_id"]: item for item in semantic}
    _require(len(semantic_map) == len(semantic), "TASK096_DUPLICATE_SEMANTIC_EVIDENCE")
    _require(set(semantic_map) == set(evidence_map), "TASK096_SEMANTIC_EVIDENCE_COVERAGE")

    negative_raw = data.get("negative_evidence")
    _require(isinstance(negative_raw, list) and negative_raw, "TASK096_NEGATIVE_EVIDENCE")
    negative = [validate_negative_evidence(item) for item in negative_raw]
    negative_map = {item["search_id"]: item for item in negative}
    _require(len(negative_map) == len(negative), "TASK096_DUPLICATE_NEGATIVE_SEARCH")

    for item in semantic:
        search_id = item.get("negative_search_id")
        if search_id is not None:
            _require(search_id in negative_map, "TASK096_NEGATIVE_SEARCH_REFERENCE")
            _require(item["claim_domain"] == "SEARCH_RESULT", "TASK096_NEGATIVE_SEARCH_DOMAIN")

    edges = _by(_rows_from_csv_text(legacy_edges_csv), "edge_id")
    qa = _by(_rows_from_csv_text(graph_qa_csv), "qid")

    for edge_id, source, target, confidence in (
        ("E05", "decreto_118_2024", "policy_eiti_limeira", "A"),
        ("E06", "lei_7366_2026", "policy_eiti_limeira", "A"),
        ("E11", "policy_eiti_limeira", "ppa_program_2001", "B"),
        ("E12", "policy_eiti_limeira", "ppa_indicator_eiti", "B"),
    ):
        edge = edges.get(edge_id) or {}
        _require(edge.get("source_id") == source, f"TASK096_LEGACY_{edge_id}_SOURCE")
        _require(edge.get("target_id") == target, f"TASK096_LEGACY_{edge_id}_TARGET")
        _require(edge.get("confidence") == confidence, f"TASK096_LEGACY_{edge_id}_CONFIDENCE")

    g10 = qa.get("G10") or {}
    _require(g10.get("source") == "policy_eiti_limeira", "TASK096_G10_SOURCE")
    _require(g10.get("target") == "ppa_program_2001", "TASK096_G10_TARGET")
    _require(g10.get("relation") == "financial_identity", "TASK096_G10_RELATION")
    _require(g10.get("expected_exists") == "0" and g10.get("actual_exists") == "0", "TASK096_G10_FINANCIAL_IDENTITY_ABSENT")
    _require(g10.get("ok") == "1", "TASK096_G10_QA")

    _require(
        relation_map["REL:DECREE_ESTABLISHES_POLICY"]["status"] == "PROVEN",
        "TASK096_DECREE_STATUS",
    )
    _require(
        relation_map["REL:LAW_ESTABLISHES_POLICY"]["status"] == "PROVEN",
        "TASK096_LAW_STATUS",
    )
    _require(
        relation_map["REL:POLICY_PROGRAM_OVERLAP"]["status"] == "CORROBORATED",
        "TASK096_POLICY_PROGRAM_STATUS",
    )
    _require(
        relation_map["REL:POLICY_PROGRAM_OVERLAP"]["attributes"].get("financial_identity") is False,
        "TASK096_POLICY_PROGRAM_FINANCIAL_OVERREACH",
    )
    _require(
        relation_map["REL:INDICATOR_MEASURES_POLICY"]["status"] == "CORROBORATED",
        "TASK096_INDICATOR_POLICY_STATUS",
    )

    forbidden_policy_targets = {
        "EXPENSE:LOA2026_2720_12_306",
        "EXPENSE:LOA2026_2690_12_362",
        "EXPENSE:FOMENTO_ETI_FUNDEB_2026_B1",
    }
    for relation in bundle["relations"]:
        if relation["source_id"] == "POLICY:EITI_LIMEIRA" and relation["target_id"] in forbidden_policy_targets:
            _require(
                relation["relation_type"] not in {"SAME_IDENTITY_AS", "FINANCES", "EXECUTES"},
                "TASK096_FORBIDDEN_POLICY_FINANCIAL_RELATION",
            )

    _require(
        claim_map["CLAIM:EITI_PPA_PROGRAM_CORRESPONDENCE"]["status"] == "CORROBORATED",
        "TASK096_PPA_CORRESPONDENCE_STATUS",
    )
    _require(
        claim_map["CLAIM:EITI_PPA_PROGRAM_CORRESPONDENCE"]["attributes"].get("financial_identity") is False,
        "TASK096_PPA_CORRESPONDENCE_FINANCIAL_OVERREACH",
    )
    financial = claim_map["CLAIM:EITI_FINANCIAL_IDENTITY"]
    _require(financial["status"] == "UNKNOWN", "TASK096_FINANCIAL_IDENTITY_STATUS")
    _require(
        financial["attributes"].get("upstream_status") == "EVIDENCIA_INSUFICIENTE",
        "TASK096_FINANCIAL_UPSTREAM_STATUS",
    )

    action_search = claim_map["CLAIM:PPA_NO_EXPLICIT_EITI_ACTION_LABEL"]
    _require(action_search["status"] == "PROVEN", "TASK096_ACTION_SEARCH_STATUS")
    _require(action_search["attributes"].get("claim_domain") == "SEARCH_RESULT", "TASK096_ACTION_SEARCH_DOMAIN")
    _require(action_search["attributes"].get("proves_no_eiti_spending") is False, "TASK096_ACTION_SEARCH_OVERREACH")

    bucket = entity_map["EXPENSE:FOMENTO_ETI_FUNDEB_2026_B1"]
    _require(bucket["attributes"].get("aggregation_level") == "REPORTING_BUCKET", "TASK096_FOMENTO_BUCKET_LEVEL")
    _require(bucket["attributes"].get("applied_amount_brl") == "0.00", "TASK096_FOMENTO_AMOUNT")
    _require(bucket["attributes"].get("transaction_identity_proven") is False, "TASK096_FOMENTO_TRANSACTION_OVERREACH")
    _require(
        claim_map["CLAIM:FOMENTO_ETI_REPORTING_BUCKET"]["status"] == "PROVEN",
        "TASK096_FOMENTO_REPORTING_STATUS",
    )
    _require(
        claim_map["CLAIM:FOMENTO_ETI_TRANSACTION_IDENTITY"]["status"] == "UNKNOWN",
        "TASK096_FOMENTO_TRANSACTION_STATUS",
    )

    for expense_id in ("EXPENSE:LOA2026_2720_12_306", "EXPENSE:LOA2026_2690_12_362"):
        expense = entity_map[expense_id]
        _require(expense["attributes"].get("eiti_specific") is False, "TASK096_GENERIC_LOA_EITI_FLAG")
        _require(
            expense["attributes"].get("execution_stage") == "NOT_APPLICABLE_TO_LOA_ENACTMENT_READ",
            "TASK096_LOA_EXECUTION_OVERREACH",
        )

    page_issue = data.get("page_numbering_issue") or {}
    _require(page_issue.get("observed") is True, "TASK096_PAGE_ISSUE_MISSING")
    _require(page_issue.get("legacy_graph_page") == 18, "TASK096_PAGE_LEGACY")
    _require(page_issue.get("scoped_jom_page") == 15, "TASK096_PAGE_JOM")
    _require(page_issue.get("reconciled") is False, "TASK096_PAGE_SILENT_RECONCILIATION")

    matrix = data.get("institutionalization_matrix") or {}
    expected_matrix = {
        "normative": "PROVEN",
        "planning": "CORROBORATED",
        "budgetary_policy_identity": "UNKNOWN",
        "financial_reporting": "PROVEN",
        "transaction_execution_identity": "UNKNOWN",
        "organizational": "CANDIDATE",
        "material_delivery": "UNKNOWN",
        "outcome_effect": "UNKNOWN",
        "normative_planning_persistence": "CORROBORATED",
        "budgetary_persistence": "UNKNOWN",
    }
    for dimension, expected in expected_matrix.items():
        _require(
            (matrix.get(dimension) or {}).get("status") == expected,
            f"TASK096_MATRIX_{dimension.upper()}",
        )

    forbidden = set(data.get("forbidden_promotions") or [])
    required_forbidden = {
        "PROGRAM_2001_TOTAL_TO_EITI",
        "ACTION_2690_TO_EITI",
        "ACTION_2720_TO_EITI",
        "LOA_AMOUNT_ALIGNMENT_TO_FINANCIAL_IDENTITY",
        "FOMENTO_ETI_REPORTING_BUCKET_TO_TRANSACTION_IDENTITY",
        "ZERO_FUNDEB_FOMENTO_ETI_TO_ZERO_TOTAL_EITI_SPENDING",
        "PLANNING_TARGET_TO_OBSERVED_OUTCOME",
        "STATISTICAL_ASSOCIATION_TO_CAUSAL_EFFECT",
    }
    _require(required_forbidden.issubset(forbidden), "TASK096_FORBIDDEN_PROMOTIONS")

    causal_claims = [
        claim for claim in bundle["claims"]
        if (claim.get("attributes") or {}).get("claim_domain") == "CAUSAL_EFFECT"
    ]
    _require(not causal_claims, "TASK096_CAUSAL_CLAIM_FORBIDDEN")

    return {
        "status": "PASS_TASK096_EITI_LIMEIRA_OFFLINE_CROSSWALK",
        "entity_count": len(bundle["entities"]),
        "relation_count": len(bundle["relations"]),
        "claim_count": len(bundle["claims"]),
        "evidence_count": len(bundle["evidence"]),
        "negative_search_count": len(negative),
        "normative_status": matrix["normative"]["status"],
        "planning_status": matrix["planning"]["status"],
        "budgetary_policy_identity_status": matrix["budgetary_policy_identity"]["status"],
        "financial_reporting_status": matrix["financial_reporting"]["status"],
        "transaction_execution_identity_status": matrix["transaction_execution_identity"]["status"],
        "page_numbering_reconciled": False,
        "remote_effects": 0,
    }


def load_and_validate_eiti_crosswalk(
    crosswalk_path: str | Path,
    *,
    legacy_edges_path: str | Path,
    graph_qa_path: str | Path,
) -> dict[str, Any]:
    data = json.loads(Path(crosswalk_path).read_text(encoding="utf-8"))
    return validate_eiti_crosswalk(
        data,
        legacy_edges_csv=Path(legacy_edges_path).read_text(encoding="utf-8-sig"),
        graph_qa_csv=Path(graph_qa_path).read_text(encoding="utf-8-sig"),
    )
