"""Fail-closed validation for TASK 057 metadata-only FUNDEB candidate selection."""
from __future__ import annotations

from typing import Any

TASK = "TASK_057_F01_FUNDEB_FOMENTO_ETI_LINKAGE_CANDIDATE_SELECTION"
MODE = "T0_EXISTING_CUSTODY_METADATA_ONLY_CANDIDATE_SELECTION"
BASE_SHA = "0550879110581d4b491e6fcb6d5b812bc36e6ae9"
RESULT = "PASS_TASK057_METADATA_ONLY_TIE_NO_EVIDENTIARY_BEST_CANDIDATE_NEXT_PROBE_SELECTED_BY_STABLE_ORDER_NO_PROMOTION"
EXPECTED_IDS = [
    "1zRG-7fXYMTOMjsbWWJzoaSF7kQ54kJMe",
    "1xmAFcp2pYYeua3vHQQoY4_tfFZzr21-I",
    "1m1mg8LX-7VOn81Rl4t-zgDoP23JPCTRd",
]
EXPECTED_TITLES = [
    "FUNDEB_LIMEIRA_2026_01.pdf",
    "FUNDEB_LIMEIRA_2026_02.pdf",
    "FUNDEB_LIMEIRA_2026_03.pdf",
]


class Task057Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task057Error(code)


def validate_task057_evidence(evidence: dict[str, Any], task056: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK057_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK057_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK057_BASE_SHA_MISMATCH")

    _require(task056.get("task") == "TASK_056_F01_SECONDARY_EDUCATION_SOURCE_BOUNDED_CONTENT_READ", "TASK057_UPSTREAM_TASK_MISMATCH")
    _require(task056.get("result") == "PASS_TASK056_MAVS_FOMENTO_ETI_REPORTING_IDENTITY_PARTIAL_NO_TRANSACTION_LINKAGE_NO_PROMOTION", "TASK057_UPSTREAM_RESULT_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK057_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga autorizado", "TASK057_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK057_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK057_BLANKET_AUTH_FORBIDDEN")

    contract = evidence.get("metadata_contract") or {}
    _require(contract.get("allowed_drive_search_surface") == "DRIVE_SEARCH_METADATA_ONLY_WITH_ITEM_TYPE_DOCUMENT", "TASK057_SEARCH_SURFACE_MISMATCH")
    _require(contract.get("best_effort_fetch") is False, "TASK057_BEST_EFFORT_FETCH_FORBIDDEN")
    for key in ("source_content_read_allowed", "drive_fetch_allowed", "ocr_allowed", "public_source_network_allowed", "drive_write_allowed", "promotion_allowed"):
        _require(contract.get(key) is False, f"TASK057_POLICY_{key.upper()}_WEAKENED")

    candidates = evidence.get("candidate_set") or []
    _require(len(candidates) == 3, "TASK057_CANDIDATE_COUNT_MISMATCH")
    _require([c.get("drive_file_id") for c in candidates] == EXPECTED_IDS, "TASK057_CANDIDATE_IDS_MISMATCH")
    _require([c.get("title") for c in candidates] == EXPECTED_TITLES, "TASK057_CANDIDATE_TITLES_MISMATCH")
    _require(all(c.get("content_hydrated") is False for c in candidates), "TASK057_CONTENT_HYDRATION_OCCURRED")

    searches = evidence.get("metadata_searches") or {}
    _require(searches.get("count") == 3, "TASK057_SEARCH_COUNT_MISMATCH")
    _require(searches.get("all_item_type_document") is True, "TASK057_ITEM_TYPE_NOT_DOCUMENT")
    _require(searches.get("all_best_effort_fetch_false") is True, "TASK057_BEST_EFFORT_FETCH_TRUE")
    _require(searches.get("source_content_reads") == 0, "TASK057_SOURCE_CONTENT_READ_OCCURRED")

    analysis = evidence.get("selection_analysis") or {}
    _require(analysis.get("metadata_can_distinguish_probative_granularity") is False, "TASK057_UNSUPPORTED_METADATA_RANKING")
    _require(analysis.get("metadata_can_prove_program_action_ficha_or_transaction_key") is False, "TASK057_UNSUPPORTED_LINKAGE_CLAIM")
    _require(analysis.get("candidate_titles_are_probatively_equivalent") is True, "TASK057_TIE_NOT_RECORDED")
    _require(analysis.get("suffix_01_02_03_must_not_be_treated_as_evidence_of_superior_granularity") is True, "TASK057_SUFFIX_OVERCLAIM")
    _require(analysis.get("best_candidate_evidentially_resolved") is False, "TASK057_FALSE_BEST_CANDIDATE")
    _require(analysis.get("selection_status") == "METADATA_TIE_NO_EVIDENTIARY_BEST_CANDIDATE", "TASK057_SELECTION_STATUS_MISMATCH")
    _require(analysis.get("forced_best_candidate_forbidden") is True, "TASK057_FORCED_SELECTION_NOT_FORBIDDEN")

    probe = evidence.get("deterministic_next_probe") or {}
    _require(probe.get("enabled") is True, "TASK057_NEXT_PROBE_DISABLED")
    _require(probe.get("selection_basis") == "STABLE_SEED_ORDER_ONLY_NOT_PROBATIVE_RANKING", "TASK057_NEXT_PROBE_BASIS_MISMATCH")
    _require(probe.get("selected_drive_file_id") == EXPECTED_IDS[0], "TASK057_NEXT_PROBE_ID_MISMATCH")
    _require(probe.get("selected_title") == EXPECTED_TITLES[0], "TASK057_NEXT_PROBE_TITLE_MISMATCH")
    _require(probe.get("selected_is_claimed_best") is False, "TASK057_NEXT_PROBE_FALSE_BEST_CLAIM")
    _require(probe.get("fresh_owner_authorization_required_before_content_read") is True, "TASK057_FRESH_AUTH_NOT_REQUIRED")
    _require(probe.get("max_source_content_reads_if_later_authorized") == 1, "TASK057_FUTURE_READ_BOUND_MISMATCH")

    effects = evidence.get("effects") or {}
    _require(effects.get("drive_metadata_searches") == 3, "TASK057_EFFECT_SEARCH_COUNT_MISMATCH")
    for key in ("source_content_reads", "drive_fetch", "ocr", "public_source_network", "drive_write", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"TASK057_EFFECT_{key.upper()}_NONZERO")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK057_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_reporting_identity") == "PARTIALLY_PROVEN_DEDICATED_FUNDEB_FOMENTO_ETI_BUCKET", "TASK057_REPORTING_STATUS_MISMATCH")
    _require(promotion.get("eiti_transaction_level_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK057_TRANSACTION_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK057_OVERALL_EITI_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK057_DOWNSTREAM_PROMOTION_ENABLED")

    next_gate = evidence.get("next_bounded_gate") or {}
    _require(next_gate.get("name") == "TASK_058_F01_FUNDEB_TIED_CANDIDATE_01_BOUNDED_CONTENT_READ", "TASK057_NEXT_GATE_MISMATCH")
    _require(next_gate.get("selected_drive_file_id") == EXPECTED_IDS[0], "TASK057_NEXT_GATE_SOURCE_MISMATCH")
    _require(next_gate.get("selection_basis") == "STABLE_SEED_ORDER_ONLY_NOT_PROBATIVE_RANKING", "TASK057_NEXT_GATE_BASIS_MISMATCH")
    _require(next_gate.get("fresh_owner_authorization_required") is True, "TASK057_NEXT_GATE_AUTH_WEAKENED")
    _require(next_gate.get("max_source_content_reads") == 1, "TASK057_NEXT_GATE_READ_BOUND_MISMATCH")
    _require(next_gate.get("no_other_source_read") is True, "TASK057_NEXT_GATE_OTHER_READ_ENABLED")
    _require(next_gate.get("no_public_network") is True, "TASK057_NEXT_GATE_NETWORK_ENABLED")
    _require(next_gate.get("no_drive_write") is True, "TASK057_NEXT_GATE_DRIVE_WRITE_ENABLED")
    _require(next_gate.get("no_promotion") is True, "TASK057_NEXT_GATE_PROMOTION_ENABLED")

    _require(evidence.get("result") == RESULT, "TASK057_RESULT_MISMATCH")

    return {
        "status": RESULT,
        "selection_status": analysis["selection_status"],
        "next_probe_id": probe["selected_drive_file_id"],
        "next_gate": next_gate["name"],
    }
