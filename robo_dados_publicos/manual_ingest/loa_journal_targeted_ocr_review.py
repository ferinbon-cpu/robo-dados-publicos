"""Fail-closed review for the bounded targeted OCR of JOM 7127 pages 475-481.

TASK 037 consumes only the seven page-level review slots left by TASK 036.
OCR text is derived evidence, not source truth. Critical numeric values are never
auto-promoted and pages 480-481 remain numeric-table review requirements.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

TASK = "TASK_037_LOA_JOM_TARGETED_OCR_REVIEW"
MODE = "T2_BOUNDED_TARGETED_OCR_EXACT_BYTE_SOURCE"
BASE_SHA = "eb8f370e6957de5788bbfbbe97d8cd77c5fb9632"
SOURCE_SHA256 = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
SOURCE_BYTES = 66119594
SOURCE_PAGES = 631
TARGET_PAGES = (475, 476, 477, 478, 479, 480, 481)
RENDER_CONFIG_SHA256 = "f34141496ad0fffcd7f47809855709a8f777f8be77fe7929fb35b7dd95e3f68d"
OCR_CONFIG_SHA256 = "4b7482b941944c0de111d178cc4ba7f8c02e18033d16c99de2e23aa327ee4252"
ROWS_SHA256 = "528bfaf3bf305d395eb874f9e0d22181a93e4e9b80a9b6c4512c11346ac5f773"
IMAGE_CHAIN_SHA256 = "5d6a9f73b1dd28448292c585fad9eb51afe5ee67a205aa57f432096e714fe0f3"
OCR_CHAIN_SHA256 = "d826be350ed7f6de6cc3e4e090197fdb2785bff49c619c8a000ba86f167201ec"
OCR_TEXT_CHARS_TOTAL = 16732

EXPECTED_TEXT_HASHES = {
    475: "056bbde3b7c7113f40576c82164414c72dbf17aa8b8dad2e24e6b11e319c9ab8",
    476: "ce37144acd01311a3c546450a28c05f767b41a795df3278f985a17b9dd66e452",
    477: "c0f3a49a0963cac4d029b8abf57b154a4a1365964491629cbe378d46a870aaf8",
    478: "c0d764eb3c964965d1ff49f96ca53c05413a042f7d27c6a51333bb7bbdc2906f",
    479: "ab5762858f1e82ad440945cef36b678b555a0848a0c761688c7fcfbde6cd02b8",
    480: "ec6e3dc63c7501bc8269da2e332015cd034d46a18dfdf0ccba42e4dee0add2b6",
    481: "75f9bb4bc329176a228836449e66ad3bc454ec6f1fefe575f824f5458b79ad2f",
}


class TargetedOcrReviewError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise TargetedOcrReviewError(code)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_rows_sha256(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_text(payload)


def chain_sha256(rows: list[dict[str, Any]], key: str) -> str:
    payload = "\n".join(f"{row['page']}:{row[key]}" for row in rows)
    return _sha256_text(payload)


def validate_evidence(evidence: dict[str, Any], ocr_texts: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "EVIDENCE_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "EVIDENCE_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "EVIDENCE_BASE_SHA_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "OWNER_AUTHORIZATION_MISSING")
    _require(auth.get("owner_message") == "Prossiga", "OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorized_against_sha") == BASE_SHA, "OWNER_AUTHORIZATION_SHA_MISMATCH")
    scope = auth.get("scope") or []
    for required in (
        "DRIVE_READ_EXACT_SOURCE",
        "RENDER_PAGES_475_481",
        "TARGETED_OCR_PAGES_475_481",
        "RECORD_DERIVED_EVIDENCE",
    ):
        _require(required in scope, f"AUTH_SCOPE_MISSING_{required}")
    forbidden = set(auth.get("forbidden") or [])
    for required in (
        "PUBLIC_SOURCE_GET", "DRIVE_WRITE", "BRONZE", "SILVER", "GOLD",
        "SERVING", "PUBLICATION", "FULL_DOCUMENT_OCR",
        "LLM_NUMERIC_RECONSTRUCTION", "SILENT_TEXT_CORRECTION",
    ):
        _require(required in forbidden, f"AUTH_FORBIDDEN_MISSING_{required}")

    source = evidence.get("source") or {}
    _require(source.get("sha256") == SOURCE_SHA256, "SOURCE_SHA256_MISMATCH")
    _require(source.get("bytes") == SOURCE_BYTES, "SOURCE_BYTES_MISMATCH")
    _require(source.get("total_pdf_pages") == SOURCE_PAGES, "SOURCE_PAGE_COUNT_MISMATCH")
    _require(source.get("target_pages") == list(TARGET_PAGES), "TARGET_PAGE_SET_MISMATCH")
    _require(source.get("input_transport") == "GOOGLE_DRIVE_EXACT_BYTE_DOWNLOAD", "SOURCE_TRANSPORT_MISMATCH")
    for key in ("drive_read_completed", "source_sha256_verified", "source_bytes_verified", "source_page_count_verified"):
        _require(source.get(key) is True, f"SOURCE_{key.upper()}_NOT_VERIFIED")

    render = evidence.get("render") or {}
    _require(render.get("tool") == "PyMuPDF", "RENDER_TOOL_MISMATCH")
    _require(render.get("version") == "1.26.7", "RENDER_VERSION_MISMATCH")
    _require(render.get("dpi") == 300, "RENDER_DPI_MISMATCH")
    _require(render.get("alpha") is False, "RENDER_ALPHA_MISMATCH")
    _require(render.get("colorspace") == "RGB", "RENDER_COLORSPACE_MISMATCH")
    _require(render.get("config_sha256") == RENDER_CONFIG_SHA256, "RENDER_CONFIG_HASH_MISMATCH")

    ocr = evidence.get("ocr") or {}
    _require(ocr.get("engine") == "tesseract", "OCR_ENGINE_MISMATCH")
    _require(ocr.get("version") == "5.5.0", "OCR_VERSION_MISMATCH")
    _require(ocr.get("language") == "eng", "OCR_LANGUAGE_MISMATCH")
    _require(ocr.get("oem") == 1, "OCR_OEM_MISMATCH")
    _require(ocr.get("psm") == 6, "OCR_PSM_MISMATCH")
    _require(ocr.get("preserve_interword_spaces") == 1, "OCR_SPACING_CONFIG_MISMATCH")
    _require(ocr.get("config_sha256") == OCR_CONFIG_SHA256, "OCR_CONFIG_HASH_MISMATCH")
    _require(ocr.get("repeatability_runs") == 2, "OCR_REPEATABILITY_RUNS_MISMATCH")
    _require(ocr.get("repeatability_required") is True, "OCR_REPEATABILITY_REQUIREMENT_WEAKENED")

    manifest = evidence.get("manifest") or {}
    _require(manifest.get("row_count") == 7, "MANIFEST_ROW_COUNT_MISMATCH")
    _require(manifest.get("pages") == list(TARGET_PAGES), "MANIFEST_PAGE_SET_MISMATCH")
    rows = manifest.get("rows") or []
    _require(len(rows) == 7, "MANIFEST_ROWS_MISSING")
    _require([row.get("page") for row in rows] == list(TARGET_PAGES), "MANIFEST_PAGE_ORDER_MISMATCH")
    _require(canonical_rows_sha256(rows) == ROWS_SHA256, "MANIFEST_ROWS_HASH_MISMATCH")
    _require(manifest.get("rows_sha256") == ROWS_SHA256, "PINNED_ROWS_HASH_MISMATCH")
    _require(chain_sha256(rows, "page_image_sha256") == IMAGE_CHAIN_SHA256, "IMAGE_CHAIN_HASH_MISMATCH")
    _require(manifest.get("page_image_hash_chain_sha256") == IMAGE_CHAIN_SHA256, "PINNED_IMAGE_CHAIN_MISMATCH")
    _require(chain_sha256(rows, "ocr_text_sha256") == OCR_CHAIN_SHA256, "OCR_CHAIN_HASH_MISMATCH")
    _require(manifest.get("ocr_text_hash_chain_sha256") == OCR_CHAIN_SHA256, "PINNED_OCR_CHAIN_MISMATCH")
    _require(sum(row.get("ocr_text_chars", -1) for row in rows) == OCR_TEXT_CHARS_TOTAL, "OCR_CHAR_TOTAL_MISMATCH")
    _require(manifest.get("ocr_text_chars_total") == OCR_TEXT_CHARS_TOTAL, "PINNED_OCR_CHAR_TOTAL_MISMATCH")
    repeat = manifest.get("repeatability") or {}
    _require(repeat.get("runs") == 2, "REPEATABILITY_RUN_COUNT_MISMATCH")
    _require(repeat.get("all_page_text_hashes_identical") is True, "OCR_NOT_REPEATABLE")

    for row in rows:
        page = row["page"]
        _require(row.get("native_text_chars") == 138, f"PAGE_{page}_NATIVE_TEXT_LENGTH_MISMATCH")
        _require(row.get("critical_numeric_auto_promotion") is False, f"PAGE_{page}_NUMERIC_PROMOTION_WEAKENED")
        _require(row.get("visual_or_independent_validation_required") is True, f"PAGE_{page}_VISUAL_VALIDATION_WEAKENED")
        if page in (480, 481):
            _require(row.get("status") == "REVIEW_REQUIRED_NUMERIC_TABLE", f"PAGE_{page}_NUMERIC_TABLE_STATUS_MISMATCH")
        else:
            _require(row.get("status") == "OCR_TEXT_RECOVERED_CANDIDATE_ONLY", f"PAGE_{page}_OCR_STATUS_MISMATCH")

    _require(ocr_texts.get("task") == TASK, "OCR_TEXTS_TASK_MISMATCH")
    _require(ocr_texts.get("source_sha256") == SOURCE_SHA256, "OCR_TEXTS_SOURCE_MISMATCH")
    _require(ocr_texts.get("status") == "DERIVED_OCR_CANDIDATE_ONLY", "OCR_TEXTS_STATUS_MISMATCH")
    _require(ocr_texts.get("numeric_source_truth") is False, "OCR_TEXTS_NUMERIC_TRUTH_FORBIDDEN")
    texts = ocr_texts.get("texts") or {}
    _require(sorted(int(key) for key in texts) == list(TARGET_PAGES), "OCR_TEXTS_PAGE_SET_MISMATCH")
    for page in TARGET_PAGES:
        text = texts.get(str(page))
        _require(isinstance(text, str) and text, f"OCR_TEXT_PAGE_{page}_MISSING")
        _require(_sha256_text(text) == EXPECTED_TEXT_HASHES[page], f"OCR_TEXT_PAGE_{page}_HASH_MISMATCH")

    policy = evidence.get("policy") or {}
    for key in ("ocr_is_derived_not_source", "visual_or_independent_validation_required", "pages_480_481_numeric_tables_review_required"):
        _require(policy.get(key) is True, f"POLICY_{key.upper()}_WEAKENED")
    for key in ("numeric_values_committed", "critical_numeric_auto_promotion", "silent_character_repair", "llm_numeric_reconstruction"):
        _require(policy.get(key) is False, f"POLICY_{key.upper()}_WEAKENED")

    effects = evidence.get("effects") or {}
    expected_effects = {
        "public_source_get": 0, "drive_read": 1, "drive_write": 0,
        "pages_rendered": 7, "ocr_pages": 7, "ocr_repeat_runs": 2,
        "bronze": 0, "silver": 0, "gold": 0, "serving": 0, "publication": 0,
    }
    _require(effects == expected_effects, "EFFECTS_MISMATCH")

    promotion = evidence.get("promotion") or {}
    for key in ("bronze", "silver", "gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"PROMOTION_{key.upper()}_WEAKENED")
    _require(promotion.get("f01_status") == "NOT_SILVER", "F01_STATUS_MISMATCH")
    _require(evidence.get("result") == "PASS_TARGETED_OCR_EVIDENCE_ONLY_NOT_PROMOTED", "RESULT_MISMATCH")

    return {
        "status": "PASS_TASK_037_LOA_JOM_TARGETED_OCR_REVIEW",
        "pages": list(TARGET_PAGES),
        "ocr_text_chars_total": OCR_TEXT_CHARS_TOTAL,
        "numeric_table_review_pages": [480, 481],
        "f01_status": "NOT_SILVER",
    }
