from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any


COORDINATE_SYSTEMS = (
    "JOURNAL_EDITION_PDF_PAGE",
    "STANDALONE_PDF_PAGE",
    "DOCUMENT_INTERNAL_PRINTED_PAGE",
    "REPORT_LINE",
    "LEGACY_UNTYPED_PAGE",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceLocatorStop(RuntimeError):
    """Fail-closed locator/provenance validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ProvenanceLocatorStop(code)


def _sha256(value: object, *, code: str, optional: bool = True) -> str | None:
    if value is None and optional:
        return None
    text = str(value or "")
    _require(bool(_SHA256_RE.fullmatch(text)), code)
    return text


def validate_locator(locator: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(locator, dict), "TASK097_LOCATOR_OBJECT")
    system = str(locator.get("coordinate_system") or "")
    _require(system in COORDINATE_SYSTEMS, "TASK097_COORDINATE_SYSTEM")

    page = locator.get("page")
    _require(
        isinstance(page, int) and not isinstance(page, bool) and page >= 1,
        "TASK097_PAGE",
    )
    source_key = str(locator.get("source_key") or "").strip()
    _require(source_key != "", "TASK097_SOURCE_KEY")
    source_sha256 = _sha256(
        locator.get("source_sha256"),
        code="TASK097_SOURCE_SHA256",
        optional=True,
    )
    page_text_sha256 = _sha256(
        locator.get("page_text_sha256"),
        code="TASK097_PAGE_TEXT_SHA256",
        optional=True,
    )

    if system == "LEGACY_UNTYPED_PAGE":
        _require(
            source_sha256 is None,
            "TASK097_LEGACY_UNTYPED_MUST_NOT_GAIN_INVENTED_SOURCE_HASH",
        )
    if page_text_sha256 is not None:
        _require(source_sha256 is not None, "TASK097_PAGE_HASH_WITHOUT_SOURCE_HASH")

    return {
        "page": page,
        "coordinate_system": system,
        "source_key": source_key,
        "source_sha256": source_sha256,
        "page_text_sha256": page_text_sha256,
    }


def compare_page_locators(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    proven_offset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    a = validate_locator(left)
    b = validate_locator(right)

    if (
        a["coordinate_system"] == b["coordinate_system"]
        and a["source_sha256"] is not None
        and a["source_sha256"] == b["source_sha256"]
    ):
        return {
            "status": "PROVEN_SAME_COORDINATE_SYSTEM",
            "equivalent_page": a["page"] == b["page"],
            "left": a,
            "right": b,
            "basis": "SAME_COORDINATE_SYSTEM_AND_SOURCE_SHA256",
        }

    if proven_offset is not None:
        _require(isinstance(proven_offset, dict), "TASK097_OFFSET_OBJECT")
        offset = proven_offset.get("right_minus_left")
        _require(
            isinstance(offset, int) and not isinstance(offset, bool),
            "TASK097_OFFSET_VALUE",
        )
        basis = str(proven_offset.get("basis") or "").strip()
        _require(basis != "", "TASK097_OFFSET_BASIS")
        basis_sha = _sha256(
            proven_offset.get("basis_sha256"),
            code="TASK097_OFFSET_BASIS_SHA256",
            optional=False,
        )
        _require(
            a["coordinate_system"] != "LEGACY_UNTYPED_PAGE"
            and b["coordinate_system"] != "LEGACY_UNTYPED_PAGE",
            "TASK097_OFFSET_CANNOT_RESOLVE_UNTYPED_LEGACY_PAGE",
        )
        return {
            "status": "PROVEN_EXPLICIT_OFFSET",
            "equivalent_page": b["page"] - a["page"] == offset,
            "left": a,
            "right": b,
            "basis": basis,
            "basis_sha256": basis_sha,
            "right_minus_left": offset,
        }

    if "LEGACY_UNTYPED_PAGE" in {
        a["coordinate_system"],
        b["coordinate_system"],
    }:
        status = "UNRESOLVED_LEGACY_COORDINATE_SYSTEM"
    else:
        status = "UNRESOLVED_CROSS_COORDINATE_SYSTEM"

    return {
        "status": status,
        "equivalent_page": None,
        "left": a,
        "right": b,
        "basis": "INSUFFICIENT_PROVENANCE_FOR_PAGE_EQUIVALENCE",
    }


def normalize_task097_ppa_locator_case(contract: dict[str, Any]) -> dict[str, Any]:
    _require(contract.get("schema") == "RESEARCH_LOCATOR_PROVENANCE_V1", "TASK097_SCHEMA")
    _require(contract.get("mode") == "T0_OFFLINE_PROVENANCE_NORMALIZATION", "TASK097_MODE")
    remote = contract.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK097_REMOTE_EFFECT")

    case = contract.get("task097_case") or {}
    legacy = validate_locator(case.get("legacy_locator") or {})
    primary = validate_locator(case.get("primary_journal_locator") or {})
    result = compare_page_locators(legacy, primary)

    _require(
        result["status"] == "UNRESOLVED_LEGACY_COORDINATE_SYSTEM",
        "TASK097_CASE_MUST_REMAIN_UNRESOLVED",
    )
    _require(result["equivalent_page"] is None, "TASK097_EQUIVALENCE_OVERCLAIM")
    _require(case.get("legacy_locator_preserved") is True, "TASK097_LEGACY_NOT_PRESERVED")
    _require(
        case.get("preferred_new_citation_locator") == "PRIMARY_JOURNAL_PAGE_15",
        "TASK097_PRIMARY_LOCATOR_PREFERENCE",
    )

    return {
        "status": "PASS_TASK097_PPA_LOCATOR_PROVENANCE_NORMALIZED_NO_EQUIVALENCE_CLAIM",
        "legacy_page": legacy["page"],
        "primary_journal_page": primary["page"],
        "equivalence_status": result["status"],
        "preferred_new_citation_locator": case["preferred_new_citation_locator"],
        "remote_effects": 0,
    }


def load_locator_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(data.get("schema") == "RESEARCH_LOCATOR_PROVENANCE_V1", "TASK097_CONTRACT_SCHEMA")
    _require(tuple(data.get("coordinate_systems") or ()) == COORDINATE_SYSTEMS, "TASK097_CONTRACT_COORDINATE_SYSTEMS")
    return deepcopy(data)
