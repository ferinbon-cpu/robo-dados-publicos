"""Fail-closed validation for TASK 052 existing-custody metadata inventory."""
from __future__ import annotations

from typing import Any

TASK = "TASK_052_EXISTING_CUSTODY_GRANULAR_SOURCE_INVENTORY"
MODE = "T1_EXISTING_CUSTODY_METADATA_OR_MANIFEST_INVENTORY"
BASE_SHA = "e4c88711fcc88913210def0c3947237e7a1c60cf"
RESULT = "STOP_TASK052_SOURCE_CONTENT_READ_BOUNDARY_BREACHED_NO_PROMOTION"


class Task052Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task052Error(code)


def validate_task052_evidence(evidence: dict[str, Any], task051: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK052_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK052_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK052_BASE_SHA_MISMATCH")
    _require(task051.get("task") == "TASK_051_F01_EITI_GRANULAR_EXECUTION_SOURCE_SELECTION", "TASK052_TASK051_ID_MISMATCH")
    gate = task051.get("next_bounded_gate") or {}
    _require(gate.get("name") == TASK, "TASK052_UPSTREAM_GATE_MISMATCH")
    _require(gate.get("max_candidate_records") == 25, "TASK052_UPSTREAM_BOUND_MISMATCH")
    _require(gate.get("no_source_content_read") is True, "TASK052_UPSTREAM_CONTENT_BOUNDARY_WEAKENED")
    _require(gate.get("no_network") is True and gate.get("no_drive_write") is True, "TASK052_UPSTREAM_EFFECT_BOUNDARY_WEAKENED")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK052_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga autorizado", "TASK052_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK052_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK052_BLANKET_AUTH_FORBIDDEN")

    contract = evidence.get("inventory_contract") or {}
    _require(contract.get("max_candidate_records") == 25, "TASK052_BOUND_MISMATCH")
    _require(contract.get("source_content_read_allowed") is False, "TASK052_SOURCE_CONTENT_READ_POLICY_WEAKENED")
    _require(contract.get("public_source_network_allowed") is False, "TASK052_NETWORK_POLICY_WEAKENED")
    _require(contract.get("drive_write_allowed") is False, "TASK052_DRIVE_WRITE_POLICY_WEAKENED")
    _require(contract.get("promotion_allowed") is False, "TASK052_PROMOTION_POLICY_WEAKENED")

    candidates = evidence.get("candidate_records") or []
    _require(len(candidates) <= 25, "TASK052_CANDIDATE_BOUND_EXCEEDED")
    _require(len(candidates) == 1, "TASK052_RECORDED_CANDIDATE_COUNT_MISMATCH")
    candidate = candidates[0]
    _require(candidate.get("drive_file_id") == "1PTAnH-LL_8fvS7TsVuHSci5dBDKFLQTS", "TASK052_CANDIDATE_ID_MISMATCH")
    _require(candidate.get("title") == "05 - Maio_despesa.pdf", "TASK052_CANDIDATE_TITLE_MISMATCH")
    _require(candidate.get("basis") == "METADATA_TITLE_ONLY", "TASK052_CANDIDATE_BASIS_MISMATCH")
    _require(candidate.get("content_used_for_candidate_classification") is False, "TASK052_CONTENT_USED_FOR_CLASSIFICATION")

    incident = evidence.get("boundary_incident") or {}
    _require(incident.get("occurred") is True, "TASK052_INCIDENT_MUST_BE_RECORDED")
    _require(incident.get("source_content_read_count") == 1, "TASK052_INCIDENT_READ_COUNT_MISMATCH")
    _require(incident.get("content_used_for_task052_finding") is False, "TASK052_INCIDENT_CONTENT_PROMOTED")
    _require(incident.get("response") == "FAIL_CLOSED_STOP_NO_PROMOTION", "TASK052_INCIDENT_RESPONSE_WEAKENED")

    effects = evidence.get("effects") or {}
    _require(effects.get("source_content_reads") == 1, "TASK052_SOURCE_CONTENT_READ_COUNT_MISMATCH")
    for key in ("public_source_network", "drive_write", "ocr", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"TASK052_EFFECT_{key.upper()}_NONZERO")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("candidate_inventory_passed") is False, "TASK052_PASS_FORBIDDEN_AFTER_BOUNDARY_BREACH")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK052_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK052_EITI_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK052_DOWNSTREAM_PROMOTION_ENABLED")
    _require(evidence.get("result") == RESULT, "TASK052_RESULT_MISMATCH")

    return {
        "status": RESULT,
        "candidate_count": 1,
        "metadata_seed_drive_file_id": candidate["drive_file_id"],
        "source_content_reads": 1,
        "new_remote_data_write": False,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
    }
