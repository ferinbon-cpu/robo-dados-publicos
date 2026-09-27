from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import fetch_route


class Task168BStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task168BStop(code)


def load_config(path: str | Path) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK168B_PNCP_CONSULTA_CONTRACTS_FALLBACK_V1", "TASK168B_CONFIG_SCHEMA")
    _stop(obj["authorization"]["scope"] == "PNCP_LIVE_READ_DISCOVERY_ONLY", "TASK168B_AUTH_SCOPE")
    _stop(obj["authorization"]["new_per_page_authorization_required"] is False, "TASK168B_AUTH_REUSE")
    _stop(obj["source"]["endpoint"] == "https://pncp.gov.br/api/consulta/v1/contratos", "TASK168B_ENDPOINT")
    _stop(obj["source"]["cnpjOrgao"] == "45132495000140", "TASK168B_CNPJ")
    _stop(obj["source"]["tamanhoPagina"] == 500, "TASK168B_PAGE_SIZE")
    _stop(obj["source"]["maxPaginas"] == 20, "TASK168B_PAGE_CAP")
    _stop(obj["source"]["retryMax"] == 0, "TASK168B_RETRY")
    _stop(obj["source"]["redirectsMax"] == 0, "TASK168B_REDIRECT")
    _stop(obj["persistence"]["rawPayloadGit"] is False, "TASK168B_RAW_GIT")
    _stop(obj["persistence"]["rawPayloadDrive"] is False, "TASK168B_RAW_DRIVE")
    _stop(obj["persistence"]["rawPayloadWorkflowArtifact"] is False, "TASK168B_RAW_ARTIFACT")
    return obj


def build_url(config: dict[str, Any], page: int) -> str:
    params = {
        "dataInicial": config["source"]["dataInicial"],
        "dataFinal": config["source"]["dataFinal"],
        "cnpjOrgao": config["source"]["cnpjOrgao"],
        "pagina": page,
        "tamanhoPagina": config["source"]["tamanhoPagina"],
    }
    return config["source"]["endpoint"] + "?" + urlencode(params)


def _primitive(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


CONTRACT_ALLOW = (
    "numeroControlePNCP",
    "numeroControlePNCPCompra",
    "numeroContratoEmpenho",
    "anoContrato",
    "sequencialContrato",
    "processo",
    "objetoContrato",
    "informacaoComplementar",
    "receita",
    "valorInicial",
    "valorGlobal",
    "valorAcumulado",
    "dataAssinatura",
    "dataVigenciaInicio",
    "dataVigenciaFim",
    "dataPublicacaoPncp",
    "dataInclusao",
    "dataAtualizacao",
)


def sanitize_match(record: dict[str, Any], expected_cnpj: str) -> dict[str, Any]:
    org = record.get("orgaoEntidade") or {}
    if isinstance(org, dict) and org.get("cnpj") not in (None, ""):
        _stop(str(org.get("cnpj")) == expected_cnpj, "TASK168B_ENTITY_IDENTITY_MISMATCH")

    selected = {
        key: record.get(key)
        for key in CONTRACT_ALLOW
        if key in record and _primitive(record.get(key))
    }
    if isinstance(org, dict):
        selected["orgaoEntidade"] = {
            key: org.get(key)
            for key in ("cnpj", "razaoSocial", "poderId", "esferaId")
            if key in org and _primitive(org.get(key))
        }
    return selected


def scan_page(
    payload: dict[str, Any],
    config: dict[str, Any],
    requested_page: int,
) -> dict[str, Any]:
    _stop(isinstance(payload, dict), "TASK168B_PAYLOAD_NOT_OBJECT")
    data = payload.get("data")
    _stop(isinstance(data, list), "TASK168B_DATA_NOT_LIST")

    total_records = payload.get("totalRegistros")
    total_pages = payload.get("totalPaginas")
    page_number = payload.get("numeroPagina")
    remaining = payload.get("paginasRestantes")

    _stop(isinstance(total_records, int) and total_records >= 0, "TASK168B_TOTAL_RECORDS")
    _stop(isinstance(total_pages, int) and total_pages >= 0, "TASK168B_TOTAL_PAGES")
    _stop(page_number == requested_page, "TASK168B_PAGE_IDENTITY")
    _stop(total_pages <= config["source"]["maxPaginas"], "TASK168B_PAGE_CAP")

    target_map = {
        target["numeroControlePNCPCompra"]: target["id"]
        for target in config["targets"]
    }
    matches = []
    for record in data:
        _stop(isinstance(record, dict), "TASK168B_RECORD_NOT_OBJECT")
        linked = record.get("numeroControlePNCPCompra")
        if linked in target_map:
            matches.append({
                "target_id": target_map[linked],
                "record": sanitize_match(record, config["source"]["cnpjOrgao"]),
            })

    return {
        "requested_page": requested_page,
        "reported_page": page_number,
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "paginasRestantes": remaining,
        "record_count": len(data),
        "matches": matches,
    }


def combine_pages(pages: list[dict[str, Any]]) -> dict[str, Any]:
    _stop(bool(pages), "TASK168B_NO_PAGES")
    total_pages = pages[0]["totalPaginas"]
    total_records = pages[0]["totalRegistros"]
    _stop(all(p["totalPaginas"] == total_pages for p in pages), "TASK168B_TOTAL_PAGES_DRIFT")
    _stop(all(p["totalRegistros"] == total_records for p in pages), "TASK168B_TOTAL_RECORDS_DRIFT")
    _stop(len(pages) == total_pages, "TASK168B_INCOMPLETE_PAGINATION")
    _stop(
        [p["requested_page"] for p in pages] == list(range(1, total_pages + 1)),
        "TASK168B_PAGE_SEQUENCE",
    )
    _stop(sum(p["record_count"] for p in pages) == total_records, "TASK168B_RECORD_COUNT_MISMATCH")

    matches = [m for p in pages for m in p["matches"]]
    return {
        "status": "EXHAUSTIVE_COMPLETE",
        "totalRegistros": total_records,
        "totalPaginas": total_pages,
        "pages_scanned": list(range(1, total_pages + 1)),
        "target_matches": matches,
        "target_match_count": len(matches),
        "exhaustive_within_exact_scope": True,
    }


def execute(config: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": "TASK168B_PNCP_CONSULTA_CONTRACTS_FALLBACK_RESULT_V1",
        "scope": {
            "endpoint": config["source"]["endpoint"],
            "cnpjOrgao": config["source"]["cnpjOrgao"],
            "dataInicial": config["source"]["dataInicial"],
            "dataFinal": config["source"]["dataFinal"],
            "tamanhoPagina": config["source"]["tamanhoPagina"],
        },
        "targets": config["targets"],
        "requests": [],
        "raw_payload_persisted": False,
        "pncp_no_match_created": False,
        "payment_inference_from_pncp": "FORBIDDEN",
        "financial_identity_auto_promotion": "FORBIDDEN",
        "transaction_identity_auto_promotion": "FORBIDDEN",
    }

    page = 1
    pages: list[dict[str, Any]] = []
    while True:
        url = build_url(config, page)
        meta, payload = fetch_route(
            url,
            int(config["source"]["timeoutSeconds"]),
            int(config["source"]["maxBytesPerPage"]),
        )
        out["requests"].append(meta)

        if meta.get("http_status") == 204:
            _stop(page == 1, "TASK168B_204_AFTER_PAGINATION_STARTED")
            out["status"] = "EXHAUSTIVE_COMPLETE_EMPTY_204"
            out["pagination"] = {
                "totalRegistros": 0,
                "totalPaginas": 0,
                "pages_scanned": [],
                "target_matches": [],
                "target_match_count": 0,
                "exhaustive_within_exact_scope": True,
            }
            out["scoped_conclusion"] = "BOUNDED_NO_LINKED_CONTRACT_MATCH_IN_EXACT_DATE_CNPJ_SCOPE"
            return out

        if payload is None:
            out["status"] = "STOP_SOURCE_TRANSPORT_OR_HTTP_OR_JSON_UNAVAILABLE"
            out["failed_page"] = page
            out["complete_pagination"] = False
            return out

        scanned = scan_page(payload, config, page)
        pages.append(scanned)
        total_pages = scanned["totalPaginas"]

        if total_pages == 0:
            _stop(scanned["totalRegistros"] == 0 and page == 1, "TASK168B_ZERO_PAGE_DRIFT")
            out["status"] = "EXHAUSTIVE_COMPLETE_EMPTY_200"
            out["pagination"] = {
                "totalRegistros": 0,
                "totalPaginas": 0,
                "pages_scanned": [],
                "target_matches": [],
                "target_match_count": 0,
                "exhaustive_within_exact_scope": True,
            }
            out["scoped_conclusion"] = "BOUNDED_NO_LINKED_CONTRACT_MATCH_IN_EXACT_DATE_CNPJ_SCOPE"
            return out

        if page >= total_pages:
            break
        page += 1

    combined = combine_pages(pages)
    out["pagination"] = combined
    out["complete_pagination"] = True
    if combined["target_match_count"] == 0:
        out["status"] = "EXHAUSTIVE_COMPLETE_NO_TARGET_MATCH"
        out["scoped_conclusion"] = "BOUNDED_NO_LINKED_CONTRACT_MATCH_IN_EXACT_DATE_CNPJ_SCOPE"
    else:
        out["status"] = "EXHAUSTIVE_COMPLETE_TARGET_MATCHES_FOUND"
        out["scoped_conclusion"] = "LINKED_CONTRACT_CANDIDATES_FOUND_REQUIRING_SEMANTIC_AND_ACCOUNTING_ADJUDICATION"
    return out
