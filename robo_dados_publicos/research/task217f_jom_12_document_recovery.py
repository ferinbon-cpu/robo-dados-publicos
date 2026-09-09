from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

from robo_dados_publicos.research.task217d_jom_school_infra_redigest import (
    LiveDocumentSource,
    process_document,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task217f_jom_12_document_recovery.v1.json"


class Task217FStop(RuntimeError):
    pass


class DocumentSource(Protocol):
    network_capable: bool
    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict[str, Any]]: ...


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task217FStop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg.get("schema") == "TASK217F_JOM_12_DOCUMENT_RECOVERY_V1", "TASK217F_SCHEMA")
    _stop(cfg.get("issue") == 680, "TASK217F_ISSUE")
    _stop(
        cfg.get("base_main_sha") == "cf949a0970d43c6ac6930a78b563842cd468b4ad",
        "TASK217F_BASE",
    )
    targets = cfg["targets"]
    _stop(len(targets) == 12, "TASK217F_TARGET_COUNT")
    _stop(len({int(row["edition"]) for row in targets}) == 12, "TASK217F_TARGET_DUPLICATE")
    _stop(
        [int(row["edition"]) for row in targets]
        == [7243,7253,7265,7270,7271,7287,7294,7316,7317,7318,7319,7320],
        "TASK217F_TARGET_IDENTITY",
    )
    _stop(all(str(row["url"]).startswith("https://ecrie.com.br/") for row in targets), "TASK217F_TARGET_HOST")
    net = cfg["network"]
    _stop(net["max_document_get_attempt_count"] == 12, "TASK217F_GET_COUNT")
    _stop(net["max_total_remote_get_count"] == 12, "TASK217F_REMOTE_COUNT")
    _stop(net["automatic_retry"] is False, "TASK217F_RETRY")
    _stop(net["rediscovery_authorized"] is False, "TASK217F_REDISCOVERY")
    _stop(
        int(net["max_bytes_per_document"]) * 12 + 12
        <= int(net["max_aggregate_document_bytes"]),
        "TASK217F_BUDGET_MATH",
    )
    _stop(cfg["authorization"]["live_authorized"] is False, "TASK217F_LIVE_DEFAULT")
    _stop(cfg["authorization"]["task217d_authorization_reuse_allowed"] is False, "TASK217F_217D_REUSE")
    _stop(cfg["authorization"]["task018_authorization_reuse_allowed"] is False, "TASK217F_018_REUSE")
    _stop(cfg["promotion"]["runtime_may_promote"] is False, "TASK217F_PROMOTION")
    _stop(all(v is False for v in cfg["pre_authorization_remote_effects"].values()), "TASK217F_T0_EFFECT")
    return cfg


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    if not authorization:
        return {"status": "STOP_LIVE_NOT_AUTHORIZED"}
    if authorization.get("task018_authorization_reused") is True:
        return {"status": "STOP_TASK018_AUTHORIZATION_REUSE"}
    if authorization.get("task217d_authorization_reused") is True:
        return {"status": "STOP_TASK217D_AUTHORIZATION_REUSE"}
    if authorization.get("synthetic_test_only") is True:
        return {"status": "STOP_SYNTHETIC_AUTHORIZATION_NOT_OPERATIONAL"}
    if not re.fullmatch(r"[0-9a-f]{40}", expected_implementation_sha or ""):
        return {"status": "STOP_IMPLEMENTATION_SHA_FORMAT"}

    required = {
        "task": cfg["authorization"]["required_task"],
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "implementation_branch": "main",
        "runtime_branch": cfg["runtime"]["branch"],
        "implementation_sha": expected_implementation_sha,
        "source": "LIMEIRA_JORNAL_OFICIAL",
        "operation": cfg["authorization"]["required_operation"],
        "task217e_partial_result_sha256": cfg["source"]["task217d_embedded_result_sha256"],
        "max_document_get_attempt_count": cfg["network"]["max_document_get_attempt_count"],
        "max_total_remote_get_count": cfg["network"]["max_total_remote_get_count"],
        "max_bytes_per_document": cfg["network"]["max_bytes_per_document"],
        "max_aggregate_document_bytes": cfg["network"]["max_aggregate_document_bytes"],
        "attempt_count": 1,
        "owner_authorized": True,
        "task018_authorization_reused": False,
        "task217d_authorization_reused": False,
        "document_downloads_authorized": True,
        "rediscovery_authorized": False,
        "drive_write_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        return {"status": "STOP_LIVE_AUTHORIZATION_CONTRACT_MISMATCH"}
    return {"status": "PASS_LIVE_AUTHORIZATION"}


def _validate_download(
    item: Mapping[str, Any],
    data: bytes,
    meta: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
) -> None:
    _stop(meta.get("https") is True, "TASK217F_DOWNLOAD_HTTPS")
    _stop(meta.get("final_host") == cfg["network"]["allowed_document_host"], "TASK217F_DOWNLOAD_HOST")
    _stop(meta.get("content_type") == "application/pdf", "TASK217F_DOWNLOAD_CONTENT_TYPE")
    _stop(int(meta.get("remote_get_count") or 0) == 1, "TASK217F_DOWNLOAD_GET_COUNT")
    _stop(len(data) <= int(cfg["network"]["max_bytes_per_document"]), "TASK217F_DOCUMENT_BYTES")
    parsed = urlparse(str(item.get("url") or ""))
    _stop(parsed.scheme == "https", "TASK217F_DECLARED_URL_HTTPS")
    _stop((parsed.hostname or "").lower() == cfg["network"]["allowed_document_host"], "TASK217F_DECLARED_URL_HOST")


def execute_recovery(
    config: Mapping[str, Any],
    *,
    document_source: DocumentSource,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    cfg = dict(config)
    if offline_test_mode:
        if getattr(document_source, "network_capable", True):
            return {"status": "STOP_OFFLINE_TEST_NETWORK_CAPABLE", "complete_scope": False}
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return {"status": "STOP_OFFLINE_TEST_AUTHORIZATION", "complete_scope": False}
    else:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
        )
        if auth["status"] != "PASS_LIVE_AUTHORIZATION":
            return {**auth, "complete_scope": False}
        if not getattr(document_source, "network_capable", False):
            return {"status": "STOP_LIVE_DOCUMENT_SOURCE_NOT_NETWORK_CAPABLE", "complete_scope": False}

    attempt_count = 0
    validated_download_count = 0
    aggregate_bytes = 0
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for item in cfg["targets"]:
        edition = int(item["edition"])
        attempt_count += 1
        try:
            _stop(
                attempt_count <= int(cfg["network"]["max_document_get_attempt_count"]),
                "TASK217F_GET_ATTEMPT_BUDGET",
            )
            data, meta = document_source.get(
                str(item["url"]),
                int(cfg["network"]["max_bytes_per_document"]),
            )
            _validate_download(item, data, meta, cfg=cfg)
            validated_download_count += 1
            aggregate_bytes += len(data)
            _stop(
                aggregate_bytes <= int(cfg["network"]["max_aggregate_document_bytes"]),
                "TASK217F_AGGREGATE_BYTES",
            )
            processed = process_document(
                {
                    "source_id": item["source_id"],
                    "edition": edition,
                    "publication_date": item["publication_date"],
                    "document_url": item["url"],
                },
                data,
                excerpt_max_chars=int(cfg["processing"]["candidate_excerpt_max_chars"]),
            )
            row = {
                "edition": edition,
                "publication_date": item["publication_date"],
                "source_id": item["source_id"],
                "source_url": item["url"],
                **processed["summary"],
                "screen": processed["screen"],
            }
            results.append(row)
            if processed["status"] != "PASS_DOCUMENT":
                failures.append(
                    {
                        "edition": edition,
                        "error_class": "PROCESSING_STATUS",
                        "stop_code": str(processed["summary"].get("processing_status")),
                    }
                )
        except Exception as exc:
            failures.append(
                {
                    "edition": edition,
                    "error_class": type(exc).__name__,
                    "stop_code": str(exc),
                }
            )
            results.append(
                {
                    "edition": edition,
                    "publication_date": item["publication_date"],
                    "source_id": item["source_id"],
                    "source_url": item["url"],
                    "processing_status": "STOP_EXCEPTION",
                    "error_class": type(exc).__name__,
                    "stop_code": str(exc),
                    "screen": {
                        "page_candidates": [],
                        "resolved_exact_school_infrastructure_events": [],
                        "generic_unassigned_school_infrastructure_events": [],
                        "counts": {
                            "page_candidate_count": 0,
                            "resolved_exact_school_infrastructure_count": 0,
                            "generic_unassigned_school_infrastructure_count": 0,
                        },
                    },
                }
            )

    exact_events = [
        event
        for row in results
        for event in row.get("screen", {}).get("resolved_exact_school_infrastructure_events", [])
    ]
    generic_events = [
        event
        for row in results
        for event in row.get("screen", {}).get("generic_unassigned_school_infrastructure_events", [])
    ]
    page_candidates = [
        page
        for row in results
        for page in row.get("screen", {}).get("page_candidates", [])
    ]
    complete = len(results) == 12 and not failures

    return {
        "schema": "TASK217F_RECOVERY_RESULT_V1",
        "status": "PASS_COMPLETE_12_DOCUMENT_RECOVERY" if complete else "PARTIAL_12_DOCUMENT_RECOVERY_NO_ABSENCE_INFERENCE",
        "complete_scope": complete,
        "target_document_count": 12,
        "document_get_attempt_count": attempt_count,
        "validated_download_count": validated_download_count,
        "aggregate_document_bytes": aggregate_bytes,
        "document_results": results,
        "failures": failures,
        "counts": {
            "failure_count": len(failures),
            "page_candidate_count": len(page_candidates),
            "resolved_exact_school_infrastructure_event_count": len(exact_events),
            "generic_unassigned_school_infrastructure_event_count": len(generic_events),
        },
        "resolved_exact_school_infrastructure_events": exact_events,
        "generic_unassigned_school_infrastructure_events": generic_events,
        "page_candidates": page_candidates,
        "specific_stop_codes_preserved": True,
        "rediscovery_performed": False,
        "raw_pdf_persisted": False,
        "raw_page_text_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "absence_inference_allowed": False,
        "canonization_required": True,
    }


def validate_offline_carrier(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(config_path)
    return {
        "schema": "TASK217F_OFFLINE_CARRIER_VALIDATION_V1",
        "status": "PASS",
        "target_count": len(cfg["targets"]),
        "max_gets": cfg["network"]["max_total_remote_get_count"],
        "max_bytes_per_document": cfg["network"]["max_bytes_per_document"],
        "budget_math_safe": (
            cfg["network"]["max_bytes_per_document"] * 12 + 12
            <= cfg["network"]["max_aggregate_document_bytes"]
        ),
        "live_authorized": cfg["authorization"]["live_authorized"],
        "network": False,
        "drive_write": False,
        "promotion": False,
    }
