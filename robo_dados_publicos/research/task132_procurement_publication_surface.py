from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class Task132Stop(RuntimeError):
    pass

def _r(c:bool,code:str)->None:
    if not c:
        raise Task132Stop(code)

def validate_task132_contract(x:dict[str,Any])->dict[str,Any]:
    _r(x.get("schema")=="TASK132_PROCUREMENT_PUBLICATION_SURFACE_SELECTION_V1","TASK132_SCHEMA")
    _r(x.get("mode")=="T0_OFFLINE_PUBLIC_DOCUMENTATION_SELECTION_ONLY","TASK132_MODE")
    t=x.get("target") or {}
    _r(t.get("cnpj_orgao")=="45132495000140","TASK132_CNPJ")
    _r(t.get("procurement_mode")=="CREDENCIAMENTO","TASK132_MODE_NAME")
    _r(t.get("procurement_mode_code")==12,"TASK132_MODE_CODE")
    s=x.get("selected_surface") or {}
    _r(s.get("name")=="PNCP_PUBLIC_CONTRATACOES_BY_PUBLICATION","TASK132_SURFACE")
    _r(s.get("registry")=="PNCP","TASK132_REGISTRY")
    _r(s.get("source_role")=="SECONDARY_AGGREGATOR","TASK132_ROLE")
    _r(s.get("endpoint_template")=="https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao","TASK132_ENDPOINT")
    _r(s.get("method")=="GET","TASK132_METHOD")
    _r(len(s.get("official_documentation_basis") or [])==3,"TASK132_DOC_BASIS")

    p=x.get("initial_live_probe") or {}
    _r(p.get("authorized_now") is False,"TASK132_LIVE_NOT_AUTHORIZED")
    _r(p.get("data_inicial")=="20251128" and p.get("data_final")=="20260904","TASK132_DATES")
    _r(p.get("codigo_modalidade_contratacao")==12,"TASK132_PROBE_MODE")
    _r(p.get("cnpj")=="45132495000140","TASK132_PROBE_CNPJ")
    _r(p.get("pagina")==1 and p.get("tamanho_pagina")==500,"TASK132_PROBE_PAGE")
    _r(p.get("get_requests_max")==1,"TASK132_PROBE_GET")
    _r(p.get("redirects_max")==0 and p.get("retry")==0,"TASK132_PROBE_TRANSPORT")
    _r(p.get("timeout_seconds")==60,"TASK132_TIMEOUT")
    _r(p.get("exact_url")=="https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20251128&dataFinal=20260904&codigoModalidadeContratacao=12&cnpj=45132495000140&pagina=1&tamanhoPagina=500","TASK132_EXACT_URL")

    m=x.get("candidate_matching") or {}
    _r(len(m.get("strong_markers") or [])==5,"TASK132_STRONG_COUNT")
    _r(m.get("strong_policy_marker_required") is True,"TASK132_STRONG_REQUIRED")
    _r(m.get("weak_context_alone_qualifies") is False,"TASK132_WEAK_GUARD")
    _r(m.get("fields_to_search")==["objetoCompra","informacaoComplementar"],"TASK132_FIELDS")

    f=x.get("followup_if_candidate") or {}
    _r(f.get("each_followup_requires_separate_gate") is True,"TASK132_FOLLOWUP_GATE")
    _r("/compras/{ano}/{sequencial}" in f.get("exact_current_detail_endpoint",""),"TASK132_DETAIL_ENDPOINT")
    _r(f.get("items_endpoint","").endswith("/itens"),"TASK132_ITEMS_ENDPOINT")
    _r(f.get("history_endpoint","").endswith("/historico"),"TASK132_HISTORY_ENDPOINT")
    _r(f.get("budget_sources_endpoint","").endswith("/fonte-orcamentaria"),"TASK132_BUDGET_ENDPOINT")
    _r("/contratos/contratacao/" in f.get("contracts_endpoint",""),"TASK132_CONTRACTS_ENDPOINT")

    sem=x.get("epistemic_semantics") or {}
    _r(sem.get("source_role")=="SECONDARY_AGGREGATOR","TASK132_SEM_ROLE")
    _r(sem.get("procurement_identifier_candidate_max_status")=="CORROBORATED","TASK132_STATUS_CAP")
    _r(sem.get("primary_municipal_verification_required") is True,"TASK132_PRIMARY")
    for key in ("automatic_financial_identity","automatic_transaction_identity","automatic_supplier_linkage"):
        _r(sem.get(key) is False,f"TASK132_{key.upper()}")
    _r(sem.get("weak_join_forbidden") is True,"TASK132_WEAK_JOIN")

    rejected=x.get("rejected_surfaces") or []
    _r(len(rejected)==3,"TASK132_REJECTED_COUNT")
    effects=x.get("remote_effects") or {}
    _r(effects and all(v is False for v in effects.values()),"TASK132_REMOTE_EFFECT")
    return x

def load_task132_contract(path:str|Path)->dict[str,Any]:
    try:
        x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task132Stop("TASK132_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task132Stop("TASK132_JSON") from exc
    _r(isinstance(x,dict),"TASK132_OBJECT")
    return validate_task132_contract(x)
