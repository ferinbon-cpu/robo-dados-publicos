from __future__ import annotations
import json
from pathlib import Path
from typing import Any
class Task127Stop(RuntimeError): pass
def _r(c:bool,code:str)->None:
    if not c: raise Task127Stop(code)
def validate_task127_contract(x:dict[str,Any])->dict[str,Any]:
    _r(x.get("schema")=="TASK127_JOM_EITI_ACCOUNTING_FIELD_SCAN_V1","TASK127_SCHEMA")
    _r(x.get("mode")=="T1_SINGLE_USE_EXACT_PDF_ACCOUNTING_SCAN","TASK127_MODE")
    s=x.get("source") or {}
    _r(s.get("url")=="https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_27112025163143.pdf","TASK127_URL")
    _r(s.get("source_role")=="MUNICIPAL_PRIMARY_NORMATIVE_PROCUREMENT","TASK127_ROLE")
    _r(s.get("max_bytes")==20971520,"TASK127_MAX_BYTES")
    _r(set(s.get("expected_markers") or [])=={"EDITAL DE CREDENCIAMENTO","ESCOLA EM TEMPO INTEGRAL 2026","PROGRAMA DE EDUCACAO INTEGRAL"},"TASK127_MARKERS")
    t=x.get("transport") or {}
    _r(t.get("get_requests_max")==1,"TASK127_GET")
    _r(t.get("redirects_max")==0,"TASK127_REDIRECT")
    _r(t.get("retry")==0,"TASK127_RETRY")
    _r(t.get("exact_url_only") is True,"TASK127_EXACT")
    p=x.get("processing") or {}
    _r(p.get("pdf_magic_required") is True and p.get("sha256") is True and p.get("pypdf_only") is True,"TASK127_PROCESS")
    _r(p.get("ocr") is False,"TASK127_OCR")
    _r(set(p.get("normalized_terms") or [])=={"DOTACAO","FICHA","PROGRAMA","ACAO","SUBACAO","UNIDADE ORCAMENTARIA","FONTE","DESTINACAO","PROCESSO ADMINISTRATIVO","EMPENHO"},"TASK127_TERMS")
    _r(p.get("max_excerpt_chars_per_hit")==400 and p.get("max_hits_per_term")==20,"TASK127_LIMITS")
    sem=x.get("semantics") or {}
    _r(sem.get("candidate_bridge_requires")==["EXPLICIT_POLICY_MARKER","STABLE_ACCOUNTING_OR_BUDGET_IDENTIFIER"],"TASK127_BRIDGE")
    _r(sem.get("candidate_status")=="CANDIDATE","TASK127_STATUS")
    _r(sem.get("execution_event_still_required_for_transaction_identity") is True,"TASK127_TX_EVENT")
    for k in ("r30_hour_is_execution_event","monthly_payment_wording_is_execution_event","contract_template_is_transaction_identity","pme_link_is_accounting_identity","program_2001_similarity_is_identity","amount_equality_is_identity","automatic_promotion"):
        _r(sem.get(k) is False,f"TASK127_{k.upper()}")
    ps=x.get("persistence") or {}
    _r(ps and all(v is False for v in ps.values()),"TASK127_PERSIST")
    _r(x.get("future_retry_authorized") is False,"TASK127_FUTURE_RETRY")
    return x
def load_task127_contract(path:str|Path)->dict[str,Any]:
    try:x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as e: raise Task127Stop("TASK127_MISSING") from e
    except json.JSONDecodeError as e: raise Task127Stop("TASK127_JSON") from e
    _r(isinstance(x,dict),"TASK127_OBJECT"); return validate_task127_contract(x)
