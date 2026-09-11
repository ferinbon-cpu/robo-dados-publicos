from __future__ import annotations

from datetime import date
from typing import Any, Mapping
from urllib.parse import urlparse

WINDOW_START = date(2025, 12, 17)
WINDOW_END = date(2026, 1, 31)
ALLOWED_DOCUMENT_HOSTS = frozenset({"ecrie.com.br", "www.limeira.sp.gov.br", "limeira.sp.gov.br"})
EXPECTED_MONTHS = ((2025, 12), (2026, 1))


class Task238Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task238Stop(code)


def _parse_iso_day(value: Any) -> date:
    _stop(isinstance(value, str), "TASK238_PUBLICATION_DATE_TYPE")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise Task238Stop("TASK238_PUBLICATION_DATE_FORMAT") from exc
    return parsed


def _validate_document_url(value: Any) -> str:
    _stop(isinstance(value, str), "TASK238_DOCUMENT_URL_TYPE")
    parsed = urlparse(value)
    _stop(parsed.scheme == "https", "TASK238_DOCUMENT_URL_HTTPS")
    _stop((parsed.hostname or "").lower() in ALLOWED_DOCUMENT_HOSTS, "TASK238_DOCUMENT_URL_HOST")
    return value


def validate_month_report(report: Mapping[str, Any], *, year: int, month: int) -> dict[str, Any]:
    _stop(report.get("status") == "PASS_DISCOVERY", "TASK238_MONTH_DISCOVERY_NOT_COMPLETE")
    _stop(report.get("year") == year and report.get("month") == month, "TASK238_MONTH_SCOPE")

    pages = report.get("pages_fetched")
    _stop(isinstance(pages, int) and not isinstance(pages, bool) and 1 <= pages <= 8, "TASK238_PAGE_BOUND")

    editions = report.get("editions")
    _stop(isinstance(editions, list), "TASK238_EDITIONS_TYPE")
    _stop(report.get("count") == len(editions), "TASK238_COUNT_MISMATCH")

    reported_total = report.get("reported_total_items")
    _stop(isinstance(reported_total, int) and not isinstance(reported_total, bool), "TASK238_REPORTED_TOTAL_TYPE")
    _stop(reported_total == len(editions), "TASK238_REPORTED_TOTAL_NOT_RECONCILED")

    seen_editions: set[int] = set()
    seen_sources: set[str] = set()
    rows: list[dict[str, Any]] = []
    for raw in editions:
        _stop(isinstance(raw, Mapping), "TASK238_EDITION_ROW_TYPE")
        edition = raw.get("edition")
        _stop(isinstance(edition, int) and not isinstance(edition, bool) and edition > 0, "TASK238_EDITION_ID")
        _stop(edition not in seen_editions, "TASK238_DUPLICATE_EDITION")
        seen_editions.add(edition)

        source_id = raw.get("source_id")
        _stop(source_id == f"LIMEIRA_JO_{edition:05d}", "TASK238_SOURCE_ID")
        _stop(source_id not in seen_sources, "TASK238_DUPLICATE_SOURCE_ID")
        seen_sources.add(source_id)

        logical_key = raw.get("logical_key")
        _stop(logical_key == f"limeira/jornal_oficial/edicao/{edition}", "TASK238_LOGICAL_KEY")

        publication_day = _parse_iso_day(raw.get("publication_date"))
        _stop((publication_day.year, publication_day.month) == (year, month), "TASK238_PUBLICATION_MONTH")
        document_url = _validate_document_url(raw.get("document_url"))

        rows.append(
            {
                "edition": edition,
                "publication_date": publication_day.isoformat(),
                "source_id": source_id,
                "logical_key": logical_key,
                "document_url": document_url,
            }
        )

    rows.sort(key=lambda row: (row["publication_date"], row["edition"]))
    return {
        "year": year,
        "month": month,
        "pages_fetched": pages,
        "reported_total_items": reported_total,
        "count": len(rows),
        "editions": rows,
    }


def build_bounded_window_inventory(reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    _stop(len(reports) == 2, "TASK238_MONTH_REPORT_COUNT")
    validated = [
        validate_month_report(report, year=year, month=month)
        for report, (year, month) in zip(reports, EXPECTED_MONTHS)
    ]

    all_rows = [row for month in validated for row in month["editions"]]
    editions = [row["edition"] for row in all_rows]
    sources = [row["source_id"] for row in all_rows]
    _stop(len(set(editions)) == len(editions), "TASK238_DUPLICATE_EDITION_CROSS_MONTH")
    _stop(len(set(sources)) == len(sources), "TASK238_DUPLICATE_SOURCE_CROSS_MONTH")

    bounded = []
    for row in all_rows:
        day = _parse_iso_day(row["publication_date"])
        if WINDOW_START <= day <= WINDOW_END:
            bounded.append(dict(row))

    bounded.sort(key=lambda row: (row["publication_date"], row["edition"]))
    _stop(bool(bounded), "TASK238_EMPTY_BOUNDED_WINDOW")

    return {
        "schema": "TASK238_LT_MODIFIER_JOM_WINDOW_INVENTORY_V1",
        "status": "PASS_COMPLETE_BOUNDED_WINDOW_INVENTORY",
        "window": {"start_date": WINDOW_START.isoformat(), "end_date": WINDOW_END.isoformat()},
        "months_complete": 2,
        "month_reports": [
            {
                "year": month["year"],
                "month": month["month"],
                "count": month["count"],
                "reported_total_items": month["reported_total_items"],
                "pages_fetched": month["pages_fetched"],
            }
            for month in validated
        ],
        "window_document_count": len(bounded),
        "documents": bounded,
        "content_inspection_performed": False,
        "modifier_candidate_established": False,
        "absence_inference_allowed": False,
        "next_step": "SEPARATE_BOUNDED_PRIMARY_DOCUMENT_CONTENT_INSPECTION_REQUIRED",
    }


def fail_closed_result(code: str, **details: Any) -> dict[str, Any]:
    return {
        "schema": "TASK238_LT_MODIFIER_JOM_WINDOW_INVENTORY_V1",
        "status": code,
        "complete_window_inventory": False,
        "content_inspection_performed": False,
        "modifier_candidate_established": False,
        "absence_inference_allowed": False,
        **details,
    }


def evaluate_reports(reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    try:
        return build_bounded_window_inventory(reports)
    except Task238Stop as exc:
        return fail_closed_result(str(exc))
