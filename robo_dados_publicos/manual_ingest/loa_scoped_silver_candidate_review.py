"""Fail-closed T0 review for a scoped LOA 2026 Silver candidate.

The candidate is deliberately partial: it carries only source/legal identity,
coverage/provenance, two directly validated action records, and summaries of
the two visually validated final numeric tables. It never claims a complete
LOA parse and performs no remote write.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

TASK = "TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW"
MODE = "T0_OFFLINE_SCOPED_SILVER_CANDIDATE_REVIEW"
BASE_SHA = "68d37d9cc50ec062e3d9e514f2a2bfa666b52b22"
CONTRACT = "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE_SILVER_V1"
SOURCE_SHA256 = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
CANDIDATE_PAYLOAD_SHA256 = "3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c"
TASK036_ROWS_SHA256 = "92c1b5ee1ddab8b2269219fd8f82897ab490d7f9513cbc01358386d111ee56af"
TASK036_TEXT_CHAIN_SHA256 = "9d3df16b1132d3ecb99405ce67fd07dac3b027b06a7735748adc243f1c3c0b10"
TASK036_ACTION_INDEX_SHA256 = "d488c325693320fc2f55e9ddddc744786ee9f876dc072cce1270b9a019bdd908"
TASK037_ROWS_SHA256 = "528bfaf3bf305d395eb874f9e0d22181a93e4e9b80a9b6c4512c11346ac5f773"
TASK037_IMAGE_CHAIN_SHA256 = "5d6a9f73b1dd28448292c585fad9eb51afe5ee67a205aa57f432096e714fe0f3"
TASK037_OCR_CHAIN_SHA256 = "d826be350ed7f6de6cc3e4e090197fdb2785bff49c619c8a000ba86f167201ec"
TABLE480_ROWS_SHA256 = "287ba956b97b6edb1b5e7d53a0f5ce61e21f15ef1c9e1e46cdfe5d4d1bd970e2"
TABLE481_ROWS_SHA256 = "6354e5f4a2ff34c62fa3e4a7f9f9d6ceda8a1db29fb5cdedf673c0b47d5fe368"


class Task039Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task039Error(code)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_upstream(task036: dict[str, Any], task037: dict[str, Any], task038: dict[str, Any]) -> None:
    _require(task036.get("task") == "TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST", "TASK036_ID_MISMATCH")
    _require((task036.get("source") or {}).get("sha256") == SOURCE_SHA256, "TASK036_SOURCE_MISMATCH")
    m36 = task036.get("manifest") or {}
    _require(m36.get("row_count") == 467, "TASK036_ROW_COUNT_MISMATCH")
    _require(m36.get("rows_sha256") == TASK036_ROWS_SHA256, "TASK036_ROWS_HASH_MISMATCH")
    _require(m36.get("page_text_hash_chain_sha256") == TASK036_TEXT_CHAIN_SHA256, "TASK036_TEXT_CHAIN_MISMATCH")
    _require(m36.get("action_code_index_sha256") == TASK036_ACTION_INDEX_SHA256, "TASK036_ACTION_INDEX_MISMATCH")
    _require(m36.get("numeric_values_committed") is False, "TASK036_NUMERIC_POLICY_WEAKENED")

    _require(task037.get("task") == "TASK_037_LOA_JOM_TARGETED_OCR_REVIEW", "TASK037_ID_MISMATCH")
    _require((task037.get("source") or {}).get("sha256") == SOURCE_SHA256, "TASK037_SOURCE_MISMATCH")
    m37 = task037.get("manifest") or {}
    _require(m37.get("rows_sha256") == TASK037_ROWS_SHA256, "TASK037_ROWS_HASH_MISMATCH")
    _require(m37.get("page_image_hash_chain_sha256") == TASK037_IMAGE_CHAIN_SHA256, "TASK037_IMAGE_CHAIN_MISMATCH")
    _require(m37.get("ocr_text_hash_chain_sha256") == TASK037_OCR_CHAIN_SHA256, "TASK037_OCR_CHAIN_MISMATCH")
    _require((m37.get("repeatability") or {}).get("all_page_text_hashes_identical") is True, "TASK037_REPEATABILITY_NOT_PROVEN")
    _require((task037.get("policy") or {}).get("numeric_values_committed") is False, "TASK037_NUMERIC_POLICY_WEAKENED")

    _require(task038.get("task") == "TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION", "TASK038_ID_MISMATCH")
    _require((task038.get("source") or {}).get("sha256") == SOURCE_SHA256, "TASK038_SOURCE_MISMATCH")
    p480 = task038.get("page_480") or {}
    p481 = task038.get("page_481") or {}
    _require(p480.get("rows_sha256") == TABLE480_ROWS_SHA256, "TASK038_PAGE480_HASH_MISMATCH")
    _require(p480.get("row_sum_matches_printed_total") is True, "TASK038_PAGE480_TOTAL_NOT_VALIDATED")
    _require(p481.get("rows_sha256") == TABLE481_ROWS_SHA256, "TASK038_PAGE481_HASH_MISMATCH")
    _require((p481.get("rcl_consistency_check") or {}).get("within_tolerance") is True, "TASK038_PAGE481_CONSISTENCY_NOT_VALIDATED")
    policy38 = task038.get("policy") or {}
    _require(policy38.get("ocr_used_as_numeric_source_truth") is False, "TASK038_OCR_NUMERIC_TRUTH_WEAKENED")
    _require(policy38.get("financial_identity_eiti") == "EVIDENCIA_INSUFICIENTE", "TASK038_EITI_IDENTITY_WEAKENED")


def validate_candidate(evidence: dict[str, Any], task036: dict[str, Any], task037: dict[str, Any], task038: dict[str, Any]) -> dict[str, Any]:
    validate_upstream(task036, task037, task038)
    _require(evidence.get("task") == TASK, "TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "BASE_SHA_MISMATCH")

    candidate = evidence.get("candidate_payload") or {}
    _require(candidate.get("contract") == CONTRACT, "CONTRACT_MISMATCH")
    _require(candidate.get("scope") == "SCOPED_VALIDATED_STRUCTURE_NOT_COMPLETE_LOA_PARSE", "SCOPE_MISMATCH")
    _require(canonical_sha256(candidate) == CANDIDATE_PAYLOAD_SHA256, "CANDIDATE_PAYLOAD_HASH_MISMATCH")
    _require(evidence.get("candidate_payload_sha256") == CANDIDATE_PAYLOAD_SHA256, "PINNED_CANDIDATE_HASH_MISMATCH")

    source = candidate.get("source") or {}
    _require(source.get("sha256") == SOURCE_SHA256, "SOURCE_SHA_MISMATCH")
    _require(source.get("bytes") == 66119594, "SOURCE_BYTES_MISMATCH")
    _require(source.get("total_pdf_pages") == 631, "SOURCE_PAGE_COUNT_MISMATCH")

    legal = candidate.get("legal_instrument") or {}
    _require(legal.get("law_number") == "7.223/2025", "LAW_NUMBER_MISMATCH")
    _require(legal.get("exercise") == 2026, "EXERCISE_MISMATCH")
    _require((legal.get("law_page_start"), legal.get("law_page_end"), legal.get("law_page_count")) == (15, 481, 467), "LAW_BOUNDARY_MISMATCH")

    coverage = candidate.get("coverage") or {}
    _require(coverage.get("native_text_candidate_pages") == 454, "COVERAGE_NATIVE_TEXT_MISMATCH")
    _require(coverage.get("blank_pages") == [375,386,413,415,421,426], "COVERAGE_BLANK_SET_MISMATCH")
    _require(coverage.get("targeted_ocr_pages") == [475,476,477,478,479,480,481], "COVERAGE_TARGETED_OCR_SET_MISMATCH")
    _require(coverage.get("ocr_candidate_text_excluded_from_canonical_text") == [475,476,477,478,479], "OCR_CANDIDATE_EXCLUSION_MISMATCH")
    _require(coverage.get("visually_validated_numeric_table_pages") == [480,481], "NUMERIC_TABLE_VALIDATION_SET_MISMATCH")

    actions = candidate.get("validated_action_records") or []
    _require(len(actions) == 2, "ACTION_RECORD_COUNT_MISMATCH")
    _require(actions[0].get("action_code") == "12.362.2001.2690" and actions[0].get("amount_brl") == "6152000.00", "ACTION_171_MISMATCH")
    _require(actions[1].get("action_code") == "12.306.2001.2720" and actions[1].get("amount_brl") == "28000000.00", "ACTION_174_MISMATCH")
    _require(all(action.get("eiti_specific") is False for action in actions), "ACTION_EITI_SCOPE_WEAKENED")

    t480 = candidate.get("validated_table_480") or {}
    _require(t480.get("rows_sha256") == TABLE480_ROWS_SHA256 and t480.get("row_count") == 10, "TABLE480_MISMATCH")
    _require(t480.get("total_brl") == "128600000.00" and t480.get("row_sum_matches_printed_total") is True, "TABLE480_TOTAL_MISMATCH")
    t481 = candidate.get("validated_table_481") or {}
    _require(t481.get("rows_sha256") == TABLE481_ROWS_SHA256 and t481.get("row_count") == 11, "TABLE481_MISMATCH")
    _require(t481.get("rcl_pair_consistency_within_rounding_tolerance") is True, "TABLE481_CONSISTENCY_MISMATCH")

    pins = candidate.get("provenance_pins") or {}
    expected_pins = {
        "task036_rows_sha256": TASK036_ROWS_SHA256,
        "task036_text_chain_sha256": TASK036_TEXT_CHAIN_SHA256,
        "task036_action_index_sha256": TASK036_ACTION_INDEX_SHA256,
        "task037_rows_sha256": TASK037_ROWS_SHA256,
        "task037_image_chain_sha256": TASK037_IMAGE_CHAIN_SHA256,
        "task037_ocr_chain_sha256": TASK037_OCR_CHAIN_SHA256,
    }
    _require(pins == expected_pins, "PROVENANCE_PINS_MISMATCH")

    guardrails = candidate.get("guardrails") or {}
    for key in ("ocr_numeric_source_truth", "silent_character_repair", "llm_numeric_reconstruction", "complete_loa_parse_claim", "compliance_conclusion", "gold_authorized"):
        _require(guardrails.get(key) is False, f"GUARDRAIL_{key.upper()}_WEAKENED")
    _require(guardrails.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "EITI_FINANCIAL_IDENTITY_WEAKENED")

    readiness = evidence.get("readiness") or {}
    _require(readiness.get("decision") == "READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED", "READINESS_DECISION_MISMATCH")
    _require(readiness.get("scope_is_partial_and_explicit") is True, "PARTIAL_SCOPE_NOT_EXPLICIT")
    _require(readiness.get("complete_loa_silver_claim") is False, "COMPLETE_LOA_CLAIM_FORBIDDEN")
    _require(readiness.get("remote_write_authorized") is False, "REMOTE_WRITE_AUTH_FORBIDDEN")

    effects = evidence.get("effects") or {}
    _require(all(value == 0 for value in effects.values()), "REMOTE_OR_LAYER_EFFECT_NONZERO")
    promotion = evidence.get("promotion") or {}
    for key in ("silver", "gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"PROMOTION_{key.upper()}_WEAKENED")
    _require(promotion.get("f01_status") == "NOT_SILVER", "F01_STATUS_MISMATCH")
    _require(evidence.get("result") == "PASS_SCOPED_SILVER_CANDIDATE_REVIEW_NO_REMOTE_EFFECT", "RESULT_MISMATCH")

    return {
        "status": "PASS_TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW",
        "candidate_contract": CONTRACT,
        "candidate_payload_sha256": CANDIDATE_PAYLOAD_SHA256,
        "readiness": "READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED",
        "f01_status": "NOT_SILVER",
    }
