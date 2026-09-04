from __future__ import annotations

import json
from pathlib import Path
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


class EitiHistoricalPlanningStop(RuntimeError):
    """Fail-closed historical planning crosswalk validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EitiHistoricalPlanningStop(code)


def validate_historical_planning_crosswalk(
    data: dict[str, Any],
    *,
    task055a: dict[str, Any],
    task096: dict[str, Any],
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
        for flag in (
            "primary_document_entity_versioned",
            "primary_source_hash_versioned",
            "primary_locator_versioned",
        ):
            _require(item.get(flag) is False, f"TASK098_{period}_{flag.upper()}_OVERCLAIM")
        _require(
            item.get("planning_signal_status") == "CANDIDATE",
            f"TASK098_{period}_PLANNING_STATUS",
        )
        _require(
            item.get("policy_link_status") == "UNKNOWN",
            f"TASK098_{period}_POLICY_LINK_STATUS",
        )
        _require(
            item.get("financial_identity_status") == "UNKNOWN",
            f"TASK098_{period}_FINANCIAL_IDENTITY",
        )

    current = periods["2026-2029"]
    for flag in (
        "primary_document_entity_versioned",
        "primary_source_hash_versioned",
        "primary_locator_versioned",
    ):
        _require(current.get(flag) is True, f"TASK098_CURRENT_{flag.upper()}")
    _require(
        current.get("planning_signal_status") == "PROVEN",
        "TASK098_CURRENT_PLANNING_STATUS",
    )
    _require(
        current.get("policy_link_status") == "CORROBORATED",
        "TASK098_CURRENT_POLICY_LINK_STATUS",
    )
    _require(
        current.get("financial_identity_status") == "UNKNOWN",
        "TASK098_CURRENT_FINANCIAL_IDENTITY",
    )

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
    _require(
        locator["coordinate_system"] == "JOURNAL_EDITION_PDF_PAGE",
        "TASK098_CURRENT_LOCATOR_SYSTEM",
    )

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
        longitudinal.get("existing_task096_normative_planning_persistence")
        == "CORROBORATED",
        "TASK098_TASK096_PERSISTENCE_CHANGED",
    )
    _require(
        longitudinal.get("existing_task096_normative_planning_persistence_preserved")
        is True,
        "TASK098_TASK096_PERSISTENCE_NOT_PRESERVED",
    )

    gaps = data.get("acquisition_gaps")
    _require(isinstance(gaps, list) and len(gaps) == 2, "TASK098_ACQUISITION_GAPS")
    gap_by_period = {item.get("period"): item for item in gaps}
    _require(set(gap_by_period) == {"2018-2021", "2022-2025"}, "TASK098_GAP_PERIODS")
    required_gap_fields = {
        "PRIMARY_PPA_DOCUMENT_IDENTITY",
        "STABLE_SOURCE_HASH_OR_EQUIVALENT_IDENTITY",
        "TYPED_LOCATOR_FOR_THE_RELEVANT_PLANNING_SIGNAL",
        "DIRECT_TEXT_OR_VISUAL_EVIDENCE",
    }
    for period in ("2018-2021", "2022-2025"):
        _require(
            set(gap_by_period[period].get("required_before_promotion") or [])
            == required_gap_fields,
            f"TASK098_{period}_GAP_REQUIREMENTS",
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
        "status": "PASS_TASK098_EITI_HISTORICAL_PLANNING_COVERAGE_OFFLINE",
        "period_count": 3,
        "historical_candidate_periods": 2,
        "primary_proven_periods": 1,
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
) -> dict[str, Any]:
    data = json.loads(Path(crosswalk_path).read_text(encoding="utf-8"))
    task055a = json.loads(Path(task055a_path).read_text(encoding="utf-8"))
    task096 = json.loads(Path(task096_path).read_text(encoding="utf-8"))
    return validate_historical_planning_crosswalk(
        data,
        task055a=task055a,
        task096=task096,
    )
