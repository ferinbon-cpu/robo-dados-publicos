"""Fail-closed validation for TASK 054 metadata-safe existing-custody inventory."""
from __future__ import annotations

from typing import Any

TASK = "TASK_054_METADATA_SAFE_EXISTING_CUSTODY_INVENTORY_EXECUTION"
MODE = "T1_EXISTING_CUSTODY_METADATA_SAFE_INVENTORY_EXECUTION"
BASE_SHA = "15b2bd9562b126aa3215c37d656bd41c598609d4"
RESULT = "PASS_TASK054_METADATA_SAFE_INVENTORY_CANDIDATES_SELECTED_NO_SOURCE_READ"
PRIMARY_ID = "1PTAnH-LL_8fvS7TsVuHSci5dBDKFLQTS"
PRIMARY_TITLE = "05 - Maio_despesa.pdf"
NEXT_GATE = "TASK_055_F01_SELECTED_GRANULAR_SOURCE_BOUNDED_CONTENT_READ"


class Task054Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task054Error(code)


def validate_task054_evidence(evidence: dict[str, Any], task053: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK054_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK054_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK054_BASE_SHA_MISMATCH")

    _require(task053.get("task") == "TASK_053_METADATA_SAFE_CANDIDATE_INVENTORY_REDESIGN", "TASK054_TASK053_ID_MISMATCH")
    _require(task053.get("result") == "PASS_TASK053_METADATA_SAFE_INVENTORY_REDESIGN_NO_SOURCE_READ", "TASK054_TASK053_RESULT_MISMATCH")
    contract = task053.get("redesigned_inventory_contract") or {}
    _require(contract.get("max_candidate_records") == 25, "TASK054_UPSTREAM_BOUND_MISMATCH")
    _require(contract.get("candidate_basis_required") == "METADATA_ONLY", "TASK054_UPSTREAM_BASIS_MISMATCH")
    _require(contract.get("stop_on_any_content_hydration") is True, "TASK054_UPSTREAM_HYDRATION_STOP_WEAKENED")
    allowed = set(contract.get("allowed_surfaces") or [])
    _require(allowed == {"DRIVE_SEARCH_METADATA_ONLY", "DRIVE_LIST_METADATA_ONLY"}, "TASK054_UPSTREAM_SURFACES_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK054_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga", "TASK054_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK054_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK054_BLANKET_AUTH_FORBIDDEN")

    execution = evidence.get("execution") or {}
    _require(execution.get("metadata_search_calls") == 10, "TASK054_SEARCH_COUNT_MISMATCH")
    _require(execution.get("metadata_list_calls") == 0, "TASK054_LIST_COUNT_MISMATCH")
    _require(execution.get("all_searches_used_explicit_item_type_document") is True, "TASK054_METADATA_SURFACE_NOT_EXPLICIT")
    _require(execution.get("best_effort_fetch") is False, "TASK054_BEST_EFFORT_FETCH_FORBIDDEN")
    _require(execution.get("content_hydration_observed") is False, "TASK054_CONTENT_HYDRATION_OBSERVED")

    candidates = evidence.get("candidate_records") or []
    _require(1 <= len(candidates) <= 25, "TASK054_CANDIDATE_COUNT_OUT_OF_BOUNDS")
    ids = [candidate.get("drive_file_id") for candidate in candidates]
    _require(len(ids) == len(set(ids)), "TASK054_DUPLICATE_CANDIDATE_ID")
    _require([candidate.get("rank") for candidate in candidates] == list(range(1, len(candidates) + 1)), "TASK054_RANK_SEQUENCE_MISMATCH")
    for candidate in candidates:
        _require(candidate.get("basis") == "METADATA_ONLY", "TASK054_NON_METADATA_CANDIDATE_BASIS")
        _require(bool(candidate.get("drive_file_id")) and bool(candidate.get("title")), "TASK054_CANDIDATE_ID_OR_TITLE_MISSING")

    primary = candidates[0]
    _require(primary.get("drive_file_id") == PRIMARY_ID, "TASK054_PRIMARY_ID_MISMATCH")
    _require(primary.get("title") == PRIMARY_TITLE, "TASK054_PRIMARY_TITLE_MISMATCH")
    _require(primary.get("candidate_family") == "POTENTIAL_DETAILED_BUDGET_EXECUTION_OR_BALANCETE", "TASK054_PRIMARY_FAMILY_MISMATCH")

    selection = evidence.get("selection") or {}
    _require(selection.get("candidate_count") == len(candidates), "TASK054_SELECTION_COUNT_MISMATCH")
    _require(selection.get("candidate_inventory_passed") is True, "TASK054_INVENTORY_NOT_PASSED")
    _require(selection.get("primary_candidate_drive_file_id") == PRIMARY_ID, "TASK054_SELECTION_PRIMARY_ID_MISMATCH")
    _require(selection.get("secondary_candidate_count") == len(candidates) - 1, "TASK054_SECONDARY_COUNT_MISMATCH")

    effects = evidence.get("effects") or {}
    _require(effects.get("drive_metadata_or_index_searches") == 10, "TASK054_EFFECT_SEARCH_COUNT_MISMATCH")
    _require(effects.get("drive_list_calls") == 0, "TASK054_EFFECT_LIST_COUNT_MISMATCH")
    for key in ("source_content_reads", "public_source_network", "drive_write", "ocr", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"TASK054_EFFECT_{key.upper()}_NONZERO")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("candidate_inventory_passed") is True, "TASK054_PROMOTION_INVENTORY_FLAG_MISMATCH")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK054_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK054_EITI_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK054_DOWNSTREAM_PROMOTION_ENABLED")

    next_gate = evidence.get("next_bounded_gate") or {}
    _require(next_gate.get("name") == NEXT_GATE, "TASK054_NEXT_GATE_MISMATCH")
    _require(next_gate.get("selected_source_drive_file_id") == PRIMARY_ID, "TASK054_NEXT_GATE_SOURCE_ID_MISMATCH")
    _require(next_gate.get("selected_source_basis") == "METADATA_ONLY", "TASK054_NEXT_GATE_BASIS_MISMATCH")
    _require(next_gate.get("fresh_owner_authorization_required") is True, "TASK054_FRESH_AUTH_NOT_REQUIRED")
    _require(next_gate.get("source_content_read_authorized") is False, "TASK054_SOURCE_READ_PREAUTHORIZED")

    _require(evidence.get("result") == RESULT, "TASK054_RESULT_MISMATCH")

    return {
        "status": RESULT,
        "candidate_count": len(candidates),
        "primary_candidate_drive_file_id": PRIMARY_ID,
        "source_content_reads": 0,
        "new_remote_data_write": False,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "next_gate": NEXT_GATE,
    }
