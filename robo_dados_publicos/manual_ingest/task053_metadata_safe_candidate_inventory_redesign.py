"""Fail-closed validation for TASK 053 metadata-safe inventory redesign."""
from __future__ import annotations

from typing import Any

TASK = "TASK_053_METADATA_SAFE_CANDIDATE_INVENTORY_REDESIGN"
MODE = "T0_OFFLINE_METADATA_SAFE_INVENTORY_REDESIGN"
BASE_SHA = "ca9356000a2d0312283c17b2769009eb6935a26e"
RESULT = "PASS_TASK053_METADATA_SAFE_INVENTORY_REDESIGN_NO_SOURCE_READ"


class Task053Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task053Error(code)


def validate_task053_evidence(evidence: dict[str, Any], task052: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK053_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK053_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK053_BASE_SHA_MISMATCH")

    _require(task052.get("task") == "TASK_052_EXISTING_CUSTODY_GRANULAR_SOURCE_INVENTORY", "TASK053_TASK052_ID_MISMATCH")
    _require(task052.get("result") == "STOP_TASK052_SOURCE_CONTENT_READ_BOUNDARY_BREACHED_NO_PROMOTION", "TASK053_UPSTREAM_STOP_MISMATCH")
    next_gate = task052.get("next_bounded_gate") or {}
    _require(next_gate.get("name") == TASK, "TASK053_UPSTREAM_GATE_MISMATCH")
    _require(next_gate.get("new_authorization_required_before_any_SOURCE_CONTENT_READ") is True, "TASK053_UPSTREAM_AUTH_BOUNDARY_WEAKENED")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK053_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga", "TASK053_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK053_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK053_BLANKET_AUTH_FORBIDDEN")

    upstream = evidence.get("upstream") or {}
    _require(upstream.get("candidate_seed_drive_file_id") == "1PTAnH-LL_8fvS7TsVuHSci5dBDKFLQTS", "TASK053_SEED_ID_MISMATCH")
    _require(upstream.get("candidate_seed_title") == "05 - Maio_despesa.pdf", "TASK053_SEED_TITLE_MISMATCH")
    _require(upstream.get("candidate_seed_basis") == "METADATA_TITLE_ONLY", "TASK053_SEED_BASIS_MISMATCH")
    _require(upstream.get("hydrated_content_reuse_allowed") is False, "TASK053_HYDRATED_CONTENT_REUSE_FORBIDDEN")

    contract = evidence.get("redesigned_inventory_contract") or {}
    _require(contract.get("max_candidate_records") == 25, "TASK053_BOUND_MISMATCH")
    allowed = set(contract.get("allowed_surfaces") or [])
    _require(allowed == {"DRIVE_SEARCH_METADATA_ONLY", "DRIVE_LIST_METADATA_ONLY"}, "TASK053_ALLOWED_SURFACES_MISMATCH")
    forbidden = set(contract.get("forbidden_operations") or [])
    for required in (
        "DRIVE_FETCH",
        "DRIVE_CONTENT_READ",
        "DRIVE_FILE_DOWNLOAD",
        "OCR",
        "PUBLIC_SOURCE_NETWORK",
        "DRIVE_WRITE",
        "BRONZE_WRITE",
        "SILVER_WRITE",
        "GOLD_WRITE",
        "SERVING",
        "PUBLICATION",
    ):
        _require(required in forbidden, f"TASK053_FORBIDDEN_OPERATION_MISSING_{required}")
    _require(contract.get("candidate_basis_required") == "METADATA_ONLY", "TASK053_CANDIDATE_BASIS_WEAKENED")
    _require(contract.get("source_content_must_not_influence_classification") is True, "TASK053_CONTENT_CLASSIFICATION_BOUNDARY_WEAKENED")
    _require(contract.get("stop_on_any_content_hydration") is True, "TASK053_HYDRATION_STOP_WEAKENED")
    _require(contract.get("promotion_allowed") is False, "TASK053_PROMOTION_POLICY_WEAKENED")

    plan = evidence.get("execution_plan") or {}
    _require(plan.get("future_gate") == "TASK_054_METADATA_SAFE_EXISTING_CUSTODY_INVENTORY_EXECUTION", "TASK053_FUTURE_GATE_MISMATCH")
    _require(plan.get("source_content_read_authorized") is False, "TASK053_SOURCE_READ_AUTH_FORBIDDEN")
    _require(plan.get("fresh_owner_authorization_required_before_any_source_content_read") is True, "TASK053_FRESH_AUTH_REQUIREMENT_MISSING")

    effects = evidence.get("effects") or {}
    for key in (
        "drive_metadata_or_index_searches",
        "drive_list_calls",
        "source_content_reads",
        "public_source_network",
        "drive_write",
        "ocr",
        "bronze",
        "silver",
        "gold",
        "serving",
        "publication",
    ):
        _require(effects.get(key) == 0, f"TASK053_EFFECT_{key.upper()}_NONZERO")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("metadata_safe_inventory_contract_ready") is True, "TASK053_CONTRACT_NOT_READY")
    _require(promotion.get("candidate_inventory_executed") is False, "TASK053_EXECUTION_OCCURRED")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK053_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK053_EITI_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK053_DOWNSTREAM_PROMOTION_ENABLED")
    _require(evidence.get("result") == RESULT, "TASK053_RESULT_MISMATCH")

    return {
        "status": RESULT,
        "max_candidate_records": 25,
        "allowed_surfaces": sorted(allowed),
        "source_content_reads": 0,
        "new_remote_data_write": False,
        "future_gate": plan["future_gate"],
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
    }
