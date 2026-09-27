from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task279_paired_pncp_health_645.v1.json"
EV=ROOT/"docs/evidence/TASK_279_PRELIVE_PAIRED_PNCP_HEALTH_645_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
    if not x: raise Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"))
    stop(c["schema"]=="TASK279_PAIRED_PNCP_HEALTH_645_V1","CFG")
    p=c["probe"];stop(p["max_remote_get_count"]==2 and p["max_gets_per_url"]==1,"GETS")
    stop(not p["retry"] and not p["follow_redirects"] and not p["alternate_url_discovery"] and not p["automatic_pagination"],"BOUNDS")
    stop(not p["raw_body_persistence"] and not p["traverse_returned_contracts"],"PERSIST")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"));stop(e["live_state"]=="NOT_EXECUTED","PRELIVE");return e
def primitive(v):return v is None or isinstance(v,(str,int,float,bool))
def sanitize_contract(row,c):
    out={k:row.get(k) for k in c["contract_projection"]["scalar_fields"] if k in row and primitive(row.get(k))}
    for name,fields in c["contract_projection"]["nested_fields"].items():
        v=row.get(name)
        if isinstance(v,dict):out[name]={k:v.get(k) for k in fields if k in v and primitive(v.get(k))}
    for field in c["contract_projection"]["excluded_fields"]:stop(field not in out,"PRIVACY")
    return out
def sanitize_diag(obj,c):
    if not isinstance(obj,dict):return {}
    allow=set(c["diagnostic_projection"]["allowed_scalar_fields"]);n=int(c["diagnostic_projection"]["max_string_chars"])
    return {k:(v[:n] if isinstance(v,str) else v) for k,v in obj.items() if k in allow and primitive(v)}
def request(url,c):
    p=c["probe"]
    with tempfile.NamedTemporaryFile(prefix="task279_",delete=False) as tmp:path=Path(tmp.name)
    try:
        cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(p["connect_timeout_seconds"]),"--max-time",str(p["max_time_seconds_per_get"]),"--max-filesize",str(p["max_body_bytes_per_get"]),"--output",str(path),"--header","Accept: */*","--user-agent","robo-dados-publicos-task279/0.8.0","--write-out","%{json}",url]
        q=subprocess.run(cmd,capture_output=True,text=True,timeout=p["max_time_seconds_per_get"]+15,check=False)
        b=path.read_bytes();stop(len(b)<=p["max_body_bytes_per_get"],"BODY")
        meta={}
        try:meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
        except Exception:pass
        parsed=None;err=None
        try:parsed=json.loads(b.decode("utf-8"))
        except Exception as exc:err=type(exc).__name__
        shape="LIST" if isinstance(parsed,list) else ("OBJECT" if isinstance(parsed,dict) else "OTHER")
        return {"url":url,"http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,"body_bytes":len(b),"body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_shape":shape,"json_error":err,"parsed":parsed,"raw_body_persisted":False}
    finally:path.unlink(missing_ok=True)
def summarize_health(r):
    parsed=r.pop("parsed",None)
    item_count=len(parsed) if isinstance(parsed,list) else None
    return {**r,"item_count":item_count,"item_content_persisted":False}
def summarize_target(r,c):
    parsed=r.pop("parsed",None);contracts=[];meta={};diag={};page_valid=False
    if isinstance(parsed,dict) and isinstance(parsed.get("data"),list) and all(isinstance(x,dict) for x in parsed["data"]):
        page_valid=True
        for x in parsed["data"]:
            v=x.get("numeroControlePNCPCompra")
            if v is not None:stop(v==c["target"]["purchase_control"],"IDENTITY")
        contracts=[sanitize_contract(x,c) for x in parsed["data"]]
        meta={k:parsed.get(k) for k in c["page_contract"]["metadata_fields"] if k in parsed and primitive(parsed.get(k))}
        if "numeroPagina" in meta and meta["numeroPagina"] is not None:stop(int(meta["numeroPagina"])==1,"PAGE")
    elif isinstance(parsed,dict):
        diag=sanitize_diag(parsed,c)
    return {**r,"page_contract_valid":page_valid,"page_meta":meta,"contracts":contracts,"contracts_sha256":hashlib.sha256(json.dumps(contracts,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if page_valid else None,"diagnostic_scalars":diag,"diagnostic_sha256":hashlib.sha256(json.dumps(diag,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if diag else None}
def classify(h,t):
    healthy=h["http_code"]==200 and h["json_shape"]=="LIST"
    if healthy and t["http_code"]>=500:return "PNCP_ITEMS_HEALTHY_LINKED_CONTRACT_ROUTE_UNAVAILABLE"
    if healthy and t["http_code"]==404 and t["json_shape"]=="OBJECT":return "PNCP_ITEMS_HEALTHY_LINKED_CONTRACT_HTTP404_CONTEXT"
    if healthy and t["http_code"]==200 and t["page_contract_valid"]:return "LINKED_CONTRACT_RESOLVED_UNDER_HEALTHY_PNCP_CONTEXT"
    return "PAIRED_HEALTH_AMBIGUOUS"
def validate_auth(a:Mapping[str,Any]|None,sha:str,c):
    if not a:return "STOP_TASK279_LIVE_NOT_AUTHORIZED"
    if not HEX40.fullmatch(sha or ""):return "STOP_TASK279_IMPLEMENTATION_SHA"
    req={"task":"TASK_279_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_2_PNCP_PAIRED_HEALTH_ITEMS_AND_LINKED_CONTRACT_645","health_url":c["health"]["url"],"target_url":c["target"]["url"],"max_remote_get_count":2,"attempt_count":1,"owner_authorized":True,"source_network_authorized":True,"authorization_mode":"BOUNDED_OWNER_BIG_LEAP_LINKED_CONTRACT_DIAGNOSTIC","owner_phrase":"Prossiga autorizado grande salto","follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"automatic_pagination":False,"raw_body_persistence":False,"traverse_returned_contracts":False,"persist_item_content":False,"persist_supplier_identity":False,"persist_usuario_nome":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
    return "PASS_TASK279_LIVE_AUTHORIZATION" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK279_AUTHORIZATION_CONTRACT_MISMATCH"
def execute(c,e,*,getter=request,authorization=None,expected_implementation_sha="",offline_test_mode=False):
    if not offline_test_mode:
        s=validate_auth(authorization,expected_implementation_sha,c)
        if s!="PASS_TASK279_LIVE_AUTHORIZATION":return {"schema":"TASK279_RESULT_V1","status":s,"source_get_count":0}
    hr=summarize_health(getter(c["health"]["url"],c))
    tr=summarize_target(getter(c["target"]["url"],c),c)
    stop(hr["url"]==c["health"]["url"] and tr["url"]==c["target"]["url"],"URL")
    stop(hr["raw_body_persisted"] is False and tr["raw_body_persisted"] is False,"RAW")
    outcome=classify(hr,tr)
    return {"schema":"TASK279_PAIRED_PNCP_HEALTH_RESULT_V1","status":"PASS_TASK279_PAIRED_HEALTH_OBSERVATION","outcome":outcome,"purchase_control":c["target"]["purchase_control"],"health":hr,"target":tr,"source_get_count":2,"retry_performed":False,"redirect_followed":False,"automatic_pagination_performed":False,"absence_inference_permanent":False}
