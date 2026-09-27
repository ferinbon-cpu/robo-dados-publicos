from __future__ import annotations

from copy import deepcopy
from hashlib import sha1
import json
from pathlib import Path
from typing import Any

from robo_dados_publicos.research.task128_pncp_limeira_contracts_scan import normalize_text


class Task129Stop(RuntimeError):
    """Fail-closed TASK 129 contract or payload validation error."""


def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task129Stop(code)


def _git_blob_sha(raw: bytes) -> str:
    return sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def validate_task129_contract(x: dict[str, Any], *, root: str | Path) -> dict[str, Any]:
    _r(x.get("schema") == "TASK129_PNCP_LIMEIRA_CONTRACTS_PAGES_2_5_SCAN_V1", "TASK129_SCHEMA")
    _r(x.get("mode") == "T1_SINGLE_USE_OFFICIAL_REGISTRY_PAGES_2_5_SCAN", "TASK129_MODE")

    upstream = x.get("upstream") or {}
    _r(upstream.get("total_registros") == 2023, "TASK129_UPSTREAM_TOTAL")
    _r(upstream.get("total_paginas") == 5, "TASK129_UPSTREAM_PAGES")
    _r(upstream.get("page1_candidate_count") == 0, "TASK129_UPSTREAM_PAGE1_CANDIDATES")
    root = Path(root)
    for path_key, sha_key, code in (
        ("task128_evidence_path","task128_evidence_git_blob_sha","TASK129_TASK128_EVIDENCE_BLOB"),
        ("task128_module_path","task128_module_git_blob_sha","TASK129_TASK128_MODULE_BLOB"),
    ):
        raw=(root / str(upstream.get(path_key) or "")).read_bytes()
        _r(_git_blob_sha(raw)==upstream.get(sha_key),code)
    task128=json.loads((root / upstream["task128_evidence_path"]).read_text(encoding="utf-8"))
    cov=task128.get("coverage") or {}
    _r(cov.get("total_registros")==2023 and cov.get("total_paginas")==5,"TASK129_TASK128_SNAPSHOT")
    _r(task128.get("candidate_count")==0,"TASK129_TASK128_CANDIDATE_COUNT")
    _r(task128.get("status")=="PARTIAL_PAGE1_REQUIRES_FRESH_PAGING_GATE","TASK129_TASK128_STATUS")

    s=x.get("source") or {}
    _r(s.get("registry")=="PNCP","TASK129_REGISTRY")
    _r(s.get("base_url")=="https://pncp.gov.br/api/consulta","TASK129_BASE_URL")
    _r(s.get("source_role")=="SECONDARY_AGGREGATOR","TASK129_ROLE")
    _r(s.get("official_registry_surface") is True,"TASK129_REGISTRY_SURFACE")
    _r(s.get("cnpj_orgao")=="45132495000140","TASK129_CNPJ")
    _r(s.get("data_inicial")=="20251128" and s.get("data_final")=="20260904","TASK129_DATES")
    _r(s.get("pages")==[2,3,4,5],"TASK129_PAGES")
    _r(s.get("tamanho_pagina")==500,"TASK129_PAGE_SIZE")
    _r(s.get("max_bytes_per_page")==20971520,"TASK129_MAX_BYTES")
    expected_urls=[
        f"https://pncp.gov.br/api/consulta/v1/contratos?dataInicial=20251128&dataFinal=20260904&cnpjOrgao=45132495000140&pagina={page}&tamanhoPagina=500"
        for page in [2,3,4,5]
    ]
    _r(s.get("exact_urls")==expected_urls,"TASK129_URLS")

    t=x.get("transport") or {}
    _r(t.get("method")=="GET","TASK129_METHOD")
    _r(t.get("get_requests_max")==4,"TASK129_GET_BUDGET")
    _r(t.get("redirects_max")==0,"TASK129_REDIRECT")
    _r(t.get("retry")==0,"TASK129_RETRY")
    _r(t.get("timeout_seconds")==30,"TASK129_TIMEOUT")
    _r(t.get("accept")=="application/json","TASK129_ACCEPT")
    _r(t.get("exact_urls_only") is True,"TASK129_EXACT_URLS")
    _r(t.get("stop_after_first_failure") is True,"TASK129_STOP_FAILURE")

    snap=x.get("snapshot_consistency") or {}
    _r(snap.get("required_total_registros")==2023,"TASK129_SNAPSHOT_TOTAL")
    _r(snap.get("required_total_paginas")==5,"TASK129_SNAPSHOT_PAGES")
    _r(snap.get("require_requested_page_number") is True,"TASK129_SNAPSHOT_PAGE_NUMBER")
    _r(snap.get("metadata_drift_status")=="STOP_SNAPSHOT_METADATA_DRIFT_NO_EXHAUSTIVE_CONCLUSION","TASK129_DRIFT_STATUS")

    m=x.get("matching") or {}
    _r(tuple(m.get("normalized_strong_policy_markers") or ())==(
        "PROGRAMA DE EDUCACAO INTEGRAL",
        "PROGRAMA ESCOLA EM TEMPO INTEGRAL",
        "ESCOLA EM TEMPO INTEGRAL",
        "EDUCACAO EM TEMPO INTEGRAL",
        "EDUCACAO INTEGRAL",
        "FOMENTO ETI",
    ),"TASK129_STRONG")
    _r(tuple(m.get("weak_support_terms") or ())==("OFICINA","OFICINEIRO","EXTRACURRICULAR","TEMPO INTEGRAL"),"TASK129_WEAK")
    _r(m.get("weak_terms_qualify_alone") is False,"TASK129_WEAK_GUARD")
    _r(tuple(m.get("fields_to_search") or ())==("objetoContrato","informacaoComplementar"),"TASK129_FIELDS")
    _r(m.get("max_candidates_total")==100,"TASK129_CANDIDATE_LIMIT")

    sem=x.get("epistemic_semantics") or {}
    _r(sem.get("source_role")=="SECONDARY_AGGREGATOR","TASK129_SEM_ROLE")
    for key in ("accounting_execution_max_status","administrative_event_max_status","policy_linkage_max_status"):
        _r(sem.get(key)=="CORROBORATED","TASK129_STATUS_CAP")
    _r(sem.get("automatic_financial_identity") is False,"TASK129_FIN_PROMOTION")
    _r(sem.get("automatic_transaction_identity") is False,"TASK129_TX_PROMOTION")
    _r(sem.get("municipal_primary_verification_required") is True,"TASK129_PRIMARY_VERIFY")
    _r(sem.get("weak_join_forbidden") is True,"TASK129_WEAK_JOIN")

    p=x.get("persistence") or {}
    _r(p.get("raw_json_git") is False and p.get("raw_json_drive") is False,"TASK129_RAW_PERSIST")
    _r(p.get("sanitized_candidate_evidence_git") is True,"TASK129_SANITIZED")
    for key in ("bronze","silver","gold","rag","state_registry","queue","serving","publication"):
        _r(p.get(key) is False,"TASK129_PERSIST")
    _r(x.get("future_retry_authorized") is False,"TASK129_FUTURE_RETRY")
    _r(x.get("future_scope_widening_authorized") is False,"TASK129_FUTURE_SCOPE")
    return x


def scan_pncp_page(
    payload: dict[str, Any],
    contract: dict[str, Any],
    *,
    requested_page: int,
) -> dict[str, Any]:
    _r(requested_page in [2,3,4,5],"TASK129_REQUESTED_PAGE")
    _r(isinstance(payload,dict),"TASK129_PAYLOAD_OBJECT")
    data=payload.get("data")
    _r(isinstance(data,list),"TASK129_PAYLOAD_DATA")
    def int_field(name: str, code: str) -> int:
        value=payload.get(name)
        _r(isinstance(value,int) and not isinstance(value,bool) and value>=0,code)
        return value
    total=int_field("totalRegistros","TASK129_TOTAL_REGISTROS")
    pages=int_field("totalPaginas","TASK129_TOTAL_PAGINAS")
    current=int_field("numeroPagina","TASK129_NUMERO_PAGINA")
    if total!=contract["snapshot_consistency"]["required_total_registros"] or pages!=contract["snapshot_consistency"]["required_total_paginas"]:
        return {
            "status":"STOP_SNAPSHOT_METADATA_DRIFT_NO_EXHAUSTIVE_CONCLUSION",
            "requested_page":requested_page,
            "observed_total_registros":total,
            "observed_total_paginas":pages,
            "observed_numero_pagina":current,
            "rows_on_page":len(data),
            "candidates":[],
            "candidate_count":0,
        }
    _r(current==requested_page,"TASK129_PAGE_MISMATCH")
    _r(total>=len(data),"TASK129_TOTAL_LT_PAGE")
    _r(len(data)>0,"TASK129_EXPECTED_NONEMPTY_PAGE")

    strong=contract["matching"]["normalized_strong_policy_markers"]
    weak=contract["matching"]["weak_support_terms"]
    fields=contract["matching"]["fields_to_search"]
    candidates=[]
    for idx,row in enumerate(data):
        _r(isinstance(row,dict),"TASK129_ROW_OBJECT")
        searchable=" ".join(normalize_text(row.get(field)) for field in fields)
        strong_hits=[term for term in strong if term in searchable]
        weak_hits=[term for term in weak if term in searchable]
        if not strong_hits:
            continue
        candidates.append({
            "page":requested_page,
            "row_index":idx,
            "strong_policy_markers":strong_hits,
            "weak_support_terms":weak_hits,
            "source_role":"SECONDARY_AGGREGATOR",
            "status":"CANDIDATE_REQUIRES_MUNICIPAL_PRIMARY_VERIFICATION",
            "automatic_financial_identity":False,
            "automatic_transaction_identity":False,
            "fields":{
                field:deepcopy(row.get(field))
                for field in contract["candidate_fields"]
                if row.get(field) is not None
            },
        })
        _r(len(candidates)<=contract["matching"]["max_candidates_total"],"TASK129_CANDIDATE_LIMIT")
    return {
        "status":"PAGE_SCANNED",
        "requested_page":requested_page,
        "observed_total_registros":total,
        "observed_total_paginas":pages,
        "observed_numero_pagina":current,
        "rows_on_page":len(data),
        "candidates":candidates,
        "candidate_count":len(candidates),
    }


def combine_task128_and_task129(
    page_results: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    _r(len(page_results)==4,"TASK129_RESULT_PAGE_COUNT")
    _r([x.get("requested_page") for x in page_results]==[2,3,4,5],"TASK129_RESULT_PAGE_ORDER")
    if any(x.get("status")!="PAGE_SCANNED" for x in page_results):
        return {
            "status":"STOP_SNAPSHOT_METADATA_DRIFT_NO_EXHAUSTIVE_CONCLUSION",
            "exhaustive_within_query_scope":False,
            "candidate_count":0,
            "candidates":[],
            "pages_scanned":[x.get("requested_page") for x in page_results],
            "page1_candidate_count":0,
            "financial_identity_promoted":False,
            "transaction_identity_promoted":False,
            "municipal_primary_verification_required":True,
        }
    candidates=[c for page in page_results for c in page["candidates"]]
    _r(len(candidates)<=contract["matching"]["max_candidates_total"],"TASK129_COMBINED_CANDIDATE_LIMIT")
    rows_remaining=sum(x["rows_on_page"] for x in page_results)
    _r(rows_remaining + 500 == 2023,"TASK129_ROW_COVERAGE")
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
            "page1_rows":500,
            "pages_2_5_rows":rows_remaining,
            "rows_scanned_total":2023,
            "exhaustive_within_query_scope":True,
        },
        "candidate_count":len(candidates),
        "candidates":candidates,
        "page1_candidate_count":0,
        "weak_terms_never_qualify_alone":True,
        "financial_identity_promoted":False,
        "transaction_identity_promoted":False,
        "municipal_primary_verification_required":True,
    }


def load_task129_contract(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task129Stop("TASK129_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task129Stop("TASK129_JSON") from exc
    _r(isinstance(x,dict),"TASK129_OBJECT")
    return validate_task129_contract(x,root=root)
