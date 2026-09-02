"""Fail-closed reconciliation review for scoped F01 PPA/LDO/LOA Silver evidence.

TASK 043 is T0/offline. It may establish bounded program/action continuity classes,
but it must never infer financial identity from thematic, code, label, or amount
alignment alone.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

TASK = "TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION"
MODE = "T0_OFFLINE_SCOPED_RECONCILIATION_DESIGN_AND_REVIEW"
BASE_SHA = "013ed0fcd92051adfc1b67a0e85fc0792f51eb88"
LOA_SHA = "3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c"
PPA_SHA = "0cba09dade1c09224e549e817a859c63edb12a6fb0a5223c5ddb8aa5fe6dc730"
LDO_SHA = "4719631a3dd476efe8c760f2b9ce07eba15d678c85b56e95345af70237f02182"
TASK042_RESULT = "PASS_TASK042_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_VERIFIED"


class Task043Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task043Error(code)


def _relation_by_id(evidence: dict[str, Any], relation_id: str) -> dict[str, Any]:
    rows = evidence.get("reconciliation_ledger") or []
    matches = [row for row in rows if row.get("relation_id") == relation_id]
    _require(len(matches) == 1, f"TASK043_RELATION_{relation_id}_COUNT_MISMATCH")
    return matches[0]


def _validate_upstream(task039: dict[str, Any], task041: dict[str, Any], task042: dict[str, Any]) -> None:
    _require(task039.get("task") == "TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW", "TASK043_TASK039_ID_MISMATCH")
    _require(task039.get("candidate_payload_sha256") == LOA_SHA, "TASK043_TASK039_LOA_HASH_MISMATCH")
    loa = task039.get("candidate_payload") or {}
    _require(loa.get("contract") == "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE_SILVER_V1", "TASK043_LOA_CONTRACT_MISMATCH")
    loa_actions = loa.get("validated_action_records") or []
    _require(len(loa_actions) == 2, "TASK043_LOA_ACTION_COUNT_MISMATCH")
    expected_loa = {
        "12.362.2001.2690": ("TRANSPORTE ESCOLAR", "6152000.00", False),
        "12.306.2001.2720": ("ALIMENTACAO ESCOLAR", "28000000.00", False),
    }
    for row in loa_actions:
        key = row.get("action_code")
        _require(key in expected_loa, "TASK043_LOA_ACTION_KEY_DRIFT")
        label, amount, eiti = expected_loa[key]
        _require((row.get("label"), row.get("amount_brl"), row.get("eiti_specific")) == (label, amount, eiti), "TASK043_LOA_ACTION_VALUE_DRIFT")

    _require(task041.get("task") == "TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW", "TASK043_TASK041_ID_MISMATCH")
    _require(task041.get("ppa_candidate_sha256") == PPA_SHA, "TASK043_TASK041_PPA_HASH_MISMATCH")
    _require(task041.get("ldo_candidate_sha256") == LDO_SHA, "TASK043_TASK041_LDO_HASH_MISMATCH")
    ppa = task041.get("ppa_candidate") or {}
    actions = ((ppa.get("program_2001") or {}).get("selected_actions") or [])
    _require(len(actions) == 3, "TASK043_PPA_ACTION_COUNT_MISMATCH")
    action2720 = [row for row in actions if row.get("action_code") == "2720"]
    _require(len(action2720) == 1, "TASK043_PPA_2720_COUNT_MISMATCH")
    a2720 = action2720[0]
    _require(
        (a2720.get("label"), a2720.get("function"), a2720.get("subfunction"), a2720.get("2026"), a2720.get("units"), a2720.get("eiti_specific"))
        == ("ALIMENTACAO ESCOLAR", "12", "306", 28000, "R$ milhares medios/2025", False),
        "TASK043_PPA_2720_DRIFT",
    )
    excluded = ((ppa.get("program_2001") or {}).get("excluded_review_rows") or [])
    _require(len(excluded) == 1, "TASK043_PPA_EXCLUDED_ROW_COUNT_MISMATCH")
    _require(
        excluded[0].get("action_code") == "2690"
        and excluded[0].get("education_level") == "ENSINO MEDIO_E_SUPERIOR"
        and excluded[0].get("status") == "PARSER_REVIEW_REQUIRED"
        and excluded[0].get("promoted") is False,
        "TASK043_PPA_2690_REVIEW_ROW_DRIFT",
    )

    _require(task042.get("task") == "TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK", "TASK043_TASK042_ID_MISMATCH")
    _require(task042.get("result") == TASK042_RESULT, "TASK043_TASK042_RESULT_MISMATCH")
    _require((task042.get("ppa") or {}).get("sha256") == PPA_SHA, "TASK043_TASK042_PPA_HASH_MISMATCH")
    _require((task042.get("ldo") or {}).get("sha256") == LDO_SHA, "TASK043_TASK042_LDO_HASH_MISMATCH")
    _require((task042.get("ppa") or {}).get("readback", {}).get("byte_identity") is True, "TASK043_TASK042_PPA_READBACK_MISSING")
    _require((task042.get("ldo") or {}).get("readback", {}).get("byte_identity") is True, "TASK043_TASK042_LDO_READBACK_MISSING")


def validate_task043_evidence(
    evidence: dict[str, Any],
    task039: dict[str, Any],
    task041: dict[str, Any],
    task042: dict[str, Any],
) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK043_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK043_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK043_BASE_SHA_MISMATCH")
    _validate_upstream(task039, task041, task042)

    scope = evidence.get("input_scope") or {}
    for family, expected_hash in (("loa", LOA_SHA), ("ppa", PPA_SHA), ("ldo", LDO_SHA)):
        item = scope.get(family) or {}
        _require(item.get("candidate_sha256") == expected_hash, f"TASK043_{family.upper()}_INPUT_HASH_MISMATCH")
        _require(item.get("status") == "SILVER_SCOPED_PARTIAL_VALIDATED", f"TASK043_{family.upper()}_INPUT_STATUS_MISMATCH")

    ldo = _relation_by_id(evidence, "F01_LDO_FRAMEWORK_CONTEXT_2026")
    _require(ldo.get("classification") == "FRAMEWORK_CONTEXT_ONLY_NO_ITEM_LEVEL_LINK", "TASK043_LDO_CLASSIFICATION_WEAKENED")
    _require(ldo.get("financial_identity") is False, "TASK043_LDO_FINANCIAL_IDENTITY_FORBIDDEN")

    r2720 = _relation_by_id(evidence, "F01_PPA_LOA_PROGRAM2001_ACTION2720_12_306")
    _require(
        r2720.get("classification") == "PROGRAM_ACTION_KEY_CONTINUITY_PROVEN_AMOUNT_SCALE_ALIGNMENT_OBSERVED_NO_FINANCIAL_IDENTITY",
        "TASK043_2720_CLASSIFICATION_MISMATCH",
    )
    align = r2720.get("key_alignment") or {}
    _require(all(align.get(key) is True for key in ("program", "action", "function", "subfunction", "label")), "TASK043_2720_KEY_ALIGNMENT_INCOMPLETE")
    src = r2720.get("from") or {}
    dst = r2720.get("to") or {}
    _require((src.get("program_code"), src.get("action_code"), src.get("function"), src.get("subfunction")) == ("2001", "2720", "12", "306"), "TASK043_2720_PPA_KEY_DRIFT")
    _require(dst.get("loa_key") == "12.306.2001.2720", "TASK043_2720_LOA_KEY_DRIFT")
    diagnostic = r2720.get("amount_diagnostic") or {}
    scaled = Decimal(str(src.get("ppa_2026_value"))) * Decimal("1000")
    _require(str(scaled.quantize(Decimal("0.01"))) == diagnostic.get("ppa_value_times_1000_brl"), "TASK043_2720_SCALE_DIAGNOSTIC_MISMATCH")
    _require(diagnostic.get("matches_loa_amount_numerically") is True, "TASK043_2720_NUMERIC_ALIGNMENT_LOST")
    _require(diagnostic.get("identity_inference_allowed") is False, "TASK043_2720_NUMERIC_IDENTITY_FORBIDDEN")
    _require(r2720.get("financial_identity") is False, "TASK043_2720_FINANCIAL_IDENTITY_FORBIDDEN")
    _require(r2720.get("eiti_specific_in_ppa") is False and r2720.get("eiti_specific_in_loa") is False, "TASK043_2720_EITI_SCOPE_WEAKENED")

    r2690 = _relation_by_id(evidence, "F01_PPA_LOA_PROGRAM2001_ACTION2690_12_362")
    _require(r2690.get("classification") == "REVIEW_REQUIRED_BLOCKED_RELEVANT_PPA_ROW_UNPROMOTED", "TASK043_2690_CLASSIFICATION_WEAKENED")
    _require((r2690.get("from") or {}).get("ppa_row_status") == "PARSER_REVIEW_REQUIRED", "TASK043_2690_REVIEW_STATUS_LOST")
    _require((r2690.get("from") or {}).get("ppa_row_promoted") is False, "TASK043_2690_REVIEW_ROW_PROMOTED")
    _require(r2690.get("promoted") is False and r2690.get("financial_identity") is False, "TASK043_2690_PROMOTION_FORBIDDEN")

    eiti = _relation_by_id(evidence, "F01_EITI_FINANCIAL_IDENTITY")
    _require(eiti.get("classification") == "EVIDENCIA_INSUFICIENTE", "TASK043_EITI_CLASSIFICATION_WEAKENED")
    required_chain = eiti.get("required_chain") or []
    _require(required_chain == [
        "indicator_or_target", "program", "explicit_action_or_subaction", "budget_unit",
        "funding_source_or_destination", "expense_nature", "appropriation", "committed",
        "liquidated", "paid",
    ], "TASK043_EITI_REQUIRED_CHAIN_DRIFT")
    _require(eiti.get("financial_identity") is False, "TASK043_EITI_FINANCIAL_IDENTITY_FORBIDDEN")

    tables = evidence.get("global_loa_tables") or {}
    _require(tables.get("pages") == [480, 481] and tables.get("validated") is True, "TASK043_GLOBAL_TABLE_PIN_MISMATCH")
    _require(tables.get("role") == "GLOBAL_FISCAL_CONTEXT_ONLY" and tables.get("eiti_attribution_allowed") is False, "TASK043_GLOBAL_TABLE_EITI_ATTRIBUTION_FORBIDDEN")

    guardrails = evidence.get("guardrails") or {}
    for key in (
        "program_2001_total_attribution_to_eiti", "same_action_code_as_financial_identity",
        "same_or_scaled_amount_as_financial_identity", "review_required_row_promotion",
        "mde_fundeb_compliance_conclusion", "fiscal_compliance_conclusion", "causal_inference",
        "gold_authorized", "serving_authorized", "publication_authorized",
    ):
        _require(guardrails.get(key) is False, f"TASK043_GUARDRAIL_{key.upper()}_WEAKENED")

    expected_effects = {
        "source_network": 0, "drive_read": 0, "drive_write": 0, "ocr": 0,
        "bronze": 0, "silver_write": 0, "gold": 0, "serving": 0, "publication": 0,
    }
    _require((evidence.get("effects") or {}) == expected_effects, "TASK043_EFFECTS_MISMATCH")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK043_F01_STATUS_MISMATCH")
    _require(promotion.get("new_silver") is False, "TASK043_NEW_SILVER_FORBIDDEN")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK043_DOWNSTREAM_PROMOTION_FORBIDDEN")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK043_EITI_PROMOTION_WEAKENED")
    _require(evidence.get("result") == "PASS_TASK043_SCOPED_BUDGET_LAW_RECONCILIATION_NO_FINANCIAL_IDENTITY_PROMOTION", "TASK043_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK043_SCOPED_BUDGET_LAW_RECONCILIATION_REVIEW",
        "f01_status": "SILVER_SCOPED_PARTIAL_VALIDATED",
        "action_2720": "PROGRAM_ACTION_KEY_CONTINUITY_PROVEN_NO_FINANCIAL_IDENTITY",
        "action_2690": "REVIEW_REQUIRED_BLOCKED",
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "gold_authorized": False,
    }
