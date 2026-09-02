from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BudgetPublicationMapStop(ValueError):
    """Fail-closed validation error for the budget-law publication map."""


def load_budget_publication_map(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_budget_publication_map(data)
    return data


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BudgetPublicationMapStop(message)


def validate_budget_publication_map(data: dict[str, Any]) -> dict[str, Any]:
    _require(data.get("mode") == "T0_OFFLINE_PUBLICATION_MAPPING", "unexpected mode")
    _require(data.get("publication_source") == "JORNAL_OFICIAL_LIMEIRA", "wrong publication source")
    _require(data.get("source_role") == "PRIMARY_LEGAL_PUBLICATION", "wrong source role")

    records = data.get("records")
    _require(isinstance(records, list) and len(records) == 3, "expected exactly PPA/LDO/LOA records")

    by_type = {record.get("document_type"): record for record in records}
    _require(set(by_type) == {"PPA", "LDO", "LOA"}, "document family drift")

    expected = {
        "PPA": {
            "law_number": "7.213/2025",
            "journal_edition": 7119,
            "journal_date": "2025-11-15",
            "journal_start_page": 5,
            "journal_section_end_page": 76,
            "standalone_pages": 105,
            "journal_verified_end_page": None,
            "content_equivalence_status": "FULL_CONTENT_EQUIVALENCE_PENDING",
        },
        "LDO": {
            "law_number": "7.141/2025",
            "journal_edition": 7024,
            "journal_date": "2025-07-08",
            "journal_start_page": 5,
            "journal_verified_end_page": 41,
            "standalone_pages": 37,
            "content_equivalence_status": "PAGE_COUNT_ALIGNMENT_PROVEN_BYTE_EQUIVALENCE_NOT_CLAIMED",
        },
        "LOA": {
            "law_number": "7.223/2025",
            "journal_edition": 7127,
            "journal_date": "2025-11-29",
            "journal_start_page": 15,
            "journal_candidate_end_page": 480,
            "journal_section_end_page": 484,
            "standalone_pages": 466,
            "journal_verified_end_page": None,
            "content_equivalence_status": "FULL_PAGE_EQUIVALENCE_PENDING",
        },
    }

    for document_type, expected_fields in expected.items():
        record = by_type[document_type]
        _require(record.get("relationship_status") == "SAME_LEGAL_INSTRUMENT_PROVEN", f"{document_type}: legal identity not proven")
        _require(record.get("textual_representation") is True, f"{document_type}: journal textual representation not recorded")
        _require(str(record.get("journal_url", "")).startswith("https://ecrie.com.br/"), f"{document_type}: non-official journal URL")
        for field, value in expected_fields.items():
            _require(record.get(field) == value, f"{document_type}: {field} drift")

    ldo = by_type["LDO"]
    ldo_count = ldo["journal_verified_end_page"] - ldo["journal_start_page"] + 1
    _require(ldo_count == ldo["standalone_pages"] == 37, "LDO page-count alignment drift")

    loa = by_type["LOA"]
    candidate_end = loa["journal_start_page"] + loa["standalone_pages"] - 1
    _require(candidate_end == loa["journal_candidate_end_page"] == 480, "LOA candidate-end arithmetic drift")
    _require(loa["journal_candidate_end_page"] < loa["journal_section_end_page"], "LOA candidate end outside Gabinete boundary")
    _require(loa["journal_verified_end_page"] is None, "LOA candidate end must not be silently promoted")

    ppa = by_type["PPA"]
    _require(ppa["journal_verified_end_page"] is None, "PPA end page remains unverified")

    guardrails = data.get("guardrails", {})
    false_guards = (
        "journal_replaces_canonical_pdf_without_equivalence_proof",
        "infer_full_equivalence_from_same_law_number",
        "infer_full_equivalence_from_page_count_alignment",
        "infer_verified_end_from_section_boundary",
        "silent_correction",
    )
    for key in false_guards:
        _require(guardrails.get(key) is False, f"unsafe guard enabled: {key}")
    _require(guardrails.get("allow_journal_as_official_textual_validation_bridge") is True, "journal bridge unexpectedly disabled")
    _require(guardrails.get("divergence_action") == "REVIEW_STOP", "divergence must fail closed")

    promotion = data.get("promotion", {})
    _require(all(promotion.get(key) is False for key in ("silver", "gold", "serving", "publication")), "unauthorized promotion")

    return {
        "status": "PASS_TASK_030_BUDGET_LAWS_JOURNAL_PUBLICATION_MAP",
        "records": 3,
        "ldo_page_count_alignment": True,
        "ppa_full_equivalence_pending": True,
        "loa_full_equivalence_pending": True,
        "promotion_authorized": False,
    }
