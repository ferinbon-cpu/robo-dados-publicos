"""Deterministic page-indexed candidate manifest for JOM 7127 / LOA 2026.

The PDF text layer is OCR-derived. This module indexes candidate structure only.
It never promotes OCR numeric values as source truth and never silently repairs
corrupted action codes.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from robo_dados_publicos.manual_ingest.loa_journal_page_aware_parser import (
    extract_brl_candidates,
    extract_exact_action_codes,
)


class LoaJournalPageManifestError(RuntimeError):
    pass


TASK = "TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST"
MODE = "T1_EXACT_BYTE_COPY_OFFLINE_PAGE_INDEXED_CANDIDATE_RUN"
BASE_SHA = "cffd8040540e4a8786a38c6dd9f079d42d7a2134"
SOURCE_SHA256 = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
LAW_START_PAGE = 15
LAW_END_PAGE = 481
LAW_PAGE_COUNT = 467
BLANK_PAGES = (375, 386, 413, 415, 421, 426)
TARGETED_REVIEW_PAGES = (475, 476, 477, 478, 479, 480, 481)
EXPECTED_ROWS_SHA256 = "92c1b5ee1ddab8b2269219fd8f82897ab490d7f9513cbc01358386d111ee56af"
EXPECTED_TEXT_CHAIN_SHA256 = "9d3df16b1132d3ecb99405ce67fd07dac3b027b06a7735748adc243f1c3c0b10"
EXPECTED_ACTION_INDEX_SHA256 = "d488c325693320fc2f55e9ddddc744786ee9f876dc072cce1270b9a019bdd908"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise LoaJournalPageManifestError(code)


def _compact_code_spacing(text: str) -> str:
    value = str(text or "").replace("\u00a0", " ")
    for _ in range(4):
        previous = value
        value = re.sub(r"(?<=\d)\s+(?=\d)", "", value)
        value = re.sub(r"(?<=\d)\s*\.\s*(?=\d)", ".", value)
        value = re.sub(r"(?<=\d)\s*,\s*(?=\d)", ",", value)
        if value == previous:
            break
    return value


def detect_corrupted_action_code_candidate_strict(text: str) -> bool:
    """Flag only corruption locally anchored to an education action-code stem.

    This deliberately avoids the broader TASK 035 preview fallback that can be
    triggered by unrelated OCR noise elsewhere on a Program 2001 page.
    """
    compact = _compact_code_spacing(text)
    if re.search(r"12\.\d{3}\.\d{4}\.\d{4}", compact):
        return False
    return bool(
        re.search(
            r"12\.\d{3}\.\d{4}\.[^\n|]{0,20}[~?][^\n|]{0,8}\d",
            compact,
        )
    )


def _classify_page(page_number: int) -> str:
    _require(LAW_START_PAGE <= page_number <= LAW_END_PAGE, "PAGE_OUTSIDE_LOA_BOUNDARY")
    if page_number in BLANK_PAGES:
        return "SKIP_BLANK"
    if page_number in TARGETED_REVIEW_PAGES:
        return "REVIEW_REQUIRED_TARGETED_EXTRACTION"
    return "PARSE_TEXT_LAYER_CANDIDATES"


def _row(page_number: int, text: str) -> dict[str, Any]:
    action = _classify_page(page_number)
    text = str(text or "")
    base = {
        "page": page_number,
        "page_action": action,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text_chars": len(text),
        "critical_numeric_auto_promotion": False,
        "numeric_values_in_manifest": False,
    }
    if action == "SKIP_BLANK":
        base.update(
            {
                "status": "SKIP_BLANK",
                "action_codes": [],
                "action_code_count": 0,
                "corrupted_action_code_candidate": False,
                "numeric_candidate_count": 0,
            }
        )
        return base
    if action == "REVIEW_REQUIRED_TARGETED_EXTRACTION":
        base.update(
            {
                "status": "REVIEW_REQUIRED_TARGETED_EXTRACTION",
                "action_codes": [],
                "action_code_count": 0,
                "corrupted_action_code_candidate": False,
                "numeric_candidate_count": 0,
            }
        )
        return base

    codes = extract_exact_action_codes(text)
    corrupted = detect_corrupted_action_code_candidate_strict(text)
    numeric_count = len(extract_brl_candidates(text))
    base.update(
        {
            "status": "REVIEW_REQUIRED_CODE_CORRUPTION" if corrupted else "PARSED_CANDIDATES_ONLY",
            "action_codes": codes,
            "action_code_count": len(codes),
            "corrupted_action_code_candidate": corrupted,
            "numeric_candidate_count": numeric_count,
        }
    )
    return base


def build_page_manifest(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_page: dict[int, str] = {}
    for record in records:
        page = record.get("page")
        _require(isinstance(page, int) and not isinstance(page, bool), "PAGE_NUMBER_INVALID")
        _require(page not in by_page, "PAGE_DUPLICATE")
        by_page[page] = str(record.get("text") or "")

    expected = set(range(LAW_START_PAGE, LAW_END_PAGE + 1))
    _require(set(by_page) == expected, "PAGE_SET_INCOMPLETE_OR_OUTSIDE_BOUNDARY")
    return [_row(page, by_page[page]) for page in range(LAW_START_PAGE, LAW_END_PAGE + 1)]


def canonical_rows_sha256(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def page_text_hash_chain_sha256(rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(f"{row['page']}:{row['text_sha256']}" for row in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_action_code_index(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entries = [
        {"page": row["page"], "action_codes": row["action_codes"]}
        for row in rows
        if row["action_code_count"]
    ]
    return {"task": TASK, "source_sha256": SOURCE_SHA256, "entries": entries}


def action_code_index_sha256(index: dict[str, Any]) -> str:
    payload = json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    _require(len(rows) == LAW_PAGE_COUNT, "ROW_COUNT_MISMATCH")
    statuses: dict[str, int] = {}
    for row in rows:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    return {
        "row_count": len(rows),
        "parse_text_layer_pages": sum(row["page_action"] == "PARSE_TEXT_LAYER_CANDIDATES" for row in rows),
        "skip_blank_pages": [row["page"] for row in rows if row["status"] == "SKIP_BLANK"],
        "targeted_review_pages": [row["page"] for row in rows if row["status"] == "REVIEW_REQUIRED_TARGETED_EXTRACTION"],
        "parsed_candidates_only_pages": statuses.get("PARSED_CANDIDATES_ONLY", 0),
        "code_corruption_review_pages": [row["page"] for row in rows if row["status"] == "REVIEW_REQUIRED_CODE_CORRUPTION"],
        "exact_action_code_pages": sum(row["action_code_count"] > 0 for row in rows),
        "exact_action_code_occurrences": sum(row["action_code_count"] for row in rows),
        "pages_with_numeric_candidates": sum(row["numeric_candidate_count"] > 0 for row in rows),
        "numeric_candidate_occurrences": sum(row["numeric_candidate_count"] for row in rows),
        "numeric_values_committed": False,
        "rows_sha256": canonical_rows_sha256(rows),
        "page_text_hash_chain_sha256": page_text_hash_chain_sha256(rows),
        "action_code_index_sha256": action_code_index_sha256(build_action_code_index(rows)),
    }


def validate_evidence(evidence: dict[str, Any], action_index: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "EVIDENCE_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "EVIDENCE_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "EVIDENCE_BASE_SHA_MISMATCH")

    source = evidence.get("source") or {}
    _require(source.get("sha256") == SOURCE_SHA256, "SOURCE_SHA256_MISMATCH")
    _require(source.get("bytes") == 66119594, "SOURCE_BYTES_MISMATCH")
    _require(source.get("total_pdf_pages") == 631, "SOURCE_PAGE_COUNT_MISMATCH")
    _require(source.get("input_transport") == "CONVERSATION_MATERIALIZED_EXACT_BYTE_COPY", "SOURCE_TRANSPORT_MISMATCH")

    extraction = evidence.get("extraction") or {}
    _require(extraction.get("text_layer_kind") == "OCR_DERIVED_TEXT_LAYER", "TEXT_LAYER_KIND_MISMATCH")
    for key in ("full_document_ocr_executed", "targeted_ocr_executed", "silent_character_repair", "llm_numeric_reconstruction"):
        _require(extraction.get(key) is False, f"EXTRACTION_{key.upper()}_WEAKENED")

    manifest = evidence.get("manifest") or {}
    _require(manifest.get("row_count") == 467, "MANIFEST_ROW_COUNT_MISMATCH")
    _require(manifest.get("parse_text_layer_pages") == 454, "MANIFEST_PARSE_PAGE_COUNT_MISMATCH")
    _require(manifest.get("skip_blank_pages") == list(BLANK_PAGES), "MANIFEST_BLANK_SET_MISMATCH")
    _require(manifest.get("targeted_review_pages") == list(TARGETED_REVIEW_PAGES), "MANIFEST_TARGETED_SET_MISMATCH")
    _require(manifest.get("parsed_candidates_only_pages") == 453, "MANIFEST_PARSED_COUNT_MISMATCH")
    _require(manifest.get("code_corruption_review_pages") == [174], "MANIFEST_CORRUPTION_SET_MISMATCH")
    _require(manifest.get("exact_action_code_pages") == 18, "MANIFEST_CODE_PAGE_COUNT_MISMATCH")
    _require(manifest.get("exact_action_code_occurrences") == 49, "MANIFEST_CODE_COUNT_MISMATCH")
    _require(manifest.get("pages_with_numeric_candidates") == 347, "MANIFEST_NUMERIC_PAGE_COUNT_MISMATCH")
    _require(manifest.get("numeric_candidate_occurrences") == 6060, "MANIFEST_NUMERIC_COUNT_MISMATCH")
    _require(manifest.get("numeric_values_committed") is False, "MANIFEST_NUMERIC_VALUES_FORBIDDEN")
    _require(manifest.get("rows_sha256") == EXPECTED_ROWS_SHA256, "MANIFEST_ROWS_HASH_MISMATCH")
    _require(manifest.get("page_text_hash_chain_sha256") == EXPECTED_TEXT_CHAIN_SHA256, "MANIFEST_TEXT_CHAIN_HASH_MISMATCH")

    _require(action_index.get("task") == TASK, "ACTION_INDEX_TASK_MISMATCH")
    _require(action_index.get("source_sha256") == SOURCE_SHA256, "ACTION_INDEX_SOURCE_MISMATCH")
    entries = action_index.get("entries") or []
    _require(len(entries) == 18, "ACTION_INDEX_PAGE_COUNT_MISMATCH")
    _require(sum(len(entry.get("action_codes") or []) for entry in entries) == 49, "ACTION_INDEX_CODE_COUNT_MISMATCH")
    _require(action_code_index_sha256(action_index) == EXPECTED_ACTION_INDEX_SHA256, "ACTION_INDEX_HASH_MISMATCH")

    validations = evidence.get("direct_source_validations_carried_forward") or {}
    _require((validations.get("171") or {}).get("action_code") == "12.362.2001.2690", "PAGE_171_CODE_MISMATCH")
    _require((validations.get("171") or {}).get("amount_brl") == "6152000.00", "PAGE_171_AMOUNT_MISMATCH")
    _require((validations.get("174") or {}).get("action_code") == "12.306.2001.2720", "PAGE_174_CODE_MISMATCH")
    _require((validations.get("174") or {}).get("amount_brl") == "28000000.00", "PAGE_174_AMOUNT_MISMATCH")
    _require((validations.get("171") or {}).get("eiti_specific") is False, "PAGE_171_EITI_SCOPE_WEAKENED")
    _require((validations.get("174") or {}).get("eiti_specific") is False, "PAGE_174_EITI_SCOPE_WEAKENED")

    hardening = evidence.get("heuristic_hardening") or {}
    _require(hardening.get("previous_false_positive_page") == 392, "HARDENING_FALSE_POSITIVE_PAGE_MISMATCH")
    _require(hardening.get("remaining_code_corruption_review_pages") == [174], "HARDENING_RESULT_MISMATCH")

    promotion = evidence.get("promotion") or {}
    for key in ("bronze", "silver", "gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"PROMOTION_{key.upper()}_WEAKENED")
    _require(promotion.get("f01_status") == "NOT_SILVER", "F01_STATUS_MISMATCH")
    _require(promotion.get("financial_identity") == "EVIDENCIA_INSUFICIENTE", "FINANCIAL_IDENTITY_WEAKENED")

    effects = evidence.get("effects") or {}
    for key in ("source_get", "drive_read", "drive_write", "ocr_execution", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"EFFECT_{key.upper()}_NONZERO")

    return {
        "status": "PASS_TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST",
        "row_count": 467,
        "code_corruption_review_pages": [174],
        "targeted_review_pages": list(TARGETED_REVIEW_PAGES),
        "f01_status": "NOT_SILVER",
    }
