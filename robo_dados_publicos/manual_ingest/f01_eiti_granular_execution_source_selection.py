"""Fail-closed T0 selection of the next evidence class for F01 EITI financial identity."""
from __future__ import annotations

from typing import Any

TASK = "TASK_051_F01_EITI_GRANULAR_EXECUTION_SOURCE_SELECTION"
MODE = "T0_OFFLINE_SOURCE_SELECTION_DESIGN"
BASE_SHA = "b9edc2390ab180828e0cbe2e89a28f0878b793b5"
TASK049_RESULT = "PASS_TASK049_EITI_ACTION_LINKAGE_CLOSURE_NO_EXPLICIT_ACTION_LABEL"
TASK050_RESULT = "PASS_TASK050_LOA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_VERIFIED"


class Task051Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task051Error(code)


def validate_task051_evidence(evidence: dict[str, Any], task049: dict[str, Any], task050: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK051_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK051_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK051_BASE_SHA_MISMATCH")

    _require(task049.get("result") == TASK049_RESULT, "TASK051_TASK049_RESULT_MISMATCH")
    conclusion49 = task049.get("conclusion") or {}
    _require(conclusion49.get("f01_action_label_search_status") == "CLOSED_NO_EXPLICIT_EITI_ACTION_LABEL_IN_PROGRAM_2001_TABLE", "TASK051_PPA_SEARCH_NOT_CLOSED")
    _require(conclusion49.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK051_TASK049_EITI_STATUS_MISMATCH")

    _require(task050.get("result") == TASK050_RESULT, "TASK051_TASK050_RESULT_MISMATCH")
    promotion50 = task050.get("promotion") or {}
    _require(promotion50.get("loa_silver_v2") is True, "TASK051_LOA_V2_NOT_PERSISTED")
    _require(promotion50.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK051_TASK050_EITI_STATUS_MISMATCH")

    closed = evidence.get("closed_paths") or {}
    for key in (
        "repeat_program_2001_action_label_search",
        "attribute_program_2001_total_to_eiti",
        "attribute_generic_action_2690_to_eiti",
        "attribute_generic_action_2720_to_eiti",
        "infer_identity_from_ppa_loa_amount_alignment",
    ):
        _require(closed.get(key) is False, f"TASK051_CLOSED_PATH_REOPENED_{key.upper()}")

    fields = set(evidence.get("identity_minimum_fields") or [])
    required_fields = {
        "EXPLICIT_EITI_OR_EQUIVALENT_POLICY_MARKER",
        "BUDGET_UNIT_OR_COST_CENTER",
        "PROGRAM_ACTION_OR_SUBACTION",
        "EXPENSE_NATURE_OR_ITEM",
        "FUNDING_SOURCE_OR_DESTINATION",
        "EXECUTION_DOCUMENT_OR_EVENT_ID",
        "COMMITTED_OR_EQUIVALENT",
        "LIQUIDATED_OR_EQUIVALENT",
        "PAID_OR_EQUIVALENT",
    }
    _require(fields == required_fields, "TASK051_IDENTITY_MINIMUM_FIELDS_MISMATCH")

    classes = evidence.get("candidate_source_classes") or []
    _require([row.get("priority") for row in classes] == [1, 2, 3], "TASK051_PRIORITY_SEQUENCE_MISMATCH")
    _require([row.get("source_class") for row in classes] == [
        "EXPLICIT_EITI_COST_CENTER_SUBACTION_OR_EXECUTION_TAG",
        "DETAILED_EDUCATION_BUDGET_EXECUTION_OR_BALANCETE_EDUCACAO",
        "EMPENHO_LIQUIDACAO_PAGAMENTO_DETAIL",
    ], "TASK051_SOURCE_CLASS_ORDER_MISMATCH")
    _require(all(row.get("automatic_identity") is False for row in classes), "TASK051_AUTOMATIC_IDENTITY_ENABLED")

    insufficient = set(evidence.get("not_sufficient_alone") or [])
    for required in ("PPA_PROGRAM_TOTAL", "LOA_GENERIC_ACTION_TOTAL", "DESCRIPTION_SIMILARITY_ONLY", "AMOUNT_EQUALITY_ONLY"):
        _require(required in insufficient, f"TASK051_INSUFFICIENT_GUARD_MISSING_{required}")

    gate = evidence.get("next_bounded_gate") or {}
    _require(gate.get("name") == "TASK_052_EXISTING_CUSTODY_GRANULAR_SOURCE_INVENTORY", "TASK051_NEXT_GATE_NAME_MISMATCH")
    _require(gate.get("scope") == "READ_ONLY_EXISTING_CUSTODY_METADATA_OR_MANIFEST_INVENTORY_ONLY", "TASK051_NEXT_GATE_SCOPE_MISMATCH")
    _require(gate.get("preferred_first_family") == "DETAILED_EDUCATION_BUDGET_EXECUTION_OR_BALANCETE_EDUCACAO", "TASK051_PREFERRED_FAMILY_MISMATCH")
    _require(gate.get("max_candidate_records") == 25, "TASK051_BOUND_MISMATCH")
    _require(gate.get("no_source_content_read") is True, "TASK051_SOURCE_CONTENT_READ_ENABLED")
    _require(gate.get("no_network") is True and gate.get("no_drive_write") is True, "TASK051_NEXT_GATE_EFFECT_WEAKENED")
    _require(gate.get("authorization_required_before_live_inventory") is True, "TASK051_AUTH_BOUNDARY_REMOVED")

    _require((evidence.get("effects") or {}) == {"source_network":0,"drive_read":0,"drive_write":0,"ocr":0,"bronze":0,"silver":0,"gold":0,"serving":0,"publication":0}, "TASK051_EFFECTS_MISMATCH")
    promotion = evidence.get("promotion") or {}
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK051_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK051_EITI_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK051_DOWNSTREAM_PROMOTION_ENABLED")
    _require(evidence.get("result") == "PASS_TASK051_GRANULAR_EXECUTION_SOURCE_SELECTION_DESIGNED_NO_REMOTE_EFFECT", "TASK051_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK051_GRANULAR_EXECUTION_SOURCE_SELECTION_REVIEW",
        "preferred_first_family": gate["preferred_first_family"],
        "next_gate": gate["name"],
        "authorization_required": True,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "gold": False,
    }
