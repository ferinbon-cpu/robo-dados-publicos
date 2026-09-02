from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BudgetJournalSourceFirstStop(ValueError):
    """Fail-closed validation error for the Jornal source-first contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BudgetJournalSourceFirstStop(message)


def load_budget_journal_source_first(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_budget_journal_source_first(data)
    return data


def validate_budget_journal_source_first(data: dict[str, Any]) -> dict[str, Any]:
    _require(data.get("mode") == "T0_OFFLINE_SOURCE_FIRST_DESIGN", "unexpected mode")
    _require(data.get("municipality") == "Limeira-SP", "wrong municipality")

    decision = data.get("decision", {})
    _require(decision.get("primary_source") == "JORNAL_OFICIAL_LIMEIRA_FULL_EDITION_PDF", "journal is not primary")
    _require(decision.get("standalone_prefeitura_pdf_role") == "OFFICIAL_COMPLEMENTARY_COPY", "standalone role drift")
    _require(decision.get("full_equivalence_required_before_extraction") is False, "equivalence must not block extraction")
    _require(decision.get("journal_full_edition_must_enter_custody_before_extraction") is True, "custody prerequisite disabled")
    _require(decision.get("hash_and_readback_required_before_extraction") is True, "hash/readback prerequisite disabled")
    _require(decision.get("extract_from_search_engine_index") is False, "search index cannot be extraction source")
    _require(decision.get("extract_from_standalone_pdf_by_default") is False, "standalone cannot remain default extraction source")
    _require(decision.get("divergence_action") == "REVIEW_STOP", "divergence must stop")

    drive = data.get("target_drive", {})
    _require(drive.get("root") == "10_INBOX/PENDENTES/F01_PPA_LDO_LOA_2026", "unexpected target root")
    _require(drive.get("write_mode") == "CREATE_ONLY", "write mode must be create-only")
    for key in ("overwrite", "delete", "replace"):
        _require(drive.get(key) is False, f"unsafe drive mutation enabled: {key}")

    records = data.get("journal_editions")
    _require(isinstance(records, list) and len(records) == 3, "expected exactly three journal editions")
    by_family = {record.get("document_family"): record for record in records}
    _require(set(by_family) == {"PPA", "LDO", "LOA"}, "document family drift")

    expected = {
        "LDO": ("7.141/2025", 7024, "2025-07-08", 79, 5, "u_137_07072025191855.pdf"),
        "PPA": ("7.213/2025", 7119, "2025-11-15", 107, 5, "u_137_14112025171148.pdf"),
        "LOA": ("7.223/2025", 7127, "2025-11-29", 631, 15, "u_137_28112025211140.pdf"),
    }

    for family, values in expected.items():
        law_number, edition, publication_date, total_pages, start_page, url_suffix = values
        record = by_family[family]
        _require(record.get("law_number") == law_number, f"{family}: law number drift")
        _require(record.get("edition") == edition, f"{family}: edition drift")
        _require(record.get("publication_date") == publication_date, f"{family}: publication date drift")
        _require(record.get("expected_total_pages") == total_pages, f"{family}: page count drift")
        _require(record.get("known_law_start_page") == start_page, f"{family}: start page drift")
        source_url = str(record.get("source_url", ""))
        _require(source_url.startswith("https://ecrie.com.br/"), f"{family}: unexpected source host")
        _require(source_url.endswith(url_suffix), f"{family}: source URL drift")
        _require(record.get("custody_status") == "PENDING_SOURCE_DOWNLOAD", f"{family}: custody promoted without acquisition")
        _require(record.get("sha256") is None, f"{family}: hash must remain unknown before acquisition")
        _require(record.get("textual_representation_observed_publicly") is True, f"{family}: public text observation missing")

    extraction = data.get("extraction_policy", {})
    _require(extraction.get("input") == "FULL_JOURNAL_EDITION_UNMODIFIED", "extraction input drift")
    _require(extraction.get("page_boundaries_are_hints_not_identity") is True, "page-boundary guard disabled")
    _require(extraction.get("standalone_copy_is_validation_or_recovery_source") is True, "standalone validation role disabled")
    _require(extraction.get("ocr_only_if_journal_page_has_insufficient_text_layer") is True, "OCR fallback policy drift")
    _require(extraction.get("silent_cross_source_substitution") is False, "silent substitution enabled")

    promotion = data.get("promotion", {})
    for key in ("source_custody", "bronze", "silver", "gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"unauthorized promotion: {key}")

    return {
        "status": "PASS_TASK_031_BUDGET_LAWS_JOURNAL_SOURCE_FIRST",
        "primary_source": "JORNAL_OFICIAL_LIMEIRA_FULL_EDITION_PDF",
        "editions": [7024, 7119, 7127],
        "equivalence_required_before_extraction": False,
        "custody_required_before_extraction": True,
        "live_acquisition_authorized": False,
    }
