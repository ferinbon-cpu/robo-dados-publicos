from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

from robo_dados_publicos.journal.official import JornalOficialLimeira

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task247_jom_rolling_discovery.v1.json"


class DiscoverySource(Protocol):
    network_capable: bool

    def discover_month(self, year: int, month: int, *, max_pages: int) -> dict[str, Any]: ...


class LiveJournalDiscoverySource:
    network_capable = True

    def __init__(self, journal: JornalOficialLimeira | None = None):
        self.journal = journal or JornalOficialLimeira()

    def discover_month(self, year: int, month: int, *, max_pages: int) -> dict[str, Any]:
        return self.journal.discover_month(year, month, max_pages=max_pages)


class Task247Stop(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task247Stop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(cfg.get("schema") == "TASK247_JOM_ROLLING_DISCOVERY_V1", "TASK247_SCHEMA")
    _require(cfg.get("task") == "TASK_247", "TASK247_TASK")
    _require(cfg.get("issue") == 821, "TASK247_ISSUE")
    _require(cfg.get("base_main_sha") == "4180c9784a9583a5e3394f13f60678e6100c5bf0", "TASK247_BASE")
    _require(cfg.get("mode") == "T0_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION", "TASK247_MODE")
    _require(cfg.get("implementation_branch") == "main", "TASK247_IMPLEMENTATION_BRANCH")
    _require(cfg.get("runtime_branch") == "task-247-jom-rolling-discovery-runtime", "TASK247_RUNTIME_BRANCH")

    baseline = cfg["baseline"]
    _require(baseline["canonical_status"] == "PASS_COMPLETE_DISCOVERY_CANONIZED", "TASK247_BASELINE_STATUS")
    _require(baseline["through_date"] == "2026-09-08", "TASK247_BASELINE_DATE")
    _require(baseline["total_document_count"] == 99, "TASK247_BASELINE_COUNT")
    _require(baseline["september_count"] == 5, "TASK247_BASELINE_SEPTEMBER_COUNT")
    _require(baseline["september_editions"] == [7316, 7317, 7318, 7319, 7320], "TASK247_BASELINE_SEPTEMBER_EDITIONS")

    scope = cfg["scope"]
    _require(scope == {"year": 2026, "month": 9, "start_date": "2026-09-09", "end_date": "2026-09-16"}, "TASK247_SCOPE")
    discovery = cfg["discovery"]
    _require(discovery["max_pages_per_month"] == 5, "TASK247_PAGE_BOUND")
    _require(discovery["max_remote_get_count"] == 10, "TASK247_GET_BOUND")
    _require(discovery["automatic_retry"] is False, "TASK247_RETRY")
    _require(discovery["document_downloads"] == 0, "TASK247_PDF_DOWNLOAD")
    _require(discovery["raw_html_persisted"] is False, "TASK247_RAW_HTML")
    _require(discovery["raw_pdf_persisted"] is False, "TASK247_RAW_PDF")

    auth = cfg["authorization"]
    for key in (
        "document_downloads_authorized",
        "drive_write_authorized",
        "serving_authorized",
        "publication_authorized",
        "promotion_authorized",
        "recurrence_authorized",
        "schedule_authorized",
    ):
        _require(auth[key] is False, f"TASK247_AUTH_{key.upper()}")
    persistence = cfg["persistence"]
    _require(persistence["sanitized_discovery_artifact"] is True, "TASK247_SANITIZED_ARTIFACT")
    _require(persistence["artifact_retention_days"] == 1, "TASK247_ARTIFACT_RETENTION")
    _require(persistence["drive_write"] is False, "TASK247_DRIVE_WRITE")
    _require(persistence["serving_write"] is False, "TASK247_SERVING_WRITE")
    _require(persistence["publication"] is False, "TASK247_PUBLICATION")

    evidence = json.loads((ROOT / baseline["canonical_evidence"]).read_text(encoding="utf-8"))
    _require(evidence.get("status") == baseline["canonical_status"], "TASK247_CANONICAL_EVIDENCE_STATUS")
    _require(evidence.get("sanitized_result_sha256") == baseline["sanitized_result_sha256"], "TASK247_CANONICAL_EVIDENCE_HASH")
    _require(evidence.get("scope", {}).get("total_documents") == baseline["total_document_count"], "TASK247_CANONICAL_EVIDENCE_COUNT")
    _require(evidence.get("scope", {}).get("2026-09_through_08") == baseline["september_count"], "TASK247_CANONICAL_EVIDENCE_SEPTEMBER")

    partition = json.loads((ROOT / baseline["partition_contract"]).read_text(encoding="utf-8"))
    _require(partition.get("partitions", {}).get("2026-09") == baseline["september_editions"], "TASK247_PARTITION_BASELINE_DRIFT")
    return cfg


def stop(code: str, **details: Any) -> dict[str, Any]:
    return {
        "schema": "TASK247_JOM_ROLLING_DISCOVERY_RESULT_V1",
        "status": code,
        "baseline_verified": False,
        "observed_window_complete": False,
        "absence_inference_allowed": False,
        "document_download_count": 0,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "recurrence_performed": False,
        "schedule_performed": False,
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
    if authorization.get("synthetic_test_only") is True:
        return stop("STOP_SYNTHETIC_AUTHORIZATION_NOT_OPERATIONAL")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_implementation_sha or ""):
        return stop("STOP_IMPLEMENTATION_SHA_FORMAT")

    required = {
        "task": cfg["authorization"]["required_task"],
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "implementation_branch": cfg["implementation_branch"],
        "runtime_branch": cfg["runtime_branch"],
        "implementation_sha": expected_implementation_sha,
        "source": cfg["source"]["family"],
        "operation": cfg["authorization"]["required_operation"],
        "start_date": cfg["scope"]["start_date"],
        "end_date": cfg["scope"]["end_date"],
        "max_remote_get_count": cfg["discovery"]["max_remote_get_count"],
        "attempt_count": cfg["authorization"]["attempt_count"],
        "owner_authorized": True,
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
        "schema": "TASK247_LIVE_AUTHORIZATION_RESULT_V1",
        "status": "PASS_LIVE_AUTHORIZATION",
        "implementation_sha": expected_implementation_sha,
        "scope": {"start_date": required["start_date"], "end_date": required["end_date"]},
        "max_remote_get_count": required["max_remote_get_count"],
    }


def _validate_month_report(report: Mapping[str, Any], cfg: Mapping[str, Any]) -> list[dict[str, Any]]:
    _require(report.get("status") == "PASS_DISCOVERY", "TASK247_DISCOVERY_NOT_COMPLETE")
    _require(report.get("year") == cfg["scope"]["year"], "TASK247_DISCOVERY_YEAR")
    _require(report.get("month") == cfg["scope"]["month"], "TASK247_DISCOVERY_MONTH")
    pages = report.get("pages_fetched")
    _require(isinstance(pages, int) and not isinstance(pages, bool), "TASK247_PAGES_TYPE")
    _require(1 <= pages <= cfg["discovery"]["max_pages_per_month"], "TASK247_PAGES_BOUND")
    _require(pages * 2 <= cfg["discovery"]["max_remote_get_count"], "TASK247_REMOTE_GET_BOUND")

    editions = report.get("editions")
    _require(isinstance(editions, list), "TASK247_EDITIONS_TYPE")
    _require(report.get("count") == len(editions), "TASK247_COUNT_DRIFT")
    seen_editions: set[int] = set()
    seen_sources: set[str] = set()
    sanitized: list[dict[str, Any]] = []
    allowed_hosts = {str(x).lower() for x in cfg["source"]["allowed_document_hosts"]}
    month_prefix = f"{cfg['scope']['year']:04d}-{cfg['scope']['month']:02d}-"

    for row in editions:
        edition = row.get("edition")
        _require(isinstance(edition, int) and not isinstance(edition, bool) and edition > 0, "TASK247_EDITION")
        _require(edition not in seen_editions, "TASK247_DUPLICATE_EDITION")
        seen_editions.add(edition)
        source_id = row.get("source_id")
        _require(source_id == f"LIMEIRA_JO_{edition:05d}", "TASK247_SOURCE_ID")
        _require(source_id not in seen_sources, "TASK247_DUPLICATE_SOURCE")
        seen_sources.add(source_id)

        publication_date = str(row.get("publication_date") or "")
        _require(publication_date.startswith(month_prefix), "TASK247_PUBLICATION_MONTH")
        _require(publication_date <= cfg["scope"]["end_date"], "TASK247_AFTER_AUTHORIZED_END")
        parsed = urlparse(str(row.get("document_url") or ""))
        _require(parsed.scheme == "https", "TASK247_DOCUMENT_HTTPS")
        _require((parsed.hostname or "").lower() in allowed_hosts, "TASK247_DOCUMENT_HOST")
        sanitized.append(
            {
                "edition": edition,
                "publication_date": publication_date,
                "document_url": str(row["document_url"]),
                "source_id": source_id,
                "logical_key": row.get("logical_key"),
            }
        )
    return sorted(sanitized, key=lambda x: (x["publication_date"], x["edition"]))


def build_delta(report: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    rows = _validate_month_report(report, cfg)
    baseline_ids = set(cfg["baseline"]["september_editions"])
    pre_delta = [row for row in rows if row["publication_date"] < cfg["scope"]["start_date"]]
    pre_delta_ids = {row["edition"] for row in pre_delta}
    _require(pre_delta_ids == baseline_ids, "TASK247_BASELINE_HISTORY_DRIFT")
    _require(len(pre_delta) == cfg["baseline"]["september_count"], "TASK247_BASELINE_COUNT_DRIFT")

    delta = [
        row for row in rows
        if cfg["scope"]["start_date"] <= row["publication_date"] <= cfg["scope"]["end_date"]
    ]
    _require(not baseline_ids.intersection({row["edition"] for row in delta}), "TASK247_BASELINE_DELTA_OVERLAP")
    return {
        "baseline_ids": sorted(baseline_ids),
        "delta": delta,
        "pages_fetched": int(report["pages_fetched"]),
        "observed_month_count": len(rows),
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
        if auth.get("status") != "PASS_LIVE_AUTHORIZATION":
            return auth
        if not getattr(source, "network_capable", False):
            return stop("STOP_LIVE_SOURCE_NOT_NETWORK_CAPABLE")

    try:
        report = source.discover_month(
            int(config["scope"]["year"]),
            int(config["scope"]["month"]),
            max_pages=int(config["discovery"]["max_pages_per_month"]),
        )
    except Exception as exc:
        return stop("STOP_SOURCE_DISCOVERY_EXCEPTION", error_class=type(exc).__name__)

    try:
        delta = build_delta(report, config)
    except Exception as exc:
        return stop(str(exc) if isinstance(exc, Task247Stop) else "STOP_DELTA_VALIDATION_EXCEPTION", error_class=type(exc).__name__)

    return {
        "schema": "TASK247_JOM_ROLLING_DISCOVERY_RESULT_V1",
        "status": "PASS_JOM_ROLLING_DELTA_DISCOVERY",
        "baseline_verified": True,
        "baseline": {
            "through_date": config["baseline"]["through_date"],
            "total_document_count": config["baseline"]["total_document_count"],
            "september_editions": delta["baseline_ids"],
        },
        "scope": dict(config["scope"]),
        "observed_window_complete": True,
        "observed_month_count": delta["observed_month_count"],
        "delta_count": len(delta["delta"]),
        "delta_editions": delta["delta"],
        "index_pages_fetched": delta["pages_fetched"],
        "estimated_remote_get_count": delta["pages_fetched"] * 2,
        "document_download_count": 0,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "recurrence_performed": False,
        "schedule_performed": False,
        "absence_inference_allowed": False,
        "future_editions_inference_allowed": False,
        "next_step": "CANONIZE_LIVE_DELTA_BEFORE_ANY_DOCUMENT_DOWNLOAD_OR_RECURRENCE_PROMOTION",
    }


def validate_offline_carrier(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(config_path)
    return {
        "schema": "TASK247_OFFLINE_CARRIER_VALIDATION_V1",
        "status": "PASS",
        "baseline_total": cfg["baseline"]["total_document_count"],
        "baseline_through": cfg["baseline"]["through_date"],
        "delta_start": cfg["scope"]["start_date"],
        "delta_end": cfg["scope"]["end_date"],
        "max_remote_get_count": cfg["discovery"]["max_remote_get_count"],
        "document_downloads": 0,
        "network": False,
        "drive_write": False,
        "serving_write": False,
        "publication": False,
        "promotion": False,
        "recurrence": False,
        "schedule": False,
    }
