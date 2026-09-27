from __future__ import annotations

from pathlib import Path
import json
import re


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LoaExtractionStop(ValueError):
    """Fail-closed stop for LOA reproducible-extraction readiness."""


def load_loa_extraction_contract(path: str | Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("mode") != "T0_OFFLINE_DESIGN":
        raise LoaExtractionStop("STOP_LOA_EXTRACTION_BAD_MODE")
    source = raw.get("canonical_source") or {}
    if source.get("pages") != 466 or source.get("text_layer") != "ABSENT":
        raise LoaExtractionStop("STOP_LOA_CANONICAL_SOURCE_BOUNDARY_DRIFT")
    if not _SHA256.fullmatch(str(source.get("sha256", ""))):
        raise LoaExtractionStop("STOP_LOA_CANONICAL_HASH_INVALID")
    return raw


def choose_extraction_route(contract: dict, proposal: dict) -> dict:
    route = proposal.get("route")
    priority = contract.get("route_priority", [])
    if route not in priority:
        raise LoaExtractionStop("STOP_LOA_EXTRACTION_ROUTE_NOT_ALLOWED")

    if proposal.get("execute") is True:
        raise LoaExtractionStop("STOP_LOA_EXTRACTION_EXECUTION_NOT_AUTHORIZED")

    if route in {"OFFICIAL_MACHINE_READABLE_EQUIVALENT", "OFFICIAL_COMPLETE_TEXT_EQUIVALENT"}:
        required = contract.get("official_route", {}).get("accept_only_if", [])
        proofs = proposal.get("proofs") or {}
        missing = [name for name in required if proofs.get(name) is not True]
        if missing:
            raise LoaExtractionStop(
                "STOP_LOA_OFFICIAL_EQUIVALENCE_NOT_PROVEN: " + ", ".join(missing)
            )
        return {
            "status": "READY_FOR_SEPARATE_OFFICIAL_EQUIVALENCE_REVIEW",
            "route": route,
            "execution_authorized": False,
        }

    source = contract.get("canonical_source", {})
    if proposal.get("input_sha256") != source.get("sha256"):
        raise LoaExtractionStop("STOP_LOA_OCR_INPUT_HASH_MISMATCH")
    if proposal.get("page_count") != source.get("pages"):
        raise LoaExtractionStop("STOP_LOA_OCR_PAGE_COUNT_MISMATCH")
    return {
        "status": "READY_FOR_SEPARATE_DETERMINISTIC_OCR_AUTHORIZATION_REVIEW",
        "route": route,
        "execution_authorized": False,
    }


def validate_ocr_manifest(contract: dict, rows: list[dict]) -> dict:
    ocr = contract.get("ocr_route", {})
    acceptance = contract.get("manifest_acceptance", {})
    expected_pages = int(ocr.get("page_count_must_equal", 0))
    required_fields = tuple(ocr.get("required_page_fields", []))

    if len(rows) != expected_pages:
        raise LoaExtractionStop("STOP_LOA_OCR_MANIFEST_ROW_COUNT")

    page_numbers = [row.get("page_number") for row in rows]
    if page_numbers != list(range(1, expected_pages + 1)):
        raise LoaExtractionStop("STOP_LOA_OCR_MANIFEST_PAGE_SEQUENCE")
    if len(set(page_numbers)) != len(page_numbers):
        raise LoaExtractionStop("STOP_LOA_OCR_MANIFEST_DUPLICATE_PAGE")

    engines = set()
    render_configs = set()
    review_required = 0
    blank_pages = 0

    for row in rows:
        missing = [field for field in required_fields if field not in row]
        if missing:
            raise LoaExtractionStop(
                "STOP_LOA_OCR_MANIFEST_MISSING_FIELDS: " + ", ".join(missing)
            )
        for hash_field in ("page_image_sha256", "ocr_text_sha256", "engine_config_sha256"):
            if not _SHA256.fullmatch(str(row.get(hash_field, ""))):
                raise LoaExtractionStop(
                    f"STOP_LOA_OCR_MANIFEST_BAD_SHA256: {hash_field}"
                )
        chars = row.get("ocr_text_chars")
        if not isinstance(chars, int) or chars < 0:
            raise LoaExtractionStop("STOP_LOA_OCR_MANIFEST_BAD_TEXT_CHARS")
        blank = row.get("blank_page")
        if not isinstance(blank, bool):
            raise LoaExtractionStop("STOP_LOA_OCR_MANIFEST_BAD_BLANK_FLAG")
        if chars == 0 and blank is not True and acceptance.get("empty_text_allowed_only_when_blank_page_true"):
            raise LoaExtractionStop("STOP_LOA_OCR_EMPTY_NONBLANK_PAGE")
        if blank:
            blank_pages += 1

        engines.add((row.get("engine_name"), row.get("engine_version"), row.get("engine_config_sha256")))
        render_configs.add((row.get("render_dpi"), row.get("render_tool"), row.get("render_tool_version")))
        if row.get("critical_numeric_status") == "REVIEW_REQUIRED":
            review_required += 1

    if acceptance.get("mixed_engine_versions_allowed") is False and len(engines) != 1:
        raise LoaExtractionStop("STOP_LOA_OCR_MIXED_ENGINE_CONFIG")
    if acceptance.get("mixed_render_configs_allowed") is False and len(render_configs) != 1:
        raise LoaExtractionStop("STOP_LOA_OCR_MIXED_RENDER_CONFIG")

    return {
        "status": "PASS_LOA_OCR_MANIFEST_STRUCTURE_ONLY",
        "pages": expected_pages,
        "blank_pages": blank_pages,
        "critical_numeric_review_required_pages": review_required,
        "text_is_derived_not_source": True,
        "silver_authorized": False,
    }


def validate_numeric_candidate(contract: dict, candidate: dict) -> dict:
    policy = contract.get("ocr_route", {}).get("critical_numeric_policy", {})
    if candidate.get("value") is None:
        raise LoaExtractionStop("STOP_LOA_NUMERIC_VALUE_MISSING")
    if policy.get("requires_source_page_locator") and not candidate.get("source_page"):
        raise LoaExtractionStop("STOP_LOA_NUMERIC_SOURCE_PAGE_REQUIRED")
    if policy.get("requires_visual_or_independent_validation") and candidate.get("validated_independently") is not True:
        return {
            "status": policy.get("unresolved_status", "REVIEW_REQUIRED"),
            "automatic_promotion": False,
        }
    return {
        "status": "VALIDATED_CANDIDATE_NOT_PROMOTED",
        "automatic_promotion": False,
    }
