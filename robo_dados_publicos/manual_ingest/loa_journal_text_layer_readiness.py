"""Fail-closed review for the LOA 2026 Jornal Oficial text-layer boundary."""
from __future__ import annotations

from typing import Any


class LoaJournalTextLayerReadinessError(RuntimeError):
    pass


EXPECTED_TASK = "TASK_034_LOA_JOM_TEXT_LAYER_READINESS"
EXPECTED_MODE = "T1_EXISTING_CUSTODY_READ_ONLY_ANALYSIS"
EXPECTED_SHA256 = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
EXPECTED_BYTES = 66119594
EXPECTED_TOTAL_PAGES = 631
EXPECTED_LAW_START = 15
EXPECTED_LAW_END = 481
EXPECTED_LAW_PAGES = 467
EXPECTED_NEXT_PAGE = 482
EXPECTED_BLANK_PAGES = [375, 386, 413, 415, 421, 426]
EXPECTED_REVIEW_PAGES = [475, 476, 477, 478, 479, 480, 481]
EXPECTED_STATS_SHA256 = "a4fcb30aacb132609d7952c1c41f7a8d0804dad4a5ace2f47159dd83cbad476f"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise LoaJournalTextLayerReadinessError(code)


def validate_evidence(data: dict[str, Any]) -> dict[str, Any]:
    _require(data.get("task") == EXPECTED_TASK, "TASK_MISMATCH")
    _require(data.get("version") == "0.8.0", "VERSION_MISMATCH")
    _require(data.get("mode") == EXPECTED_MODE, "MODE_MISMATCH")

    source = data.get("source") or {}
    _require(source.get("drive_file_id") == "1bRpmMxacX16P1tJBvam-55OOPTYuQnIA", "SOURCE_ID_MISMATCH")
    _require(source.get("filename") == "SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf", "SOURCE_FILENAME_MISMATCH")
    _require(source.get("bytes") == EXPECTED_BYTES, "SOURCE_BYTES_MISMATCH")
    _require(source.get("sha256") == EXPECTED_SHA256, "SOURCE_SHA256_MISMATCH")
    _require(source.get("edition") == 7127, "SOURCE_EDITION_MISMATCH")
    _require(source.get("publication_date") == "2025-11-29", "SOURCE_DATE_MISMATCH")
    _require(source.get("total_pdf_pages") == EXPECTED_TOTAL_PAGES, "SOURCE_PAGE_COUNT_MISMATCH")
    _require(source.get("law_number") == "7.223/2025", "LAW_NUMBER_MISMATCH")

    boundary = data.get("law_boundary") or {}
    _require(boundary.get("start_page") == EXPECTED_LAW_START, "LAW_START_MISMATCH")
    _require(boundary.get("end_page") == EXPECTED_LAW_END, "LAW_END_MISMATCH")
    _require(boundary.get("pages_inclusive") == EXPECTED_LAW_PAGES, "LAW_PAGE_SPAN_MISMATCH")
    _require(boundary.get("next_page") == EXPECTED_NEXT_PAGE, "NEXT_PAGE_MISMATCH")
    _require(boundary.get("boundary_status") == "PROVEN_BY_TEXT_AND_VISUAL_REVIEW", "BOUNDARY_NOT_PROVEN")
    _require(boundary.get("end_page_visual_status") == "LOA_ANNEX_CONTENT", "END_PAGE_NOT_LOA")

    layer = data.get("text_layer") or {}
    _require(layer.get("law_pages_with_native_content_text") == 454, "NATIVE_TEXT_PAGE_COUNT_MISMATCH")
    _require(layer.get("visually_blank_law_pages") == EXPECTED_BLANK_PAGES, "BLANK_PAGE_SET_MISMATCH")
    _require(layer.get("image_content_without_body_text_pages") == EXPECTED_REVIEW_PAGES, "IMAGE_ONLY_PAGE_SET_MISMATCH")
    _require(layer.get("targeted_ocr_or_visual_extraction_required_pages") == EXPECTED_REVIEW_PAGES, "TARGETED_REVIEW_SET_MISMATCH")
    _require(layer.get("full_466_page_ocr_required") is False, "FULL_466_OCR_MUST_REMAIN_FALSE")
    _require(layer.get("full_467_page_journal_law_ocr_required") is False, "FULL_JOM_OCR_MUST_REMAIN_FALSE")
    _require(layer.get("page_stats_sha256") == EXPECTED_STATS_SHA256, "PAGE_STATS_HASH_MISMATCH")

    review = data.get("review") or {}
    for key in (
        "page_15_render_verified",
        "pages_472_485_render_verified",
        "low_text_pages_render_verified",
        "page_481_is_loa_content",
        "page_482_is_not_loa",
        "no_ocr_executed",
        "no_parser_executed",
        "no_drive_write_performed",
        "no_bronze_silver_gold_serving_publication",
    ):
        _require(review.get(key) is True, f"REVIEW_FLAG_{key.upper()}_MISMATCH")

    promotion = data.get("promotion") or {}
    _require(promotion.get("f01_status") == "NOT_SILVER", "F01_PROMOTION_FORBIDDEN")

    return {
        "status": "PASS_TASK_034_LOA_JOM_TEXT_LAYER_READINESS",
        "law_pages": EXPECTED_LAW_PAGES,
        "native_text_content_pages": 454,
        "targeted_review_pages": EXPECTED_REVIEW_PAGES,
        "full_document_ocr_required": False,
        "f01_status": "NOT_SILVER",
    }
