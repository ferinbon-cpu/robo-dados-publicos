"""Page-aware, fail-closed candidate parser for the LOA 2026 Jornal Oficial.

The source PDF carries an OCR-derived text layer. This module may use that layer
for navigation and structural candidates, but it never treats critical numeric
values as source truth without visual or independent validation.
"""
from __future__ import annotations

import re
from typing import Any, Iterable


class LoaJournalPageAwareParserError(RuntimeError):
    pass


EXPECTED_TASK = "TASK_035_LOA_JOM_PAGE_AWARE_PARSER_PREVIEW"
EXPECTED_MODE = "T0_OFFLINE_PARSER_IMPLEMENTATION_AND_PINNED_PREVIEW"
EXPECTED_SOURCE_SHA256 = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
LAW_START_PAGE = 15
LAW_END_PAGE = 481
BLANK_PAGES = (375, 386, 413, 415, 421, 426)
TARGETED_REVIEW_PAGES = (475, 476, 477, 478, 479, 480, 481)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise LoaJournalPageAwareParserError(code)


def validate_contract(data: dict[str, Any]) -> dict[str, Any]:
    _require(data.get("task") == EXPECTED_TASK, "CONTRACT_TASK_MISMATCH")
    _require(data.get("mode") == EXPECTED_MODE, "CONTRACT_MODE_MISMATCH")
    source = data.get("source") or {}
    _require(source.get("edition") == 7127, "CONTRACT_EDITION_MISMATCH")
    _require(source.get("law_number") == "7.223/2025", "CONTRACT_LAW_MISMATCH")
    _require(source.get("sha256") == EXPECTED_SOURCE_SHA256, "CONTRACT_SHA256_MISMATCH")
    _require(source.get("total_pdf_pages") == 631, "CONTRACT_TOTAL_PAGE_MISMATCH")
    _require(source.get("law_start_page") == LAW_START_PAGE, "CONTRACT_START_PAGE_MISMATCH")
    _require(source.get("law_end_page") == LAW_END_PAGE, "CONTRACT_END_PAGE_MISMATCH")

    policy = data.get("page_policy") or {}
    _require(tuple(policy.get("visually_blank_pages") or []) == BLANK_PAGES, "CONTRACT_BLANK_SET_MISMATCH")
    _require(tuple(policy.get("targeted_review_pages") or []) == TARGETED_REVIEW_PAGES, "CONTRACT_REVIEW_SET_MISMATCH")
    _require(policy.get("blank_page_action") == "SKIP_BLANK", "CONTRACT_BLANK_ACTION_MISMATCH")
    _require(policy.get("targeted_review_action") == "REVIEW_REQUIRED_TARGETED_EXTRACTION", "CONTRACT_REVIEW_ACTION_MISMATCH")
    _require(policy.get("other_page_action") == "PARSE_TEXT_LAYER_CANDIDATES", "CONTRACT_PARSE_ACTION_MISMATCH")

    numeric = data.get("numeric_policy") or {}
    expected_false = (
        "text_layer_numeric_values_are_final",
        "critical_numeric_auto_promotion",
        "silent_correction",
        "llm_numeric_reconstruction",
    )
    _require(numeric.get("text_layer_kind") == "OCR_DERIVED_TEXT_LAYER", "CONTRACT_TEXT_LAYER_KIND_MISMATCH")
    _require(numeric.get("visual_or_independent_validation_required") is True, "CONTRACT_NUMERIC_VALIDATION_WEAKENED")
    for key in expected_false:
        _require(numeric.get(key) is False, f"CONTRACT_{key.upper()}_WEAKENED")

    promotion = data.get("promotion") or {}
    for key in ("bronze", "silver", "gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"CONTRACT_{key.upper()}_PROMOTION_WEAKENED")
    return {"status": "PASS_TASK_035_CONTRACT"}


def classify_page(page_number: int) -> str:
    _require(isinstance(page_number, int) and not isinstance(page_number, bool), "PAGE_NUMBER_INVALID")
    _require(LAW_START_PAGE <= page_number <= LAW_END_PAGE, "PAGE_OUTSIDE_LOA_BOUNDARY")
    if page_number in BLANK_PAGES:
        return "SKIP_BLANK"
    if page_number in TARGETED_REVIEW_PAGES:
        return "REVIEW_REQUIRED_TARGETED_EXTRACTION"
    return "PARSE_TEXT_LAYER_CANDIDATES"


def _compact_code_spacing(text: str) -> str:
    """Normalize spacing only; never repair non-digit OCR substitutions."""
    value = str(text or "").replace("\u00a0", " ")
    # Join digits separated by OCR whitespace and normalize separators. This can
    # recover `12. 362 . 2001 . 2690`, but deliberately leaves `2 ~20` broken.
    for _ in range(4):
        previous = value
        value = re.sub(r"(?<=\d)\s+(?=\d)", "", value)
        value = re.sub(r"(?<=\d)\s*\.\s*(?=\d)", ".", value)
        value = re.sub(r"(?<=\d)\s*,\s*(?=\d)", ",", value)
        if value == previous:
            break
    return value


def extract_exact_action_codes(text: str) -> list[str]:
    """Return only digit-exact function.subfunction.program.action codes.

    Table borders can be OCR'd as leading `1` characters, so matching is allowed
    inside a longer digit run. No character substitution is repaired.
    """
    compact = _compact_code_spacing(text)
    codes = re.findall(r"(12\.\d{3}\.\d{4}\.\d{4})", compact)
    seen: list[str] = []
    for code in codes:
        if code not in seen:
            seen.append(code)
    return seen


def detect_corrupted_action_code_candidate(text: str) -> bool:
    """Detect an action-looking education code whose final token is OCR-corrupt."""
    compact = _compact_code_spacing(text)
    if re.search(r"12\.\d{3}\.\d{4}\.\d{4}", compact):
        return False
    # Typical observed corruption includes `2 ~20`; permit punctuation/noise but
    # never convert it into a digit-exact code.
    return bool(re.search(r"12\.\d{3}\.\d{4}\.[0-9][^\s|]{0,2}\s*[~?][^\s|]{0,3}[0-9]", compact)) or (
        "2001" in compact and "~" in compact and "12." in compact
    )


def _brl_string_to_cents(raw: str) -> int:
    normalized = re.sub(r"\s+", "", raw)
    normalized = normalized.replace(".", "").replace(",", ".")
    value = float(normalized)
    return int(round(value * 100))


def extract_brl_candidates(text: str) -> list[dict[str, Any]]:
    """Extract OCR-text monetary candidates, always marked unverified."""
    pattern = re.compile(r"(?<!\d)(\d{1,3}(?:\s*\.\s*\d{3})+\s*,\s*\d{2})(?!\d)")
    out: list[dict[str, Any]] = []
    for match in pattern.finditer(str(text or "")):
        raw = match.group(1)
        out.append(
            {
                "raw": raw,
                "cents": _brl_string_to_cents(raw),
                "status": "OCR_TEXT_NUMERIC_CANDIDATE_UNVERIFIED",
                "auto_promotable": False,
            }
        )
    return out


def parse_page(page_number: int, text: str) -> dict[str, Any]:
    action = classify_page(page_number)
    result: dict[str, Any] = {
        "page": page_number,
        "page_action": action,
        "source_layer": "OCR_DERIVED_TEXT_LAYER",
        "critical_numeric_auto_promotion": False,
    }
    if action == "SKIP_BLANK":
        result.update({"action_codes": [], "numeric_candidates": [], "status": "SKIP_BLANK"})
        return result
    if action == "REVIEW_REQUIRED_TARGETED_EXTRACTION":
        result.update(
            {
                "action_codes": [],
                "numeric_candidates": [],
                "status": "REVIEW_REQUIRED_TARGETED_EXTRACTION",
            }
        )
        return result

    exact_codes = extract_exact_action_codes(text)
    corrupted = detect_corrupted_action_code_candidate(text)
    result.update(
        {
            "action_codes": exact_codes,
            "numeric_candidates": extract_brl_candidates(text),
            "corrupted_action_code_candidate": corrupted,
            "status": "REVIEW_REQUIRED_CODE_CORRUPTION" if corrupted else "PARSED_CANDIDATES_ONLY",
        }
    )
    return result


def parse_pages(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    seen: set[int] = set()
    for record in records:
        page_number = record.get("page")
        _require(isinstance(page_number, int) and not isinstance(page_number, bool), "PAGE_RECORD_NUMBER_INVALID")
        _require(page_number not in seen, "PAGE_RECORD_DUPLICATE")
        seen.add(page_number)
        pages.append(parse_page(page_number, str(record.get("text") or "")))
    pages.sort(key=lambda row: row["page"])
    return {
        "status": "PASS_TASK_035_PARSER_PREVIEW",
        "pages": pages,
        "promotion_authorized": False,
        "numeric_truth_from_text_layer_authorized": False,
    }
