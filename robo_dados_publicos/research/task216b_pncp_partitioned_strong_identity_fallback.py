from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import fetch_route
from robo_dados_publicos.research.task216_pncp_strong_identity_bridge import (
    DEFAULT_CONFIG as TASK216_DEFAULT_CONFIG,
    adjudicate_records,
    load_config as load_parent_config,
    load_jom_anchors,
    load_tce_index,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task216b_pncp_partitioned_strong_identity_fallback.v1.json"


class Task216BStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task216BStop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK216B_PNCP_PARTITIONED_STRONG_IDENTITY_FALLBACK_V1", "TASK216B_SCHEMA")
    _stop(obj.get("issue") == 676, "TASK216B_ISSUE")
    _stop(obj["authorization"]["scope"] == "PNCP_LIVE_READ_DISCOVERY_ONLY", "TASK216B_AUTH")
    _stop(obj["source"]["endpoint"] == "https://pncp.gov.br/api/consulta/v1/contratos", "TASK216B_ENDPOINT")
    _stop(obj["source"]["cnpjOrgao"] == "45132495000140", "TASK216B_CNPJ")
    _stop(obj["source"]["tamanhoPagina"] == 500, "TASK216B_PAGE_SIZE")
    _stop(obj["source"]["maxPaginasPerPartition"] == 5, "TASK216B_PAGE_CAP")
    _stop(obj["source"]["retryMax"] == 0 and obj["source"]["redirectsMax"] == 0, "TASK216B_RETRY_REDIRECT")
    _stop(obj["persistence"]["rawPayloadGit"] is False, "TASK216B_RAW_GIT")
    _stop(obj["persistence"]["rawPayloadDrive"] is False, "TASK216B_RAW_DRIVE")
    _stop(obj["persistence"]["rawPayloadWorkflowArtifact"] is False, "TASK216B_RAW_ARTIFACT")
    _stop(obj["persistence"]["sanitizedResultWorkflowArtifact"] is True, "TASK216B_SANITIZED")
    parts = obj["partitions"]
    _stop(len(parts) == 9, "TASK216B_PARTITION_COUNT")
    _stop(parts[0]["dataInicial"] == "20260101", "TASK216B_SCOPE_START")
    _stop(parts[-1]["dataFinal"] == "20260908", "TASK216B_SCOPE_END")
    last_end = None
    for part in parts:
        _stop(part["dataInicial"] <= part["dataFinal"], "TASK216B_PARTITION_ORDER")
        if last_end is not None:
            _stop(part["dataInicial"] > last_end, "TASK216B_PARTITION_OVERLAP")
        last_end = part["dataFinal"]
    return obj


def build_url(config: dict[str, Any], partition: dict[str, str], page: int) -> str:
    params = {
        "dataInicial": partition["dataInicial"],
        "dataFinal": partition["dataFinal"],
        "cnpjOrgao": config["source"]["cnpjOrgao"],
        "pagina": page,
        "tamanhoPagina": config["source"]["tamanhoPagina"],
    }
    return config["source"]["endpoint"] + "?" + urlencode(params)


def _scan_page(payload: dict[str, Any], requested_page: int, config: dict[str, Any]) -> dict[str, Any]:
    _stop(isinstance(payload, dict), "TASK216B_PAYLOAD_OBJECT")
    data = payload.get("data")
    _stop(isinstance(data, list), "TASK216B_DATA_LIST")
    total_records = payload.get("totalRegistros")
    total_pages = payload.get("totalPaginas")
    page_number = payload.get("numeroPagina")
    _stop(isinstance(total_records, int) and total_records >= 0, "TASK216B_TOTAL_RECORDS")
    _stop(isinstance(total_pages, int) and total_pages >= 0, "TASK216B_TOTAL_PAGES")
    _stop(page_number == requested_page, "TASK216B_PAGE_IDENTITY")
    _stop(total_pages <= config["source"]["maxPaginasPerPartition"], "TASK216B_PAGE_CAP")
    _stop(all(isinstance(row, dict) for row in data), "TASK216B_RECORD_OBJECT")
    return {
        "requested_page": requested_page,
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "record_count": len(data),
        "records": data,
    }


def execute(config: dict[str, Any]) -> dict[str, Any]:
    parent = load_parent_config(TASK216_DEFAULT_CONFIG)
    anchors = load_jom_anchors(parent)
    tce_index = load_tce_index(parent)
    out: dict[str, Any] = {
        "schema": "TASK216B_PNCP_PARTITIONED_STRONG_IDENTITY_FALLBACK_RESULT_V1",
        "overall_scope": {
            "cnpjOrgao": config["source"]["cnpjOrgao"],
            "dataInicial": config["partitions"][0]["dataInicial"],
            "dataFinal": config["partitions"][-1]["dataFinal"],
            "partition_count": len(config["partitions"]),
        },
        "partition_results": [],
        "requests": [],
        "raw_payload_persisted": False,
        "weak_identity_fields_used": False,
        "promotion_auto_decision": "FORBIDDEN_RUNTIME_ONLY_DISCOVERY",
    }
    all_records: list[dict[str, Any]] = []

    for partition in config["partitions"]:
        page = 1
        pages: list[dict[str, Any]] = []
        partition_requests: list[dict[str, Any]] = []
        while True:
            meta, payload = fetch_route(
                build_url(config, partition, page),
                int(config["source"]["timeoutSeconds"]),
                int(config["source"]["maxBytesPerPage"]),
            )
            meta = {"partition_id": partition["id"], "page": page, **meta}
            out["requests"].append(meta)
            partition_requests.append(meta)

            if meta.get("http_status") == 204:
                _stop(page == 1, "TASK216B_204_AFTER_PAGE1")
                pages = []
                break
            if payload is None:
                out["status"] = "STOP_PARTITION_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
                out["failed_partition"] = partition["id"]
                out["failed_page"] = page
                out["complete_all_partitions"] = False
                out["partition_results"].append({
                    "partition_id": partition["id"],
                    "dataInicial": partition["dataInicial"],
                    "dataFinal": partition["dataFinal"],
                    "status": "STOP_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE",
                    "requests": partition_requests,
                })
                return out

            scanned = _scan_page(payload, page, config)
            pages.append(scanned)
            if scanned["totalPaginas"] == 0:
                _stop(scanned["totalRegistros"] == 0 and page == 1, "TASK216B_ZERO_PAGE_DRIFT")
                break
            if page >= scanned["totalPaginas"]:
                break
            page += 1

        if not pages:
            total_pages = 0
            total_records = 0
            records: list[dict[str, Any]] = []
        else:
            total_pages = pages[0]["totalPaginas"]
            total_records = pages[0]["totalRegistros"]
            _stop(all(p["totalPaginas"] == total_pages for p in pages), "TASK216B_TOTAL_PAGES_DRIFT")
            _stop(all(p["totalRegistros"] == total_records for p in pages), "TASK216B_TOTAL_RECORDS_DRIFT")
            _stop(len(pages) == total_pages or total_pages == 0, "TASK216B_INCOMPLETE_PARTITION")
            _stop(sum(p["record_count"] for p in pages) == total_records, "TASK216B_RECORD_RECONCILIATION")
            records = [row for p in pages for row in p["records"]]

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
    out["identity"] = adjudicate_records(all_records, anchors, tce_index)
    out["status"] = (
        "EXHAUSTIVE_COMPLETE_STRONG_CHAINS_FOUND"
        if out["identity"]["counts"]["end_to_end_identity_chain_count"]
        else "EXHAUSTIVE_COMPLETE_NO_END_TO_END_STRONG_CHAIN"
    )
    return out
