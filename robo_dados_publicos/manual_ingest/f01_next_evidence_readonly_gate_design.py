"""Fail-closed T0 review for the next F01 existing-custody read-only evidence gate."""
from __future__ import annotations

from typing import Any

TASK = "TASK_044_F01_NEXT_EVIDENCE_READONLY_GATE_DESIGN"
MODE = "T0_OFFLINE_DESIGN_ONLY"
BASE_SHA = "eaeabe210f72e60eeb497702b6a1fe69500759bb"
PPA_FILE_ID = "1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj"
PPA_SHA = "cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a"
LOA_FILE_ID = "1bRpmMxacX16P1tJBvam-55OOPTYuQnIA"
LOA_SHA = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
PPA_PAGES = [15, 16]
LOA_PAGES = [153, 154, 155, 156, 170, 171, 172, 173, 174, 175]


class Task044Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task044Error(code)


def validate_task044_design(evidence: dict[str, Any], task043: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK044_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK044_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK044_BASE_SHA_MISMATCH")

    _require(task043.get("task") == "TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION", "TASK044_TASK043_ID_MISMATCH")
    _require(task043.get("result") == "PASS_TASK043_SCOPED_BUDGET_LAW_RECONCILIATION_NO_FINANCIAL_IDENTITY_PROMOTION", "TASK044_TASK043_RESULT_MISMATCH")
    promotion43 = task043.get("promotion") or {}
    _require(promotion43.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK044_TASK043_F01_STATUS_MISMATCH")
    _require(promotion43.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK044_TASK043_EITI_STATUS_MISMATCH")

    problem = evidence.get("problem") or {}
    _require(problem.get("action_2720") == "PROGRAM_ACTION_KEY_CONTINUITY_PROVEN_NO_FINANCIAL_IDENTITY", "TASK044_2720_PROBLEM_DRIFT")
    _require(problem.get("action_2690") == "REVIEW_REQUIRED_BLOCKED", "TASK044_2690_PROBLEM_DRIFT")
    _require(problem.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK044_EITI_PROBLEM_DRIFT")

    minimization = evidence.get("evidence_minimization") or {}
    _require(minimization.get("ppa_pages") == PPA_PAGES, "TASK044_PPA_PAGE_SET_DRIFT")
    _require(minimization.get("loa_pages") == LOA_PAGES, "TASK044_LOA_PAGE_SET_DRIFT")
    _require(minimization.get("ldo_additional_read_needed") is False, "TASK044_UNNEEDED_LDO_READ_ADDED")
    _require(minimization.get("max_selected_pages") == 12, "TASK044_PAGE_BUDGET_MISMATCH")
    _require(len(PPA_PAGES) + len(LOA_PAGES) == 12, "TASK044_INTERNAL_PAGE_BUDGET_MISMATCH")

    future = evidence.get("future_readonly_contract") or {}
    _require(future.get("tier") == "T1_EXISTING_CUSTODY_READONLY", "TASK044_FUTURE_TIER_MISMATCH")
    _require(future.get("authorization_required") is True, "TASK044_AUTH_REQUIREMENT_REMOVED")
    _require(future.get("authorization_granted") is False, "TASK044_PREAUTHORIZED_FUTURE_READ_FORBIDDEN")
    _require(future.get("authorized_against_sha") is None, "TASK044_PREPINNED_AUTH_SHA_FORBIDDEN")
    files = future.get("drive_files") or []
    _require(len(files) == 2, "TASK044_DRIVE_FILE_COUNT_MISMATCH")
    by_family = {row.get("family"): row for row in files}
    ppa = by_family.get("PPA") or {}
    loa = by_family.get("LOA") or {}
    _require((ppa.get("file_id"), ppa.get("source_sha256"), ppa.get("pages")) == (PPA_FILE_ID, PPA_SHA, PPA_PAGES), "TASK044_PPA_TARGET_DRIFT")
    _require((loa.get("file_id"), loa.get("source_sha256"), loa.get("pages")) == (LOA_FILE_ID, LOA_SHA, LOA_PAGES), "TASK044_LOA_TARGET_DRIFT")
    for key in ("source_network", "drive_write", "ocr", "retry", "pagination", "bronze", "silver_write", "gold", "serving", "publication"):
        _require(future.get(key) is False, f"TASK044_FUTURE_{key.upper()}_MUST_REMAIN_FALSE")

    questions = evidence.get("questions_to_answer") or []
    _require(len(questions) == 3, "TASK044_QUESTION_SET_MISMATCH")
    _require(any("2690" in q and "PPA" in q for q in questions), "TASK044_2690_QUESTION_MISSING")
    _require(any("budget unit" in q.lower() and "expense nature" in q.lower() for q in questions), "TASK044_LOA_KEY_FIELD_QUESTION_MISSING")

    policy = evidence.get("promotion_policy") or {}
    _require(policy.get("missing_field_behavior") == "UNKNOWN_NOT_INFERRED", "TASK044_MISSING_FIELD_INFERENCE_WEAKENED")
    _require(policy.get("material_text_visual_divergence") == "REVIEW_STOP", "TASK044_DIVERGENCE_POLICY_WEAKENED")
    _require(policy.get("review_required_row_behavior") == "NO_PROMOTION_UNTIL_DIRECT_SOURCE_RESOLUTION", "TASK044_REVIEW_ROW_POLICY_WEAKENED")
    for key in ("financial_identity_from_same_code_label_or_amount", "program_2001_total_attribution_to_eiti", "execution_stage_from_loa", "gold_authorized"):
        _require(policy.get(key) is False, f"TASK044_POLICY_{key.upper()}_WEAKENED")

    expected_effects = {
        "source_network": 0, "drive_read": 0, "drive_write": 0, "ocr": 0,
        "bronze": 0, "silver": 0, "gold": 0, "serving": 0, "publication": 0,
    }
    _require((evidence.get("effects") or {}) == expected_effects, "TASK044_EFFECTS_MISMATCH")
    _require(evidence.get("result") == "PASS_TASK044_NEXT_EVIDENCE_READONLY_GATE_DESIGNED_NOT_AUTHORIZED", "TASK044_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK044_NEXT_EVIDENCE_READONLY_GATE_DESIGN_REVIEW",
        "future_tier": "T1_EXISTING_CUSTODY_READONLY",
        "selected_pages": 12,
        "authorization_required": True,
        "authorization_granted": False,
        "gold_authorized": False,
    }
