from __future__ import annotations
from hashlib import sha1
import json
from pathlib import Path
from typing import Any

class Task131Stop(RuntimeError):
    pass

def _r(c:bool,code:str)->None:
    if not c:
        raise Task131Stop(code)

def _git_blob_sha(raw:bytes)->str:
    return sha1(f"blob {len(raw)}\0".encode("ascii")+raw).hexdigest()

def validate_task131_contract(x:dict[str,Any],*,root:str|Path)->dict[str,Any]:
    _r(x.get("schema")=="TASK131_WEB_INDEX_PROCUREMENT_IDENTIFIER_DISCOVERY_V1","TASK131_SCHEMA")
    _r(x.get("mode")=="T1_BOUNDED_WEB_INDEXED_PRIMARY_REFERENT_DISCOVERY","TASK131_MODE")
    root=Path(root)
    up=x.get("upstream") or {}
    _r(set(up)=={"task126","task127","task130"},"TASK131_UPSTREAM_SET")
    for key in ("task126","task127","task130"):
        meta=up[key]
        raw=(root/str(meta.get("path") or "")).read_bytes()
        _r(_git_blob_sha(raw)==meta.get("git_blob_sha"),f"TASK131_{key.upper()}_BLOB")
    t126=json.loads((root/up["task126"]["path"]).read_text(encoding="utf-8"))
    t127=json.loads((root/up["task127"]["path"]).read_text(encoding="utf-8"))
    t130=json.loads((root/up["task130"]["path"]).read_text(encoding="utf-8"))
    _r(t126.get("selected_next")=="JOM_7126_2025_EITI_CREDENCIAMENTO","TASK131_TASK126_SELECTION")
    _r(t127.get("result")=="STOP_TASK127_JOM_PDF_TRANSPORT_FAILED_ZERO_BYTES_NO_DATA_CONCLUSION","TASK131_TASK127_STOP")
    _r(t130.get("result")=="PASS_TASK130_EXHAUSTIVE_PNCP_SCOPE_NO_STRONG_POLICY_CANDIDATES","TASK131_TASK130_RESULT")

    target=x.get("target") or {}
    _r(target.get("procurement_title")=="EDITAL DE CREDENCIAMENTO ESCOLA EM TEMPO INTEGRAL 2026","TASK131_TITLE")
    _r(target.get("policy_program")=="PROGRAMA DE EDUCACAO INTEGRAL","TASK131_POLICY")
    _r(target.get("selected_pdf_url")=="https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_27112025163143.pdf","TASK131_PDF")

    s=x.get("search") or {}
    _r(s.get("allowed_target_domains")==["ecrie.com.br","limeira.sp.gov.br"],"TASK131_DOMAINS")
    _r(s.get("query_family_count_max")==8,"TASK131_FAMILIES")
    _r(s.get("search_query_count_max")==16,"TASK131_QUERIES")
    for key in ("direct_pdf_open_requests","raw_pdf_requests","pncp_requests","drive_reads","retry"):
        _r(s.get(key)==0,f"TASK131_{key.upper()}")
    _r(s.get("query_families")==[
      "PROCESSO_ADMINISTRATIVO","PROCESSO","EDITAL_NUMBER","CREDENCIAMENTO_NUMBER",
      "INEXIGIBILIDADE","CHAMAMENTO","BUDGET_FIELDS","OFICINEIROS_POLICY_PROCESS"
    ],"TASK131_QUERY_FAMILIES")

    ids=x.get("identifier_types") or []
    _r(len(ids)==7 and len(set(ids))==7,"TASK131_IDENTIFIER_TYPES")
    sem=x.get("evidence_semantics") or {}
    _r(sem.get("search_index_snippet_max_status")=="CANDIDATE","TASK131_STATUS_CAP")
    _r(sem.get("candidate_status")=="CANDIDATE_ADMINISTRATIVE_IDENTIFIER_REQUIRES_PRIMARY_VERIFICATION","TASK131_CANDIDATE_STATUS")
    _r(sem.get("may_select_future_primary_lookup") is True,"TASK131_PRIMARY_SELECTION")
    for key in ("financial_identity","transaction_identity","expenditure_attribution","supplier_contract_linkage","weak_term_contract_join"):
        _r(sem.get(key) is False,f"TASK131_SEM_{key.upper()}")

    p=x.get("persistence") or {}
    _r(p.get("raw_web_content") is False,"TASK131_RAW")
    _r(p.get("sanitized_query_log_git") is True and p.get("sanitized_candidate_evidence_git") is True,"TASK131_SANITIZED")
    for key in ("drive_write","bronze","silver","gold","rag","state_registry","queue","serving","publication"):
        _r(p.get(key) is False,"TASK131_PERSIST")
    _r(x.get("future_primary_read_authorized") is False,"TASK131_FUTURE_PRIMARY")
    _r(x.get("future_weak_join_authorized") is False,"TASK131_FUTURE_WEAK")
    return x

def load_task131_contract(path:str|Path,*,root:str|Path)->dict[str,Any]:
    try:
        x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task131Stop("TASK131_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task131Stop("TASK131_JSON") from exc
    _r(isinstance(x,dict),"TASK131_OBJECT")
    return validate_task131_contract(x,root=root)
