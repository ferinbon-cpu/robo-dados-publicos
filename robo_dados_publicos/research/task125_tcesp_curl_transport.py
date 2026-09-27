from __future__ import annotations
import json
from pathlib import Path
from typing import Any
class Task125Stop(RuntimeError): pass
def _r(c:bool,code:str)->None:
    if not c: raise Task125Stop(code)
def validate_task125_contract(x:dict[str,Any])->dict[str,Any]:
    _r(x.get("schema")=="TASK125_TCESP_CURL_TRANSPORT_V1","TASK125_SCHEMA")
    _r(x.get("mode")=="T1_SINGLE_USE_EXACT_CURL_GET","TASK125_MODE")
    s=x.get("source") or {}
    _r(s.get("url")=="https://transparencia.tce.sp.gov.br/sites/default/files/csv/despesas-limeira-2026.zip","TASK125_URL")
    _r(s.get("host")=="transparencia.tce.sp.gov.br","TASK125_HOST")
    _r(s.get("source_role")=="SECONDARY_AGGREGATOR","TASK125_ROLE")
    _r(s.get("max_bytes")==10485760,"TASK125_BYTES")
    c=x.get("curl_contract") or {}
    _r(c.get("get_requests_max")==1,"TASK125_GET")
    _r(c.get("head_requests")==0,"TASK125_HEAD")
    _r(c.get("max_redirs")==0,"TASK125_REDIRECT")
    _r(c.get("fail_on_http_error") is True,"TASK125_FAIL")
    _r(c.get("silent") is True and c.get("show_error") is True,"TASK125_OUTPUT")
    _r(c.get("retry")==0,"TASK125_RETRY")
    _r(c.get("exact_url_only") is True,"TASK125_EXACT")
    lp=x.get("local_processing") or {}
    _r(lp.get("sha256") is True and lp.get("verify_zip") is True,"TASK125_LOCAL")
    _r(lp.get("max_members")==10 and lp.get("max_uncompressed_bytes")==104857600,"TASK125_ZIP_LIMITS")
    _r(lp.get("csv_only") is True,"TASK125_CSV")
    _r(lp.get("fuzzy_matching") is False,"TASK125_FUZZY")
    sem=x.get("semantics") or {}
    _r(sem.get("source_role")=="SECONDARY_AGGREGATOR","TASK125_SEM_ROLE")
    _r(sem.get("automatic_financial_identity") is False,"TASK125_FIN")
    _r(sem.get("automatic_transaction_identity") is False,"TASK125_TX")
    _r(sem.get("primary_municipal_verification_required") is True,"TASK125_PRIMARY")
    p=x.get("persistence") or {}
    _r(p and all(v is False for v in p.values()),"TASK125_PERSIST")
    _r(x.get("future_retry_authorized") is False,"TASK125_FUTURE_RETRY")
    _r(x.get("future_primary_verification_authorized") is False,"TASK125_FUTURE_PRIMARY")
    return x
def load_task125_contract(path:str|Path)->dict[str,Any]:
    try: x=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as e: raise Task125Stop("TASK125_MISSING") from e
    except json.JSONDecodeError as e: raise Task125Stop("TASK125_JSON") from e
    _r(isinstance(x,dict),"TASK125_OBJECT"); return validate_task125_contract(x)
