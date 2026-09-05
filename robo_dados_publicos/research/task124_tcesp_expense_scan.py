from __future__ import annotations
import json
from pathlib import Path
from typing import Any
class Task124Stop(RuntimeError): pass
def _r(c:bool,code:str)->None:
    if not c: raise Task124Stop(code)
def validate_task124_contract(x:dict[str,Any])->dict[str,Any]:
    _r(x.get("schema")=="TASK124_TCESP_LIMEIRA_2026_EXPENSE_SCAN_V1","TASK124_SCHEMA")
    _r(x.get("mode")=="T1_SINGLE_SOURCE_BOUNDED_TCESP_ZIP_SCAN","TASK124_MODE")
    s=x.get("source") or {}
    _r(s.get("url")=="https://transparencia.tce.sp.gov.br/sites/default/files/csv/despesas-limeira-2026.zip","TASK124_URL")
    _r(s.get("host")=="transparencia.tce.sp.gov.br","TASK124_HOST")
    _r(s.get("source_role")=="SECONDARY_AGGREGATOR","TASK124_ROLE")
    _r(s.get("max_compressed_bytes")==10485760,"TASK124_BYTES")
    n=x.get("network") or {}
    _r(n.get("get_requests_max")==1,"TASK124_REQUEST_BUDGET")
    for k in ("retries","pagination","redirect_host_change_allowed","other_hosts_allowed"):
        _r(n.get(k) is False,f"TASK124_NETWORK_{k.upper()}")
    z=x.get("zip_safety") or {}
    _r(z.get("max_members")==10,"TASK124_ZIP_MEMBERS")
    _r(z.get("max_total_uncompressed_bytes")==104857600,"TASK124_ZIP_SIZE")
    for k in ("path_traversal_forbidden","symlink_forbidden","csv_members_only"):
        _r(z.get(k) is True,f"TASK124_ZIP_{k.upper()}")
    scan=x.get("scan") or {}
    _r(scan.get("exact_code_tokens")==["2607004"],"TASK124_CODE")
    _r(scan.get("fuzzy_matching") is False,"TASK124_FUZZY")
    _r(scan.get("full_local_row_scan_allowed") is True,"TASK124_LOCAL_SCAN")
    _r(scan.get("require_row_sha256") is True,"TASK124_ROW_HASH")
    sem=x.get("semantics") or {}
    for k in ("automatic_financial_identity","automatic_transaction_identity"):
        _r(sem.get(k) is False,f"TASK124_SEM_{k.upper()}")
    _r(sem.get("primary_municipal_verification_required") is True,"TASK124_PRIMARY_VERIFY")
    p=x.get("persistence") or {}
    _r(p and all(v is False for v in p.values()),"TASK124_PERSIST")
    _r(x.get("future_primary_verification_authorized") is False,"TASK124_FUTURE")
    return x
def load_task124_contract(path:str|Path)->dict[str,Any]:
    try: x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as e: raise Task124Stop("TASK124_MISSING") from e
    except json.JSONDecodeError as e: raise Task124Stop("TASK124_JSON") from e
    _r(isinstance(x,dict),"TASK124_OBJECT")
    return validate_task124_contract(x)
