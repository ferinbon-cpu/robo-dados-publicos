"""Fail-closed validation for TASK 038 LOA JOM numeric tables.

This task records direct visual validation of pages 480-481 from the pinned
300 DPI renders produced from the exact custodied JOM 7127 source. It does not
promote to Silver and does not treat OCR text as numeric source truth.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any

TASK = "TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION"
MODE = "T2_DIRECT_VISUAL_VALIDATION_FROM_EXACT_SOURCE_RENDER"
BASE_SHA = "742843abf24ba8b5a64d445e6600edebd3fd9a4a"
SOURCE_SHA256 = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
PAGE_480_IMAGE_SHA256 = "39be4e0320364441f8e8a18013afe2d44c676c14386ab2082c17ebc615bc5642"
PAGE_481_IMAGE_SHA256 = "1c15c05e2f430655d2d00fc3e502e509f31459b241b6f478447ea61cee398058"
PAGE_480_ROWS_SHA256 = "287ba956b97b6edb1b5e7d53a0f5ce61e21f15ef1c9e1e46cdfe5d4d1bd970e2"
PAGE_481_ROWS_SHA256 = "6354e5f4a2ff34c62fa3e4a7f9f9d6ceda8a1db29fb5cdedf673c0b47d5fe368"

class Task038Error(RuntimeError):
    pass

def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task038Error(code)

def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def validate_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "BASE_SHA_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "OWNER_AUTHORIZATION_MISSING")
    _require(auth.get("owner_message") == "Autorizado prossiga", "OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorized_against_sha") == BASE_SHA, "AUTH_SHA_MISMATCH")
    allowed = set(auth.get("scope") or [])
    for item in ("DIRECT_VISUAL_VALIDATION_PAGES_480_481","ARITHMETIC_CROSSCHECK","RECORD_DERIVED_EVIDENCE","PREPARE_SILVER_CANDIDATE_ONLY"):
        _require(item in allowed, f"AUTH_SCOPE_MISSING_{item}")
    forbidden = set(auth.get("forbidden") or [])
    for item in ("PUBLIC_SOURCE_GET","DRIVE_WRITE","NEW_OCR","FULL_DOCUMENT_OCR","BRONZE","SILVER","GOLD","SERVING","PUBLICATION","LLM_NUMERIC_RECONSTRUCTION","SILENT_TEXT_CORRECTION"):
        _require(item in forbidden, f"AUTH_FORBIDDEN_MISSING_{item}")

    source = evidence.get("source") or {}
    _require(source.get("sha256") == SOURCE_SHA256, "SOURCE_SHA_MISMATCH")
    _require(source.get("bytes") == 66119594, "SOURCE_BYTES_MISMATCH")
    _require(source.get("total_pdf_pages") == 631, "SOURCE_PAGES_MISMATCH")
    _require(source.get("validated_pages") == [480, 481], "PAGE_SET_MISMATCH")

    visual = evidence.get("visual_basis") or {}
    _require(visual.get("render_carried_forward_from_task_037") is True, "RENDER_PROVENANCE_MISSING")
    _require(visual.get("render_tool") == "PyMuPDF", "RENDER_TOOL_MISMATCH")
    _require(visual.get("render_version") == "1.26.7", "RENDER_VERSION_MISMATCH")
    _require(visual.get("dpi") == 300, "RENDER_DPI_MISMATCH")
    hashes = visual.get("page_image_sha256") or {}
    _require(hashes.get("480") == PAGE_480_IMAGE_SHA256, "PAGE_480_IMAGE_HASH_MISMATCH")
    _require(hashes.get("481") == PAGE_481_IMAGE_SHA256, "PAGE_481_IMAGE_HASH_MISMATCH")
    _require(visual.get("validation_method") == "DIRECT_VISUAL_READ_OF_RENDERED_SOURCE_PAGE_NOT_OCR_TEXT", "VISUAL_METHOD_MISMATCH")

    p480 = evidence.get("page_480") or {}
    rows480 = p480.get("rows") or []
    _require(len(rows480) == 10, "PAGE_480_ROW_COUNT_MISMATCH")
    _require(canonical_sha256(rows480) == PAGE_480_ROWS_SHA256, "PAGE_480_ROWS_HASH_MISMATCH")
    computed = sum(int(round(float(row["amount_brl"]) * 100)) for row in rows480)
    _require(computed == 12860000000, "PAGE_480_COMPUTED_TOTAL_MISMATCH")
    _require(p480.get("printed_total_brl") == "128600000.00", "PAGE_480_PRINTED_TOTAL_MISMATCH")
    _require(p480.get("computed_total_brl") == "128600000.00", "PAGE_480_PINNED_TOTAL_MISMATCH")
    _require(p480.get("row_sum_matches_printed_total") is True, "PAGE_480_TOTAL_CHECK_FAILED")
    _require(p480.get("status") == "VISUALLY_VALIDATED_NUMERIC_TABLE", "PAGE_480_STATUS_MISMATCH")

    p481 = evidence.get("page_481") or {}
    rows481 = p481.get("rows") or []
    _require(len(rows481) == 11, "PAGE_481_ROW_COUNT_MISMATCH")
    _require(canonical_sha256(rows481) == PAGE_481_ROWS_SHA256, "PAGE_481_ROWS_HASH_MISMATCH")
    _require(p481.get("status") == "VISUALLY_VALIDATED_NUMERIC_TABLE", "PAGE_481_STATUS_MISMATCH")
    check = p481.get("rcl_consistency_check") or {}
    _require(check.get("within_tolerance") is True, "PAGE_481_RCL_CONSISTENCY_FAILED")
    _require(float(check.get("tolerance_thousands")) == 100.0, "PAGE_481_TOLERANCE_MISMATCH")

    policy = evidence.get("policy") or {}
    _require(policy.get("visual_validation_is_source_page_based") is True, "VISUAL_SOURCE_POLICY_WEAKENED")
    _require(policy.get("ocr_used_as_numeric_source_truth") is False, "OCR_NUMERIC_TRUTH_FORBIDDEN")
    _require(policy.get("numeric_values_now_visually_verified_for_pages_480_481") is True, "NUMERIC_VISUAL_VALIDATION_MISSING")
    _require(policy.get("financial_identity_eiti") == "EVIDENCIA_INSUFICIENTE", "EITI_IDENTITY_WEAKENED")
    _require(policy.get("silent_character_repair") is False, "SILENT_REPAIR_FORBIDDEN")
    _require(policy.get("llm_numeric_reconstruction") is False, "LLM_NUMERIC_RECONSTRUCTION_FORBIDDEN")

    effects = evidence.get("effects") or {}
    expected_effects = {"public_source_get":0,"drive_read":0,"drive_write":0,"new_ocr_pages":0,"bronze":0,"silver":0,"gold":0,"serving":0,"publication":0}
    _require(effects == expected_effects, "EFFECTS_MISMATCH")

    promotion = evidence.get("promotion") or {}
    for key in ("bronze","silver","gold","serving","publication"):
        _require(promotion.get(key) is False, f"PROMOTION_{key.upper()}_WEAKENED")
    _require(promotion.get("f01_status") == "NOT_SILVER", "F01_STATUS_MISMATCH")
    _require(promotion.get("silver_candidate_prepared") is True, "SILVER_CANDIDATE_FLAG_MISSING")
    _require(evidence.get("result") == "PASS_VISUAL_NUMERIC_VALIDATION_SILVER_CANDIDATE_ONLY_NOT_PROMOTED", "RESULT_MISMATCH")
    return {
        "status":"PASS_TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION",
        "validated_pages":[480,481],
        "page_480_total_brl":"128600000.00",
        "page_481_rows":11,
        "f01_status":"NOT_SILVER",
    }
