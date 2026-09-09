from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlencode

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import fetch_route
from robo_dados_publicos.research.task219c_pncp_exact_identity_bridge import (
    adjudicate_pncp_records,
    load_combined_anchors,
    load_config as load_parent_config,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219c2_pncp_halfmonth_exact_identity_fallback.v1.json"


class Task219C2Stop(RuntimeError):
    pass


class PncpSource(Protocol):
    def fetch(self, url: str, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
        ...


class LivePncpSource:
    def fetch(self, url: str, timeout: int, max_bytes: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
        return fetch_route(url, timeout, max_bytes)


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219C2Stop(code)


def _date(value: str) -> datetime:
    return datetime.strptime(value, "%Y%m%d")


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg.get("schema") == "TASK219C2_PNCP_HALFMONTH_EXACT_IDENTITY_FALLBACK_V1", "TASK219C2_SCHEMA")
    _stop(cfg.get("task") == "TASK_219C2" and cfg.get("issue") == 691, "TASK219C2_TASK")
    first = cfg["first_runtime"]
    _stop(first["run_id"] == 34364890448, "TASK219C2_PARENT_RUN")
    _stop(first["remote_get_count"] == 1 and first["bytes_received"] == 0, "TASK219C2_PARENT_EFFECT")
    _stop(first["scientific_effect"] == "NONE", "TASK219C2_PARENT_SCIENCE")
    _stop(first["authorization_reuse_allowed"] is False, "TASK219C2_AUTH_REUSE")

    source = cfg["source"]
    _stop(source["endpoint"] == "https://pncp.gov.br/api/consulta/v1/contratos", "TASK219C2_ENDPOINT")
    _stop(source["cnpjOrgao"] == "45132495000140", "TASK219C2_ORG")
    _stop(source["tamanhoPagina"] == 250, "TASK219C2_PAGE_SIZE")
    _stop(source["maxPaginasPerPartition"] == 3, "TASK219C2_PAGE_CAP")
    _stop(source["maxTotalRemoteGets"] == 54, "TASK219C2_GET_CAP")
    _stop(source["timeoutSeconds"] == 120, "TASK219C2_TIMEOUT")
    _stop(source["retryMax"] == 0 and source["redirectsMax"] == 0, "TASK219C2_RETRY")

    parts = cfg["partitions"]
    _stop(len(parts) == 18, "TASK219C2_PARTITION_COUNT")
    _stop(parts[0]["dataInicial"] == "20260101" and parts[-1]["dataFinal"] == "20260908", "TASK219C2_SCOPE")
    previous_end = None
    for part in parts:
        start = _date(part["dataInicial"])
        end = _date(part["dataFinal"])
        _stop(start <= end, "TASK219C2_PARTITION_ORDER")
        if previous_end is not None:
            _stop(start == previous_end + timedelta(days=1), "TASK219C2_PARTITION_GAP_OR_OVERLAP")
        previous_end = end

    persistence = cfg["persistence"]
    _stop(persistence["rawPayloadGit"] is False, "TASK219C2_RAW_GIT")
    _stop(persistence["rawPayloadDrive"] is False, "TASK219C2_RAW_DRIVE")
    _stop(persistence["rawPayloadWorkflowArtifact"] is False, "TASK219C2_RAW_ARTIFACT")
    _stop(persistence["sanitizedResultWorkflowArtifact"] is True, "TASK219C2_SANITIZED")
    _stop(cfg["promotion_policy"]["runtime_auto_promotion"] is False, "TASK219C2_PROMOTION")
    _stop(cfg["promotion_policy"]["end_to_end_chain_claim_allowed"] is False, "TASK219C2_CHAIN")
    return cfg


def validate_owner_authorization(
    authorization: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
    expected_implementation_sha: str,
) -> dict[str, Any]:
    _stop(authorization.get("schema") == "TASK219C2_OWNER_AUTHORIZATION_V1", "TASK219C2_AUTH_SCHEMA")
    _stop(authorization.get("task") == "TASK_219C2_LIVE_AUTHORIZATION", "TASK219C2_AUTH_TASK")
    _stop(authorization.get("implementation_sha") == expected_implementation_sha, "TASK219C2_AUTH_SHA")
    _stop(authorization.get("runtime_branch") == cfg["runtime"]["branch"], "TASK219C2_AUTH_BRANCH")
    _stop(authorization.get("source") == "PNCP", "TASK219C2_AUTH_SOURCE")
    _stop(authorization.get("operation") == "BOUNDED_2026_PNCP_HALFMONTH_EXACT_IDENTITY_DISCOVERY_303_KEYS", "TASK219C2_AUTH_OPERATION")
    _stop(authorization.get("attempt_count") == 1, "TASK219C2_AUTH_ATTEMPT")
    _stop(authorization.get("owner_authorized") is True, "TASK219C2_AUTH_OWNER")
    _stop(authorization.get("authorization_token_batch") == 10, "TASK219C2_AUTH_BATCH")
    _stop(authorization.get("authorization_token_consumed_for_this_operation") == 5, "TASK219C2_AUTH_TOKEN")
    _stop(authorization.get("authorization_tokens_remaining_after_this_operation") == 5, "TASK219C2_AUTH_REMAINING")
    _stop(authorization.get("max_total_remote_get_count") == 54, "TASK219C2_AUTH_GET_CAP")
    _stop(authorization.get("pncp_read_authorized") is True, "TASK219C2_AUTH_PNCP")
    for key in (
        "task216_authorization_reused",
        "task219a_authorization_reused",
        "task219c_authorization_reused",
        "task219c2_prior_authorization_reused",
        "tce_network_authorized",
        "drive_write_authorized",
        "serving_authorized",
        "publication_authorized",
        "promotion_authorized",
        "recurrence_authorized",
        "schedule_authorized",
    ):
        _stop(authorization.get(key) is False, "TASK219C2_AUTH_FORBIDDEN_" + key.upper())
    return dict(authorization)


def build_url(cfg: Mapping[str, Any], partition: Mapping[str, str], page: int) -> str:
    params = {
        "dataInicial": partition["dataInicial"],
        "dataFinal": partition["dataFinal"],
        "cnpjOrgao": cfg["source"]["cnpjOrgao"],
        "pagina": page,
        "tamanhoPagina": cfg["source"]["tamanhoPagina"],
    }
    return cfg["source"]["endpoint"] + "?" + urlencode(params)


def _scan_page(payload: Mapping[str, Any], requested_page: int, cfg: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    _stop(isinstance(data, list), "TASK219C2_DATA_LIST")
    total_records = payload.get("totalRegistros")
    total_pages = payload.get("totalPaginas")
    page_number = payload.get("numeroPagina")
    _stop(isinstance(total_records, int) and total_records >= 0, "TASK219C2_TOTAL_RECORDS")
    _stop(isinstance(total_pages, int) and total_pages >= 0, "TASK219C2_TOTAL_PAGES")
    _stop(page_number == requested_page, "TASK219C2_PAGE_IDENTITY")
    _stop(total_pages <= cfg["source"]["maxPaginasPerPartition"], "TASK219C2_PAGE_CAP_RUNTIME")
    _stop(all(isinstance(row, dict) for row in data), "TASK219C2_RECORD_OBJECT")
    return {
        "requested_page": requested_page,
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "record_count": len(data),
        "records": data,
    }


def execute(
    cfg: Mapping[str, Any],
    *,
    source: PncpSource,
    authorization: Mapping[str, Any],
    expected_implementation_sha: str,
) -> dict[str, Any]:
    validate_owner_authorization(
        authorization,
        cfg=cfg,
        expected_implementation_sha=expected_implementation_sha,
    )
    parent_cfg = load_parent_config(ROOT / cfg["inputs"]["parent_config"])
    anchors = load_combined_anchors(parent_cfg)
    _stop(len(anchors) == cfg["inputs"]["expected_anchor_rows"], "TASK219C2_ANCHOR_ROWS")
    _stop(len({(r["anchor_type"], r["anchor_value"]) for r in anchors}) == cfg["inputs"]["expected_unique_identities"], "TASK219C2_IDENTITIES")

    out: dict[str, Any] = {
        "schema": "TASK219C2_PNCP_HALFMONTH_EXACT_IDENTITY_FALLBACK_RESULT_V1",
        "scope": {
            "cnpjOrgao": cfg["source"]["cnpjOrgao"],
            "dataInicial": cfg["partitions"][0]["dataInicial"],
            "dataFinal": cfg["partitions"][-1]["dataFinal"],
            "partition_count": len(cfg["partitions"]),
        },
        "partition_results": [],
        "requests": [],
        "raw_payload_persisted": False,
        "weak_identity_fields_used": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "complete_all_partitions": False,
    }
    all_records: list[dict[str, Any]] = []

    for partition in cfg["partitions"]:
        page = 1
        pages: list[dict[str, Any]] = []
        while True:
            _stop(len(out["requests"]) < cfg["source"]["maxTotalRemoteGets"], "TASK219C2_TOTAL_GET_CAP")
            meta, payload = source.fetch(
                build_url(cfg, partition, page),
                int(cfg["source"]["timeoutSeconds"]),
                int(cfg["source"]["maxBytesPerPage"]),
            )
            meta = {"partition_id": partition["id"], "page": page, **meta}
            out["requests"].append(meta)
            if meta.get("http_status") == 204:
                _stop(page == 1, "TASK219C2_204_AFTER_PAGE1")
                break
            if payload is None:
                out["status"] = "STOP_PARTITION_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
                out["failed_partition"] = partition["id"]
                out["failed_page"] = page
                return out
            scanned = _scan_page(payload, page, cfg)
            pages.append(scanned)
            if scanned["totalPaginas"] == 0:
                _stop(scanned["totalRegistros"] == 0 and page == 1, "TASK219C2_ZERO_PAGE_DRIFT")
                break
            if page >= scanned["totalPaginas"]:
                break
            page += 1

        if pages:
            total_pages = pages[0]["totalPaginas"]
            total_records = pages[0]["totalRegistros"]
            _stop(all(p["totalPaginas"] == total_pages for p in pages), "TASK219C2_TOTAL_PAGES_DRIFT")
            _stop(all(p["totalRegistros"] == total_records for p in pages), "TASK219C2_TOTAL_RECORDS_DRIFT")
            _stop(len(pages) == total_pages, "TASK219C2_INCOMPLETE_PARTITION")
            _stop(sum(p["record_count"] for p in pages) == total_records, "TASK219C2_RECORD_RECONCILIATION")
            records = [r for p in pages for r in p["records"]]
        else:
            total_pages = 0
            total_records = 0
            records = []

        all_records.extend(records)
        out["partition_results"].append({
            "partition_id": partition["id"],
            "dataInicial": partition["dataInicial"],
            "dataFinal": partition["dataFinal"],
            "status": "EXHAUSTIVE_COMPLETE",
            "totalRegistros": total_records,
            "totalPaginas": total_pages,
            "pages_scanned": list(range(1, total_pages + 1)),
        })

    out["complete_all_partitions"] = True
    out["total_records_across_partitions"] = len(all_records)
    out["identity"] = adjudicate_pncp_records(all_records, anchors)
    out["status"] = (
        "EXHAUSTIVE_COMPLETE_PNCP_EXACT_IDENTITIES_FOUND"
        if out["identity"]["counts"]["matched_identity_count"]
        else "EXHAUSTIVE_COMPLETE_NO_PNCP_EXACT_IDENTITY"
    )
    return out


__all__ = [
    "Task219C2Stop",
    "LivePncpSource",
    "load_config",
    "validate_owner_authorization",
    "build_url",
    "execute",
]
