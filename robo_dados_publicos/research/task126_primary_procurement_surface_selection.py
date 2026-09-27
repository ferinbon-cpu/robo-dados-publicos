from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class Task126Stop(RuntimeError):
    pass

def _r(c: bool, code: str) -> None:
    if not c:
        raise Task126Stop(code)

def validate_task126_contract(x: dict[str, Any]) -> dict[str, Any]:
    _r(x.get("schema")=="TASK126_PRIMARY_PROCUREMENT_SURFACE_SELECTION_V1","TASK126_SCHEMA")
    _r(x.get("mode")=="T0_PUBLIC_WEB_DISCOVERY_SELECTION_ONLY","TASK126_MODE")
    up=x.get("upstream") or {}
    _r(up.get("resolver_task")=="TASK_122","TASK126_UPSTREAM_RESOLVER")
    _r(up.get("drive_inventory_task")=="TASK_123","TASK126_UPSTREAM_DRIVE")
    _r(up.get("tcesp_zip_attempts")==["TASK_124","TASK_125"],"TASK126_UPSTREAM_TCESP")
    _r(up.get("current_identity_status")=="UNKNOWN","TASK126_IDENTITY_STATUS")
    _r(up.get("required_bridge")==["EXPLICIT_POLICY_MARKER","STABLE_ACCOUNTING_IDENTIFIER","EXECUTION_EVENT"],"TASK126_BRIDGE")

    candidates=x.get("candidates") or []
    _r(len(candidates)==3,"TASK126_CANDIDATE_COUNT")
    ids=[c.get("id") for c in candidates]
    _r(ids==["PREFEITURA_NEWS_OFICINEIROS_2026","JOM_7126_2025_EITI_CREDENCIAMENTO","TCESP_HTML_EXPENSE_DETAIL"],"TASK126_CANDIDATE_SET")
    _r(candidates[0].get("source_role")=="MUNICIPAL_PRIMARY_PUBLIC_INFORMATION","TASK126_NEWS_ROLE")
    _r(candidates[1].get("source_role")=="MUNICIPAL_PRIMARY_NORMATIVE_PROCUREMENT","TASK126_JOM_ROLE")
    _r(candidates[2].get("source_role")=="SECONDARY_AGGREGATOR","TASK126_TCESP_ROLE")
    _r(candidates[2].get("municipal_primary_verification_required") is True,"TASK126_TCESP_PRIMARY_VERIFY")
    _r(sum(1 for c in candidates if c.get("selected_for_next_read") is True)==1,"TASK126_ONE_SELECTION")

    sel=x.get("selection") or {}
    _r(sel.get("selected_candidate_id")=="JOM_7126_2025_EITI_CREDENCIAMENTO","TASK126_SELECTED")
    _r(sel.get("next_read_exact_url")=="https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_27112025163143.pdf","TASK126_URL")
    _r(sel.get("max_source_gets")==1,"TASK126_GET_BUDGET")
    _r(sel.get("retry") is False,"TASK126_RETRY")
    _r(sel.get("redirects_max")==0,"TASK126_REDIRECTS")
    terms=set(sel.get("terms") or [])
    for term in {"DOTACAO","FICHA","PROGRAMA","ACAO","SUBACAO","UNIDADE ORCAMENTARIA","FONTE","DESTINACAO","PROCESSO ADMINISTRATIVO","EMPENHO"}:
        _r(term in terms,"TASK126_TERM_SET")

    guards=x.get("guards") or {}
    _r(guards and all(v is False for v in guards.values()),"TASK126_GUARDS")
    effects=x.get("effects") or {}
    _r(effects and all(v==0 for v in effects.values()),"TASK126_EFFECTS")
    _r(x.get("future_source_read_authorized") is False,"TASK126_FUTURE_SOURCE")
    return x

def load_task126_contract(path: str | Path) -> dict[str, Any]:
    try:
        x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise Task126Stop("TASK126_MISSING") from e
    except json.JSONDecodeError as e:
        raise Task126Stop("TASK126_JSON") from e
    _r(isinstance(x,dict),"TASK126_OBJECT")
    return validate_task126_contract(x)
