from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from robo_dados_publicos.research.provenance_locator import validate_locator


EXPECTED_PERIODS = ("2018-2021", "2022-2025", "2026-2029")
EXPECTED_HISTORICAL_SIGNALS = {
    "2018-2021": (
        "escolas com programas em tempo integral",
        "TASK055A_PPA2018_ALIAS_MISSING",
    ),
    "2022-2025": (
        "indice de alunos em Educacao Integral",
        "TASK055A_PPA2022_ALIAS_MISSING",
    ),
}
TASK107_2022_SOURCE_SHA256 = "8e10123b07d83e9a9928fd2444318f595a7560eac2bc06c920761ca7893778f7"
TASK107_2022_PAGE_TEXT_SHA256 = "6c8294fb4a511fc7fbc86d69dda780085cdc5bbbea363b8482d06c22eba57883"
TASK107_2022_URL = "https://www.limeira.sp.gov.br/sitenovo/downloads/9d8dd63f39cc3b51ef032a4c96210a07.pdf"
TASK107_2018_URL = "https://www.limeira.sp.gov.br/sitenovo/downloads/0fa1a5cc5c9a1823fbf5436def00f01f.pdf"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EitiHistoricalPlanningStop(RuntimeError):
    """Fail-closed historical planning crosswalk validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EitiHistoricalPlanningStop(code)


def _validate_task107(task107: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(task107, dict), "TASK108_TASK107_OBJECT")
    _require(
        task107.get("schema") == "TASK_107_HISTORICAL_PPA_LIVE_RESULT_V1",
        "TASK108_TASK107_SCHEMA",
    )
    _require(
        task107.get("overall_status") == "PARTIAL_TASK107_ONE_PRIMARY_PPA_MATCH",
        "TASK108_TASK107_STATUS",
    )
    _require(task107.get("primary_match_count") == 1, "TASK108_TASK107_PRIMARY_COUNT")
    _require(task107.get("request_count") == 3, "TASK108_TASK107_REQUEST_COUNT")
    _require(task107.get("retry_performed") is False, "TASK108_TASK107_RETRY")
    _require(task107.get("recurrence") is False, "TASK108_TASK107_RECURRENCE")
    _require(task107.get("schedule") is False, "TASK108_TASK107_SCHEDULE")
    _require(
        task107.get("future_execution_authorized") is False,
        "TASK108_TASK107_FUTURE_EXECUTION",
    )
    boundaries = task107.get("hard_boundaries") or {}
    _require(boundaries and all(value == 0 for value in boundaries.values()), "TASK108_TASK107_BOUNDARY")

    period_results = task107.get("period_results")
    _require(isinstance(period_results, list) and len(period_results) == 2, "TASK108_TASK107_PERIODS")
    indexed = {item.get("period"): item for item in period_results}
    _require(set(indexed) == {"2018-2021", "2022-2025"}, "TASK108_TASK107_PERIOD_SET")

    p2018 = indexed["2018-2021"]
    _require(p2018.get("status") == "STOP_REMOTE_ACQUISITION", "TASK108_2018_MUST_REMAIN_OPEN")
    _require(p2018.get("error") == "TASK106_PDF_TEXT_EMPTY", "TASK108_2018_EMPTY_TEXT_EVIDENCE")

    p2022 = indexed["2022-2025"]
    _require(p2022.get("status") == "PRIMARY_MATCH", "TASK108_2022_PRIMARY_MATCH")
    _require(p2022.get("source_url") == TASK107_2022_URL, "TASK108_2022_SOURCE_URL")
    _require(p2022.get("final_url") == TASK107_2022_URL, "TASK108_2022_FINAL_URL")
    _require(p2022.get("source_sha256") == TASK107_2022_SOURCE_SHA256, "TASK108_2022_SOURCE_SHA")
    _require(p2022.get("source_bytes") == 3273513, "TASK108_2022_SOURCE_BYTES")
    _require(p2022.get("law_number") == "6.659", "TASK108_2022_LAW")
    _require(p2022.get("planning_signal_found") is True, "TASK108_2022_SIGNAL")
    _require(
        p2022.get("primary_document_identity_found_in_pdf_text") is True,
        "TASK108_2022_DOCUMENT_IDENTITY",
    )
    locator = p2022.get("locator") or {}
    _require(locator.get("coordinate_system") == "SOURCE_PDF_PAGE_1_BASED", "TASK108_2022_LOCATOR_SYSTEM")
    _require(locator.get("page") == 23, "TASK108_2022_LOCATOR_PAGE")
    _require(
        locator.get("page_text_sha256") == TASK107_2022_PAGE_TEXT_SHA256,
        "TASK108_2022_PAGE_HASH",
    )
    _require(p2022.get("financial_identity_created") is False, "TASK108_2022_FINANCIAL_IDENTITY")
    _require(p2022.get("implementation_proven") is False, "TASK108_2022_IMPLEMENTATION")
    _require(p2022.get("causal_effect_created") is False, "TASK108_2022_CAUSAL")
    return indexed


def validate_historical_planning_crosswalk(
    data: dict[str, Any],
    *,
    task055a: dict[str, Any],
    task096: dict[str, Any],
    task107: dict[str, Any],
) -> dict[str, Any]:
    _require(isinstance(data, dict), "TASK098_OBJECT")
    _require(
        data.get("schema") == "EITI_HISTORICAL_PLANNING_CROSSWALK_V1",
        "TASK098_SCHEMA",
    )
    _require(
        data.get("mode") == "T0_OFFLINE_VERSIONED_REPOSITORY_EVIDENCE_ONLY",
        "TASK098_MODE",
    )
    _require(data.get("policy_id") == "POLICY:EITI_LIMEIRA", "TASK098_POLICY")

    remote = data.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK098_REMOTE_EFFECT")

    ontology = task055a.get("ontology") or {}
    aliases = set(ontology.get("B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES") or [])
    _require(
        task055a.get("task") == "TASK_055A_F01_EITI_TERMINOLOGY_ONTOLOGY",
        "TASK098_TASK055A_ID",
    )
    _require(
        (task055a.get("matching_rules") or {}).get("no_semantic_overreach") is True,
        "TASK098_TASK055A_OVERREACH_GUARD",
    )

    _require(
        task096.get("task") == "TASK_096_EITI_LIMEIRA_OFFLINE_CROSSWALK",
        "TASK098_TASK096_ID",
    )
    task096_matrix = task096.get("institutionalization_matrix") or {}
    _require(
        task096_matrix.get("normative_planning_persistence") == "CORROBORATED",
        "TASK098_TASK096_PERSISTENCE_BASELINE",
    )
    _require(
        task096_matrix.get("budgetary_persistence") == "UNKNOWN",
        "TASK098_TASK096_BUDGETARY_PERSISTENCE_BASELINE",
    )

    live_periods = _validate_task107(task107)

    raw_periods = data.get("periods")
    _require(isinstance(raw_periods, list), "TASK098_PERIODS")
    _require(
        tuple(item.get("period") for item in raw_periods) == EXPECTED_PERIODS,
        "TASK098_PERIOD_ORDER",
    )
    periods = {item["period"]: item for item in raw_periods}

    for period, (signal, validator_tag) in EXPECTED_HISTORICAL_SIGNALS.items():
        item = periods[period]
        _require(item.get("repository_signal") == signal, f"TASK098_{period}_SIGNAL")
        _require(signal in aliases, f"TASK098_{period}_SIGNAL_NOT_IN_TASK055A")
        _require(
            item.get("signal_origin") == "TASK_055A_LOCAL_PLANNING_ALIAS",
            f"TASK098_{period}_ORIGIN",
        )
        _require(
            item.get("task055a_validator_tag") == validator_tag,
            f"TASK098_{period}_VALIDATOR_TAG",
        )
        _require(
            item.get("financial_identity_status") == "UNKNOWN",
            f"TASK098_{period}_FINANCIAL_IDENTITY",
        )

    historical = periods["2018-2021"]
    for flag in (
        "primary_document_entity_versioned",
        "primary_source_hash_versioned",
        "primary_locator_versioned",
    ):
        _require(historical.get(flag) is False, f"TASK098_2018-2021_{flag.upper()}_OVERCLAIM")
    _require(historical.get("planning_signal_status") == "CANDIDATE", "TASK098_2018-2021_PLANNING_STATUS")
    _require(historical.get("policy_link_status") == "UNKNOWN", "TASK098_2018-2021_POLICY_LINK_STATUS")
    _require(historical.get("task107_official_pdf_url") == TASK107_2018_URL, "TASK108_2018_URL")
    _require(historical.get("task107_parser_status") == "PDF_TEXT_EMPTY", "TASK108_2018_PARSER_STATUS")
    _require(
        historical.get("task107_live_result") == "docs/evidence/TASK_107_LIVE_RESULT_0.8.0.json",
        "TASK108_2018_EVIDENCE_RECORD",
    )
    requests_2018 = [
        item for item in task107.get("requests") or []
        if item.get("period") == "2018-2021"
    ]
    _require(len(requests_2018) == 2, "TASK108_2018_REQUEST_COUNT")
    _require(requests_2018[-1].get("path") == "/sitenovo/downloads/0fa1a5cc5c9a1823fbf5436def00f01f.pdf", "TASK108_2018_RESOLVED_PATH")

    prior = periods["2022-2025"]
    for flag in (
        "primary_document_entity_versioned",
        "primary_source_hash_versioned",
        "primary_locator_versioned",
    ):
        _require(prior.get(flag) is True, f"TASK108_2022_{flag.upper()}")
    _require(prior.get("planning_signal_status") == "PROVEN", "TASK108_2022_PLANNING_STATUS")
    _require(prior.get("policy_link_status") == "CANDIDATE", "TASK108_2022_POLICY_LINK_STATUS")
    _require(prior.get("primary_evidence_task") == "TASK_107", "TASK108_2022_EVIDENCE_TASK")
    _require(
        prior.get("primary_evidence_record") == "docs/evidence/TASK_107_LIVE_RESULT_0.8.0.json",
        "TASK108_2022_EVIDENCE_RECORD",
    )
    _require(prior.get("primary_source_url") == TASK107_2022_URL, "TASK108_2022_CROSSWALK_URL")
    _require(
        prior.get("primary_source_sha256") == TASK107_2022_SOURCE_SHA256,
        "TASK108_2022_CROSSWALK_SOURCE_SHA",
    )
    _require(prior.get("primary_source_bytes") == 3273513, "TASK108_2022_CROSSWALK_SOURCE_BYTES")
    locator_2022 = prior.get("preferred_locator") or {}
    _require(locator_2022.get("coordinate_system") == "SOURCE_PDF_PAGE_1_BASED", "TASK108_2022_CROSSWALK_LOCATOR_SYSTEM")
    _require(locator_2022.get("page") == 23, "TASK108_2022_CROSSWALK_LOCATOR_PAGE")
    _require(locator_2022.get("source_sha256") == TASK107_2022_SOURCE_SHA256, "TASK108_2022_CROSSWALK_LOCATOR_SOURCE_SHA")
    _require(locator_2022.get("page_text_sha256") == TASK107_2022_PAGE_TEXT_SHA256, "TASK108_2022_CROSSWALK_PAGE_SHA")
    _require(
        locator_2022.get("match_signal") == "ÍNDICE DE ALUNOS EM EDUCACAO INTEGRAL",
        "TASK108_2022_CROSSWALK_SIGNAL",
    )
    _require(
        live_periods["2022-2025"]["source_sha256"] == prior["primary_source_sha256"],
        "TASK108_2022_LIVE_CROSSWALK_SHA_MISMATCH",
    )

    current = periods["2026-2029"]
    for flag in (
        "primary_document_entity_versioned",
        "primary_source_hash_versioned",
        "primary_locator_versioned",
    ):
        _require(current.get(flag) is True, f"TASK098_CURRENT_{flag.upper()}")
    _require(current.get("planning_signal_status") == "PROVEN", "TASK098_CURRENT_PLANNING_STATUS")
    _require(current.get("policy_link_status") == "CORROBORATED", "TASK098_CURRENT_POLICY_LINK_STATUS")
    _require(current.get("financial_identity_status") == "UNKNOWN", "TASK098_CURRENT_FINANCIAL_IDENTITY")

    locator_raw = current.get("preferred_locator") or {}
    locator = validate_locator(
        {
            "page": locator_raw.get("page"),
            "coordinate_system": locator_raw.get("coordinate_system"),
            "source_key": "SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf",
            "source_sha256": locator_raw.get("source_sha256"),
            "page_text_sha256": locator_raw.get("page_text_sha256"),
        }
    )
    _require(locator["page"] == 15, "TASK098_CURRENT_LOCATOR_PAGE")
    _require(locator["coordinate_system"] == "JOURNAL_EDITION_PDF_PAGE", "TASK098_CURRENT_LOCATOR_SYSTEM")

    longitudinal = data.get("longitudinal_assessment") or {}
    _require(
        longitudinal.get("three_ppa_period_policy_continuity") == "CANDIDATE",
        "TASK098_THREE_PPA_CONTINUITY_OVERCLAIM",
    )
    _require(
        longitudinal.get("three_ppa_period_budgetary_persistence") == "UNKNOWN",
        "TASK098_THREE_PPA_BUDGETARY_PERSISTENCE",
    )
    _require(
        longitudinal.get("existing_task096_normative_planning_persistence") == "CORROBORATED",
        "TASK098_TASK096_PERSISTENCE_CHANGED",
    )
    _require(
        longitudinal.get("existing_task096_normative_planning_persistence_preserved") is True,
        "TASK098_TASK096_PERSISTENCE_NOT_PRESERVED",
    )
    _require(
        longitudinal.get("two_of_three_primary_planning_periods_proven") is True,
        "TASK108_TWO_OF_THREE_PRIMARY_NOT_PRESERVED",
    )

    gaps = data.get("acquisition_gaps")
    _require(isinstance(gaps, list) and len(gaps) == 1, "TASK108_ACQUISITION_GAPS")
    gap = gaps[0]
    _require(gap.get("period") == "2018-2021", "TASK108_GAP_PERIOD")
    required_gap_fields = {
        "PRIMARY_PPA_DOCUMENT_IDENTITY",
        "STABLE_SOURCE_HASH_OR_EQUIVALENT_IDENTITY",
        "TYPED_LOCATOR_FOR_THE_RELEVANT_PLANNING_SIGNAL",
        "DIRECT_TEXT_OR_VISUAL_EVIDENCE",
    }
    _require(
        set(gap.get("required_before_promotion") or []) == required_gap_fields,
        "TASK098_2018-2021_GAP_REQUIREMENTS",
    )
    _require(
        "PYPDF_TEXT_EMPTY" in str(gap.get("current_obstacle") or ""),
        "TASK108_2018_CURRENT_OBSTACLE",
    )

    forbidden = set(data.get("forbidden_promotions") or [])
    required_forbidden = {
        "TASK055A_ALIAS_TO_PROVEN_PRIMARY_PLANNING_FACT",
        "HISTORICAL_ALIAS_TO_FINANCIAL_IDENTITY",
        "THREE_PPA_ALIAS_SEQUENCE_TO_PROVEN_POLICY_CONTINUITY",
        "PLANNING_SIGNAL_TO_OBSERVED_IMPLEMENTATION",
        "PLANNING_SIGNAL_TO_CAUSAL_OUTCOME",
    }
    _require(required_forbidden.issubset(forbidden), "TASK098_FORBIDDEN_PROMOTIONS")

    return {
        "status": "PASS_TASK108_EITI_HISTORICAL_PLANNING_PRIMARY_EVIDENCE_INGESTED",
        "period_count": 3,
        "historical_candidate_periods": 1,
        "primary_proven_periods": 2,
        "historical_primary_gaps_remaining": 1,
        "three_ppa_continuity_status": "CANDIDATE",
        "three_ppa_budgetary_persistence_status": "UNKNOWN",
        "task096_persistence_preserved": True,
        "new_source_reads": 0,
        "remote_effects": 0,
    }


def load_and_validate_historical_planning_crosswalk(
    crosswalk_path: str | Path,
    *,
    task055a_path: str | Path,
    task096_path: str | Path,
    task107_path: str | Path,
) -> dict[str, Any]:
    data = json.loads(Path(crosswalk_path).read_text(encoding="utf-8"))
    task055a = json.loads(Path(task055a_path).read_text(encoding="utf-8"))
    task096 = json.loads(Path(task096_path).read_text(encoding="utf-8"))
    task107 = json.loads(Path(task107_path).read_text(encoding="utf-8"))
    return validate_historical_planning_crosswalk(
        data,
        task055a=task055a,
        task096=task096,
        task107=task107,
    )
