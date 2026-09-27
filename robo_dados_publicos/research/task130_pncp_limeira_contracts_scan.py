from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.research.task129_pncp_limeira_contracts_scan import (
    load_task129_contract,
    scan_pncp_page,
)


class Task130Stop(RuntimeError):
    """Fail-closed TASK 130 validation error."""


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task130Stop(code)


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def validate_task130_contract(x: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    _r(x.get("schema") == "TASK130_PNCP_LIMEIRA_CONTRACTS_PAGES_3_5_SCAN_V1", "TASK130_SCHEMA")
    _r(x.get("mode") == "T1_SINGLE_USE_OFFICIAL_REGISTRY_PAGES_3_5_SCAN", "TASK130_MODE")
    root=Path(root)

    upstream=x.get("upstream") or {}
    _r(upstream.get("confirmed_rows_scanned")==1000,"TASK130_UPSTREAM_ROWS")
    _r(upstream.get("confirmed_pages")==[1,2],"TASK130_UPSTREAM_PAGES")
    _r(upstream.get("confirmed_candidate_count")==0,"TASK130_UPSTREAM_CANDIDATES")
    _r(upstream.get("total_registros")==2023 and upstream.get("total_paginas")==5,"TASK130_UPSTREAM_SNAPSHOT")
    for path_key,sha_key,code in (
        ("task129_evidence_path","task129_evidence_git_blob_sha","TASK130_TASK129_EVIDENCE_BLOB"),
        ("task129_module_path","task129_module_git_blob_sha","TASK130_TASK129_MODULE_BLOB"),
        ("task129_contract_path","task129_contract_git_blob_sha","TASK130_TASK129_CONTRACT_BLOB"),
    ):
        raw=(root/str(upstream.get(path_key) or "")).read_bytes()
        _r(_git_blob_sha(raw)==upstream.get(sha_key),code)

    evidence=json.loads((root/upstream["task129_evidence_path"]).read_text(encoding="utf-8"))
    coverage=evidence.get("combined_coverage") or {}
    _r(coverage.get("rows_confirmed_scanned")==1000,"TASK130_EVIDENCE_ROWS")
    _r(coverage.get("pages_confirmed_scanned")==[1,2],"TASK130_EVIDENCE_PAGES")
    _r(coverage.get("pages_remaining")==[3,4,5],"TASK130_EVIDENCE_REMAINING")
    _r(coverage.get("exhaustive_within_query_scope") is False,"TASK130_EVIDENCE_PARTIAL")
    _r((evidence.get("live_execution") or {}).get("page2",{}).get("candidate_count")==0,"TASK130_EVIDENCE_CANDIDATES")
    _r(evidence.get("result")=="STOP_TASK129_PAGE3_TIMEOUT_AFTER_PAGE2_SUCCESS_PARTIAL_NO_EXHAUSTIVE_CONCLUSION","TASK130_EVIDENCE_RESULT")

    s=x.get("source") or {}
    _r(s.get("registry")=="PNCP","TASK130_REGISTRY")
    _r(s.get("base_url")=="https://pncp.gov.br/api/consulta","TASK130_BASE_URL")
    _r(s.get("source_role")=="SECONDARY_AGGREGATOR","TASK130_ROLE")
    _r(s.get("official_registry_surface") is True,"TASK130_REGISTRY_SURFACE")
    _r(s.get("cnpj_orgao")=="45132495000140","TASK130_CNPJ")
    _r(s.get("data_inicial")=="20251128" and s.get("data_final")=="20260904","TASK130_DATES")
    _r(s.get("pages")==[3,4,5],"TASK130_PAGES")
    _r(s.get("tamanho_pagina")==500,"TASK130_PAGE_SIZE")
    _r(s.get("max_bytes_per_page")==20971520,"TASK130_BYTES")
    expected_urls=[
        f"https://pncp.gov.br/api/consulta/v1/contratos?dataInicial=20251128&dataFinal=20260904&cnpjOrgao=45132495000140&pagina={page}&tamanhoPagina=500"
        for page in [3,4,5]
    ]
    _r(s.get("exact_urls")==expected_urls,"TASK130_URLS")

    t=x.get("transport") or {}
    _r(t.get("method")=="GET","TASK130_METHOD")
    _r(t.get("get_requests_max")==3,"TASK130_GET")
    _r(t.get("redirects_max")==0,"TASK130_REDIRECT")
    _r(t.get("retry")==0,"TASK130_RETRY")
    _r(t.get("timeout_seconds")==60,"TASK130_TIMEOUT")
    _r(t.get("accept")=="application/json","TASK130_ACCEPT")
    _r(t.get("exact_urls_only") is True,"TASK130_EXACT")
    _r(t.get("stop_after_first_failure") is True,"TASK130_STOP")

    snap=x.get("snapshot_consistency") or {}
    _r(snap.get("required_total_registros")==2023,"TASK130_TOTAL")
    _r(snap.get("required_total_paginas")==5,"TASK130_TOTAL_PAGES")
    _r(snap.get("require_requested_page_number") is True,"TASK130_PAGE_NUMBER")
    _r(snap.get("remaining_rows_required")==1023,"TASK130_REMAINING_ROWS")
    _r(snap.get("full_rows_required")==2023,"TASK130_FULL_ROWS")

    m=x.get("matching") or {}
    _r(m.get("inherited_exactly_from_task129") is True,"TASK130_MATCH_INHERIT")
    _r(m.get("weak_terms_qualify_alone") is False,"TASK130_WEAK")
    _r(m.get("max_candidates_total")==100,"TASK130_CANDIDATE_LIMIT")

    sem=x.get("epistemic_semantics") or {}
    _r(sem.get("source_role")=="SECONDARY_AGGREGATOR","TASK130_SEM_ROLE")
    _r(sem.get("automatic_financial_identity") is False,"TASK130_FIN")
    _r(sem.get("automatic_transaction_identity") is False,"TASK130_TX")
    _r(sem.get("municipal_primary_verification_required") is True,"TASK130_PRIMARY")
    _r(sem.get("weak_join_forbidden") is True,"TASK130_WEAK_JOIN")

    p=x.get("persistence") or {}
    _r(p.get("raw_json_git") is False and p.get("raw_json_drive") is False,"TASK130_RAW")
    _r(p.get("sanitized_candidate_evidence_git") is True,"TASK130_SANITIZED")
    for key in ("bronze","silver","gold","rag","state_registry","queue","serving","publication"):
        _r(p.get(key) is False,"TASK130_PERSIST")
    _r(x.get("future_retry_authorized") is False,"TASK130_FUTURE_RETRY")
    _r(x.get("future_scope_widening_authorized") is False,"TASK130_FUTURE_SCOPE")

    # Revalidate the inherited TASK129 scanner contract offline.
    load_task129_contract(root/upstream["task129_contract_path"],root=root)
    return x


def combine_remaining_pages(
    page_results: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    _r(len(page_results)==3,"TASK130_RESULT_COUNT")
    _r([x.get("requested_page") for x in page_results]==[3,4,5],"TASK130_RESULT_ORDER")
    if any(x.get("status")!="PAGE_SCANNED" for x in page_results):
        return {
            "status":"STOP_INCOMPLETE_OR_SNAPSHOT_DRIFT_NO_EXHAUSTIVE_CONCLUSION",
            "coverage":{
                "confirmed_prior_rows":1000,
                "new_rows":sum(x.get("rows_on_page",0) for x in page_results if x.get("status")=="PAGE_SCANNED"),
                "exhaustive_within_query_scope":False,
            },
            "candidate_count":0,
            "candidates":[],
            "financial_identity_promoted":False,
            "transaction_identity_promoted":False,
            "municipal_primary_verification_required":True,
        }
    rows=sum(x["rows_on_page"] for x in page_results)
    _r(rows==contract["snapshot_consistency"]["remaining_rows_required"],"TASK130_REMAINING_ROW_COVERAGE")
    candidates=[c for x in page_results for c in x["candidates"]]
    _r(len(candidates)<=contract["matching"]["max_candidates_total"],"TASK130_COMBINED_CANDIDATE_LIMIT")
    full=contract["upstream"]["confirmed_rows_scanned"]+rows
    _r(full==contract["snapshot_consistency"]["full_rows_required"],"TASK130_FULL_ROW_COVERAGE")
    status="CANDIDATE_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE" if candidates else "NO_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE_ONLY"
    return {
        "status":status,
        "query_scope":{
            "cnpj_orgao":contract["source"]["cnpj_orgao"],
            "data_inicial":contract["source"]["data_inicial"],
            "data_final":contract["source"]["data_final"],
            "pages":[1,2,3,4,5],
            "tamanho_pagina":500,
        },
        "coverage":{
            "total_registros":2023,
            "total_paginas":5,
            "prior_rows":1000,
            "remaining_rows":rows,
            "rows_scanned_total":full,
            "pages_scanned":[1,2,3,4,5],
            "exhaustive_within_query_scope":True,
        },
        "candidate_count":len(candidates),
        "candidates":candidates,
        "prior_candidate_count":0,
        "financial_identity_promoted":False,
        "transaction_identity_promoted":False,
        "municipal_primary_verification_required":True,
    }


def load_task130_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task130Stop("TASK130_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task130Stop("TASK130_JSON") from exc
    _r(isinstance(x,dict),"TASK130_OBJECT")
    return validate_task130_contract(x,root=root)
