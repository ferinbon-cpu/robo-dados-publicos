"""Fail-closed validation for TASK 055 bounded selected-source read."""
from __future__ import annotations

from typing import Any

TASK = "TASK_055_F01_SELECTED_GRANULAR_SOURCE_BOUNDED_CONTENT_READ"
MODE = "T1_EXISTING_CUSTODY_SINGLE_SOURCE_CONTENT_READ"
BASE_SHA = "a030150edebe1c9c9d9ef3d67df369b54be1d46f"
SELECTED_ID = "1PTAnH-LL_8fvS7TsVuHSci5dBDKFLQTS"
RESULT = "PASS_TASK055_SELECTED_SOURCE_READ_NEGATIVE_FOR_EITI_GRANULARITY_NO_PROMOTION"


class Task055Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task055Error(code)


def validate_task055_evidence(evidence: dict[str, Any], task054: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK055_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK055_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK055_BASE_SHA_MISMATCH")

    _require(task054.get("task") == "TASK_054_METADATA_SAFE_EXISTING_CUSTODY_INVENTORY_EXECUTION", "TASK055_TASK054_ID_MISMATCH")
    _require(task054.get("result") == "PASS_TASK054_METADATA_SAFE_INVENTORY_CANDIDATES_SELECTED_NO_SOURCE_READ", "TASK055_TASK054_RESULT_MISMATCH")
    upstream_gate = task054.get("next_bounded_gate") or {}
    _require(upstream_gate.get("name") == TASK, "TASK055_UPSTREAM_GATE_MISMATCH")
    _require(upstream_gate.get("selected_source_drive_file_id") == SELECTED_ID, "TASK055_UPSTREAM_SOURCE_MISMATCH")
    _require(upstream_gate.get("fresh_owner_authorization_required") is True, "TASK055_UPSTREAM_AUTH_REQUIREMENT_WEAKENED")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK055_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga", "TASK055_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK055_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK055_BLANKET_AUTH_FORBIDDEN")

    contract = evidence.get("read_contract") or {}
    _require(contract.get("max_source_content_reads") == 1, "TASK055_READ_BOUND_MISMATCH")
    _require(contract.get("allowed_drive_file_ids") == [SELECTED_ID], "TASK055_ALLOWED_SOURCE_SET_MISMATCH")
    _require(contract.get("public_source_network_allowed") is False, "TASK055_NETWORK_POLICY_WEAKENED")
    _require(contract.get("drive_write_allowed") is False, "TASK055_DRIVE_WRITE_POLICY_WEAKENED")
    _require(contract.get("ocr_allowed") is False, "TASK055_OCR_POLICY_WEAKENED")
    _require(contract.get("promotion_allowed") is False, "TASK055_PROMOTION_POLICY_WEAKENED")

    source = evidence.get("observed_source") or {}
    _require(source.get("drive_file_id") == SELECTED_ID, "TASK055_OBSERVED_SOURCE_MISMATCH")
    _require(source.get("title") == "05 - Maio_despesa.pdf", "TASK055_OBSERVED_TITLE_MISMATCH")
    _require(source.get("report_title") == "BALANCETE SINTETICO DA DESPESA EMPENHADA POR ELEMENTO", "TASK055_REPORT_TYPE_MISMATCH")
    _require(source.get("granularity") == "ECONOMIC_ELEMENT_AGGREGATE", "TASK055_GRANULARITY_MISMATCH")
    _require(source.get("execution_stage_explicitly_observed") == "EMPENHADA", "TASK055_STAGE_MISMATCH")

    checks = evidence.get("eiti_granularity_checks") or {}
    for key in (
        "educacao_marker_found",
        "eiti_or_tempo_integral_marker_found",
        "program_marker_found",
        "action_marker_found",
        "liquidado_marker_found",
        "pago_marker_found",
        "stable_policy_to_accounting_key_found",
        "can_attribute_amounts_specifically_to_eiti",
    ):
        _require(checks.get(key) is False, f"TASK055_UNEXPECTED_{key.upper()}")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("content_read_completed_as_authorized") is True, "TASK055_READ_NOT_COMPLETED")
    _require(interpretation.get("negative_evidence_is_not_absence_of_eiti_spending") is True, "TASK055_NEGATIVE_EVIDENCE_OVERCLAIM")

    effects = evidence.get("effects") or {}
    _require(effects.get("source_content_reads") == 1, "TASK055_SOURCE_READ_COUNT_MISMATCH")
    _require(effects.get("other_source_content_reads") == 0, "TASK055_OTHER_SOURCE_READ_OCCURRED")
    for key in ("public_source_network", "drive_write", "ocr", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"TASK055_EFFECT_{key.upper()}_NONZERO")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("selected_source_read_passed") is True, "TASK055_READ_GATE_NOT_PASSED")
    _require(promotion.get("selected_source_proves_eiti_financial_identity") is False, "TASK055_EITI_IDENTITY_FALSE_POSITIVE")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK055_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK055_EITI_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK055_DOWNSTREAM_PROMOTION_ENABLED")

    next_gate = evidence.get("next_bounded_gate") or {}
    _require(next_gate.get("name") == "TASK_056_F01_SECONDARY_EDUCATION_SOURCE_BOUNDED_CONTENT_READ", "TASK055_NEXT_GATE_MISMATCH")
    _require(next_gate.get("selected_drive_file_id") == "17Fl8opb1pkqdFa485-bkQR3j6LnApnE-", "TASK055_NEXT_SOURCE_MISMATCH")
    _require(next_gate.get("fresh_owner_authorization_required") is True, "TASK055_NEXT_AUTH_REQUIREMENT_WEAKENED")

    _require(evidence.get("result") == RESULT, "TASK055_RESULT_MISMATCH")

    return {
        "status": RESULT,
        "source_content_reads": 1,
        "selected_source_proves_eiti_financial_identity": False,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "next_gate": next_gate["name"],
    }
