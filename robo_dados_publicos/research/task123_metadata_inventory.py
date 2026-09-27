from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class Task123Stop(RuntimeError):
    pass

def _require(condition: bool, code: str)->None:
    if not condition:
        raise Task123Stop(code)

def validate_task123_contract(data:dict[str,Any])->dict[str,Any]:
    _require(data.get("schema")=="TASK123_GRANULAR_EXECUTION_METADATA_INVENTORY_V1","TASK123_SCHEMA")
    _require(data.get("mode")=="T1_BOUNDED_DRIVE_METADATA_ONLY_FILENAME_INVENTORY","TASK123_MODE")
    s=data.get("search_contract") or {}
    _require(s.get("item_type")=="document","TASK123_ITEM_TYPE")
    _require(s.get("best_effort_fetch") is False,"TASK123_FETCH")
    _require(s.get("filename_only_filters") is True,"TASK123_FILENAME_ONLY")
    _require(s.get("max_probes")==8,"TASK123_PROBE_BUDGET")
    _require(s.get("topn_per_probe")==20,"TASK123_TOPN")
    _require(s.get("page_token_allowed") is False,"TASK123_PAGINATION")
    _require(s.get("content_hydration_allowed") is False,"TASK123_HYDRATION")
    _require(s.get("allowed_probe_terms")==["fomento","2607004","empenho","liquidacao","pagamento","balancete","ficha","despesa"],"TASK123_TERMS")
    e=data.get("remote_effects") or {}
    _require(e.get("drive_metadata_search") is True,"TASK123_METADATA_SEARCH")
    for key,value in e.items():
        if key!="drive_metadata_search":
            _require(value is False,f"TASK123_EFFECT_{key.upper()}")
    _require(data.get("content_claims_allowed") is False,"TASK123_CONTENT_CLAIMS")
    _require(data.get("future_content_read_authorized") is False,"TASK123_FUTURE_READ")
    return data

def load_task123_contract(path:str|Path)->dict[str,Any]:
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task123Stop("TASK123_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task123Stop("TASK123_JSON") from exc
    _require(isinstance(data,dict),"TASK123_OBJECT")
    return validate_task123_contract(data)
