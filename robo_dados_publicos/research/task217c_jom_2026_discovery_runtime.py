from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Protocol

from robo_dados_publicos.journal.official import JornalOficialLimeira
from robo_dados_publicos.research.task217b_jom_2026_school_infrastructure_expansion import (
    Task217BStop,
    build_discovery_plan,
    validate_month_discovery,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task217c_jom_2026_discovery_runtime.v1.json"


class DiscoverySource(Protocol):
    network_capable: bool

    def discover_month(self, year: int, month: int, *, max_pages: int) -> dict[str, Any]: ...


class LiveJournalDiscoverySource:
    network_capable = True

    def __init__(self, journal: JornalOficialLimeira | None = None):
        self.journal = journal or JornalOficialLimeira()

    def discover_month(self, year: int, month: int, *, max_pages: int) -> dict[str, Any]:
        return self.journal.discover_month(year, month, max_pages=max_pages)


class Task217CStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task217CStop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK217C_JOM_2026_DISCOVERY_RUNTIME_V1", "TASK217C_SCHEMA")
    _stop(obj.get("issue") == 680, "TASK217C_ISSUE")
    _stop(
        obj.get("base_main_sha") == "ea16982dfe0333870fde23531848520c0263b492",
        "TASK217C_BASE",
    )
    _stop(obj["scope"]["months"] == list(range(1, 10)), "TASK217C_MONTHS")
    _stop(obj["scope"]["end_date"] == "2026-09-08", "TASK217C_END")
    _stop(obj["discovery"]["max_pages_per_month"] == 5, "TASK217C_MONTH_PAGE_BOUND")
    _stop(obj["discovery"]["max_total_index_pages"] == 45, "TASK217C_TOTAL_PAGE_BOUND")
    _stop(obj["discovery"]["max_remote_get_count"] == 90, "TASK217C_GET_BOUND")
    _stop(obj["discovery"]["automatic_retry"] is False, "TASK217C_RETRY")
    _stop(obj["discovery"]["document_downloads"] == 0, "TASK217C_NO_DOCUMENTS")
    _stop(obj["authorization"]["task018_authorization_reused"] is False, "TASK217C_TASK018")
    _stop(obj["authorization"]["promotion_authorized"] is False, "TASK217C_PROMOTION")
    _stop(all(v is False for v in obj["remote_effects_before_authorization"].values()), "TASK217C_T0_EFFECT")
    return obj


def stop(code: str, **details: Any) -> dict[str, Any]:
    return {
        "schema": "TASK217C_JOM_2026_DISCOVERY_RESULT_V1",
        "status": code,
        "complete_scope": False,
        "absence_inference_allowed": False,
        "document_download_count": 0,
        "drive_write_count": 0,
        "promotion_performed": False,
        **details,
    }


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    if not authorization:
        return stop("STOP_LIVE_NOT_AUTHORIZED")
    if authorization.get("task") == "TASK_018" or authorization.get("task018_authorization_reused") is True:
        return stop("STOP_TASK018_AUTHORIZATION_REUSE")
    if authorization.get("synthetic_test_only") is True:
        return stop("STOP_SYNTHETIC_AUTHORIZATION_NOT_OPERATIONAL")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_implementation_sha or ""):
        return stop("STOP_IMPLEMENTATION_SHA_FORMAT")

    required = {
        "task": cfg["authorization"]["required_task"],
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "implementation_branch": cfg["authorization"]["implementation_branch"],
        "runtime_branch": cfg["runtime_branch"],
        "implementation_sha": expected_implementation_sha,
        "source": cfg["scope"]["source"],
        "operation": cfg["authorization"]["required_operation"],
        "start_date": cfg["scope"]["start_date"],
        "end_date": cfg["scope"]["end_date"],
        "max_remote_get_count": cfg["discovery"]["max_remote_get_count"],
        "attempt_count": cfg["authorization"]["attempt_count"],
        "owner_authorized": True,
        "task018_authorization_reused": False,
        "document_downloads_authorized": False,
        "drive_write_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        return stop("STOP_LIVE_AUTHORIZATION_CONTRACT_MISMATCH")
    return {
        "status": "PASS_LIVE_AUTHORIZATION",
        "implementation_sha": expected_implementation_sha,
        "max_remote_get_count": cfg["discovery"]["max_remote_get_count"],
    }


def execute(
    config: Mapping[str, Any],
    *,
    source: DiscoverySource,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    if offline_test_mode:
        if getattr(source, "network_capable", True):
            return stop("STOP_OFFLINE_TEST_NETWORK_CAPABLE")
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return stop("STOP_OFFLINE_TEST_AUTHORIZATION")
    else:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
        )
        if auth["status"] != "PASS_LIVE_AUTHORIZATION":
            return auth
        if not getattr(source, "network_capable", False):
            return stop("STOP_LIVE_SOURCE_NOT_NETWORK_CAPABLE")

    reports: list[dict[str, Any]] = []
    total_pages = 0
    for month in config["scope"]["months"]:
        try:
            report = source.discover_month(
                2026,
                int(month),
                max_pages=int(config["discovery"]["max_pages_per_month"]),
            )
        except Exception as exc:
            return stop(
                "STOP_SOURCE_DISCOVERY_EXCEPTION",
                failed_month=int(month),
                completed_months=len(reports),
                error_class=type(exc).__name__,
                total_index_pages=total_pages,
                estimated_remote_get_count=total_pages * 2,
            )
        try:
            validated = validate_month_discovery(report, year=2026, month=int(month))
        except (Task217BStop, Exception) as exc:
            return stop(
                "STOP_MONTH_DISCOVERY_CONTRACT",
                failed_month=int(month),
                completed_months=len(reports),
                source_status=report.get("status") if isinstance(report, dict) else None,
                error_class=type(exc).__name__,
                total_index_pages=total_pages,
                estimated_remote_get_count=total_pages * 2,
            )
        total_pages += int(validated["pages_fetched"])
        if total_pages > int(config["discovery"]["max_total_index_pages"]):
            return stop(
                "STOP_TOTAL_INDEX_PAGE_BUDGET",
                failed_month=int(month),
                completed_months=len(reports),
                total_index_pages=total_pages,
                estimated_remote_get_count=total_pages * 2,
            )
        if total_pages * 2 > int(config["discovery"]["max_remote_get_count"]):
            return stop(
                "STOP_REMOTE_GET_BUDGET",
                failed_month=int(month),
                completed_months=len(reports),
                total_index_pages=total_pages,
                estimated_remote_get_count=total_pages * 2,
            )
        reports.append(dict(report))

    try:
        plan = build_discovery_plan(reports)
    except Exception as exc:
        return stop(
            "STOP_AGGREGATE_DISCOVERY_PLAN",
            completed_months=len(reports),
            error_class=type(exc).__name__,
            total_index_pages=total_pages,
            estimated_remote_get_count=total_pages * 2,
        )

    return {
        "schema": "TASK217C_JOM_2026_DISCOVERY_RESULT_V1",
        "status": "PASS_COMPLETE_2026_JOM_DISCOVERY_READY_FOR_REDIGEST",
        "complete_scope": True,
        "scope": plan["scope"],
        "total_index_pages": plan["total_index_pages"],
        "estimated_remote_get_count": plan["total_index_pages"] * 2,
        "document_count": plan["document_count"],
        "documents": plan["documents"],
        "document_download_count": 0,
        "raw_html_persisted": False,
        "raw_pdf_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "absence_inference_allowed": False,
        "next_step": "TASK_217D_BOUNDED_DOCUMENT_REDIGEST_REQUIRES_SEPARATE_CANONIZED_SCOPE",
    }


def validate_offline_carrier(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(config_path)
    return {
        "schema": "TASK217C_OFFLINE_CARRIER_VALIDATION_V1",
        "status": "PASS",
        "runtime_branch": cfg["runtime_branch"],
        "months": len(cfg["scope"]["months"]),
        "max_remote_get_count": cfg["discovery"]["max_remote_get_count"],
        "document_downloads": cfg["discovery"]["document_downloads"],
        "live_authorization_present": False,
        "network": False,
        "drive_write": False,
        "promotion": False,
    }
