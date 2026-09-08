from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from robo_dados_publicos.analytics.task217_jom_school_identity_bridge import (
    build_alias_index,
    classify_event_school_identity,
    load_config as load_identity_config,
    normalize_text,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task217b_jom_2026_school_infrastructure_expansion.v1.json"


class Task217BStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task217BStop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK217B_JOM_2026_SCHOOL_INFRA_EXPANSION_V1", "TASK217B_SCHEMA")
    _stop(obj.get("issue") == 680, "TASK217B_ISSUE")
    _stop(
        obj.get("base_main_sha") == "bd5659a9be61c91a1f72ccbf4e3eaeb7e46a93f6",
        "TASK217B_BASE",
    )
    _stop(obj["scope"]["months"] == list(range(1, 10)), "TASK217B_MONTHS")
    _stop(obj["scope"]["end_date"] == "2026-09-08", "TASK217B_END_DATE")
    _stop(obj["discovery"]["automatic_retry"] is False, "TASK217B_RETRY")
    _stop(obj["discovery"]["alternate_url_guessing"] is False, "TASK217B_URL_GUESS")
    _stop(obj["authorization"]["live_execution_authorized"] is False, "TASK217B_LIVE_DEFAULT")
    _stop(obj["authorization"]["task018_authorization_reuse_allowed"] is False, "TASK217B_TASK018_REUSE")
    _stop(obj["promotion"]["runtime_may_promote_answerability"] is False, "TASK217B_RUNTIME_PROMOTION")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK217B_REMOTE_EFFECT")
    return obj


def month_windows(path: str | Path = DEFAULT_CONFIG) -> list[dict[str, Any]]:
    cfg = load_config(path)
    end_date = cfg["scope"]["end_date"]
    windows = []
    for month in cfg["scope"]["months"]:
        start = f"2026-{month:02d}-01"
        end = end_date if month == 9 else f"2026-{month + 1:02d}-01"
        windows.append(
            {
                "year": 2026,
                "month": month,
                "start_date_inclusive": start,
                "end_date_exclusive": None if month == 9 else end,
                "end_date_inclusive": end_date if month == 9 else None,
            }
        )
    return windows


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_sha: str,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    if not authorization:
        return {"status": "STOP_LIVE_NOT_AUTHORIZED"}
    if authorization.get("task") == "TASK_018" or authorization.get("task018_authorization_reused") is True:
        return {"status": "STOP_TASK018_AUTHORIZATION_REUSE"}
    if authorization.get("synthetic_test_only") is True:
        return {"status": "STOP_SYNTHETIC_AUTHORIZATION_NOT_OPERATIONAL"}

    required = {
        "task": cfg["authorization"]["required_task"],
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "branch": "main",
        "implementation_sha": expected_sha,
        "source": cfg["source"]["family"],
        "operation": cfg["authorization"]["required_operation"],
        "start_date": cfg["scope"]["start_date"],
        "end_date": cfg["scope"]["end_date"],
        "attempt_count": cfg["authorization"]["attempt_count"],
        "owner_authorized": True,
        "drive_write_authorized": False,
        "publication_authorized": False,
        "serving_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        return {"status": "STOP_LIVE_AUTHORIZATION_CONTRACT_MISMATCH"}
    return {"status": "PASS_LIVE_AUTHORIZATION", "scope": {"start_date": required["start_date"], "end_date": required["end_date"]}}


def _validate_document_url(url: Any, cfg: Mapping[str, Any]) -> None:
    parsed = urlparse(str(url or ""))
    _stop(parsed.scheme == "https", "TASK217B_DOCUMENT_HTTPS")
    _stop((parsed.hostname or "").lower() in set(cfg["source"]["allowed_document_hosts"]), "TASK217B_DOCUMENT_HOST")


def validate_month_discovery(
    report: Mapping[str, Any],
    *,
    year: int,
    month: int,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    _stop(report.get("status") == "PASS_DISCOVERY", "TASK217B_DISCOVERY_NOT_COMPLETE")
    _stop(report.get("year") == year and report.get("month") == month, "TASK217B_DISCOVERY_SCOPE")
    pages = report.get("pages_fetched")
    _stop(isinstance(pages, int) and not isinstance(pages, bool), "TASK217B_DISCOVERY_PAGES_TYPE")
    _stop(1 <= pages <= cfg["discovery"]["max_pages_per_month"], "TASK217B_DISCOVERY_PAGE_BOUND")

    editions = report.get("editions")
    _stop(isinstance(editions, list), "TASK217B_DISCOVERY_EDITIONS")
    _stop(report.get("count") == len(editions), "TASK217B_DISCOVERY_COUNT")

    seen_editions: set[int] = set()
    seen_sources: set[str] = set()
    sanitized = []
    for row in editions:
        edition = row.get("edition")
        _stop(isinstance(edition, int) and not isinstance(edition, bool) and edition > 0, "TASK217B_EDITION")
        _stop(edition not in seen_editions, "TASK217B_DUPLICATE_EDITION_MONTH")
        seen_editions.add(edition)
        source_id = row.get("source_id")
        _stop(source_id == f"LIMEIRA_JO_{edition:05d}", "TASK217B_SOURCE_ID")
        _stop(source_id not in seen_sources, "TASK217B_DUPLICATE_SOURCE_MONTH")
        seen_sources.add(source_id)

        publication_date = str(row.get("publication_date") or "")
        _stop(publication_date.startswith(f"{year:04d}-{month:02d}-"), "TASK217B_PUBLICATION_MONTH")
        _stop(publication_date <= cfg["scope"]["end_date"], "TASK217B_AFTER_SCOPE_END")
        _validate_document_url(row.get("document_url"), cfg)
        sanitized.append(
            {
                "edition": edition,
                "publication_date": publication_date,
                "document_url": row["document_url"],
                "source_id": source_id,
                "logical_key": row.get("logical_key"),
            }
        )
    return {
        "year": year,
        "month": month,
        "pages_fetched": pages,
        "count": len(sanitized),
        "editions": sorted(sanitized, key=lambda x: x["edition"]),
    }


def build_discovery_plan(
    reports: list[Mapping[str, Any]],
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    months = cfg["scope"]["months"]
    _stop(len(reports) == len(months), "TASK217B_MONTH_REPORT_COUNT")

    validated = [
        validate_month_discovery(report, year=2026, month=month, config_path=config_path)
        for report, month in zip(reports, months)
    ]
    total_pages = sum(row["pages_fetched"] for row in validated)
    _stop(total_pages <= cfg["discovery"]["max_total_index_pages"], "TASK217B_TOTAL_INDEX_PAGES")

    docs = [doc for row in validated for doc in row["editions"]]
    _stop(len(docs) <= cfg["discovery"]["max_documents"], "TASK217B_DOCUMENT_BOUND")
    editions = [doc["edition"] for doc in docs]
    sources = [doc["source_id"] for doc in docs]
    _stop(len(set(editions)) == len(editions), "TASK217B_DUPLICATE_EDITION_CROSS_MONTH")
    _stop(len(set(sources)) == len(sources), "TASK217B_DUPLICATE_SOURCE_CROSS_MONTH")

    return {
        "schema": "TASK217B_JOM_2026_DISCOVERY_PLAN_V1",
        "scope": {
            "start_date": cfg["scope"]["start_date"],
            "end_date": cfg["scope"]["end_date"],
            "months_complete": len(validated),
        },
        "total_index_pages": total_pages,
        "document_count": len(docs),
        "documents": sorted(docs, key=lambda x: (x["publication_date"], x["edition"])),
        "complete_scope": True,
        "document_downloads_performed": 0,
        "network_performed_by_this_function": False,
    }


def _contains_phrase(text: str, phrase: str) -> bool:
    return f" {normalize_text(phrase)} " in f" {normalize_text(text)} "


def screen_page_text(
    text: str,
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    identity_cfg = load_identity_config(ROOT / cfg["identity"]["task217a_config"])
    normalized = normalize_text(text)
    aliases = build_alias_index(ROOT / cfg["identity"]["task217a_config"])["aliases"]

    school_codes: set[str] = set()
    for alias, schools in aliases.items():
        if f" {alias} " in f" {normalized} ":
            school_codes.update(row["school_code"] for row in schools)

    infrastructure_markers = [
        marker for marker in identity_cfg["infrastructure_markers"]
        if _contains_phrase(normalized, marker)
    ]
    generic_school_markers = [
        marker for marker in identity_cfg["generic_school_references"]
        if _contains_phrase(normalized, marker)
    ]
    return {
        "candidate_page": bool(infrastructure_markers and (school_codes or generic_school_markers)),
        "exact_school_codes_present": sorted(school_codes),
        "generic_school_markers": sorted(generic_school_markers),
        "infrastructure_markers": sorted(infrastructure_markers),
        "page_screening_created_school_identity": False,
    }


def adjudicate_event_rows(
    events: list[Mapping[str, Any]],
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    identity_path = ROOT / cfg["identity"]["task217a_config"]
    classified = [
        classify_event_school_identity(event, config_path=identity_path)
        for event in events
    ]
    resolved = [
        row for row in classified
        if row["school_identity_status"] == "RESOLVED_EXACT_SCHOOL"
        and row["infrastructure_candidate"]
    ]
    generic = [
        row for row in classified
        if row["school_identity_status"] == "GENERIC_SCHOOL_REFERENCE"
        and row["infrastructure_candidate"]
    ]
    return {
        "schema": "TASK217B_EXPANDED_EVENT_ADJUDICATION_V1",
        "input_event_count": len(events),
        "resolved_exact_school_infrastructure_count": len(resolved),
        "generic_unassigned_school_infrastructure_count": len(generic),
        "resolved_exact_school_infrastructure_events": resolved,
        "generic_unassigned_school_infrastructure_events": generic,
        "runtime_answerability_promotion": False,
        "canonization_required": bool(resolved),
        "zero_exact_match_means_global_absence": False,
    }


def validate_offline_design(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(path)
    return {
        "schema": "TASK217B_OFFLINE_DESIGN_VALIDATION_V1",
        "status": "PASS",
        "month_window_count": len(month_windows(path)),
        "live_execution_authorized": cfg["authorization"]["live_execution_authorized"],
        "task018_authorization_reuse_allowed": cfg["authorization"]["task018_authorization_reuse_allowed"],
        "runtime_answerability_promotion_allowed": cfg["promotion"]["runtime_may_promote_answerability"],
        "network": False,
        "drive_write": False,
        "publication": False,
        "serving": False,
    }
