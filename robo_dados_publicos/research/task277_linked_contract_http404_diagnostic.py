from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task277_linked_contract_http404_diagnostic.v1.json"
EV=ROOT/"docs/evidence/TASK_277_PRELIVE_LINKED_CONTRACT_HTTP404_DIAGNOSTIC_645_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
    if not x:raise Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"));stop(c["schema"]=="TASK277_LINKED_CONTRACT_HTTP404_DIAGNOSTIC_V1","CFG")
    t=c["target"];stop(t["pagina"]==1 and t["tamanhoPagina"]==50 and t["url"].endswith("?pagina=1&tamanhoPagina=50"),"TARGET")
    p=c["probe"];stop(p["max_remote_get_count"]==1 and not p["retry"] and not p["follow_redirects"] and not p["alternate_url_discovery"] and not p["automatic_pagination"],"BOUNDS")
    stop(not p["raw_body_persistence"] and not p["traverse_returned_contracts"],"PERSIST")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"));stop(e["live_state"]=="NOT_EXECUTED","PRELIVE");stop(e["source_task276"]["absence_inference"] is False,"ABSENCE");return e
def primitive(v):return v is None or isinstance(v,(str,int,float,bool))
def sanitize_contract(row,c):
    out={k:row.get(k) for k in c["contract_projection"]["scalar_fields"] if k in row and primitive(row.get(k))}
    for name,fields in c["contract_projection"]["nested_fields"].items():
        v=row.get(name)
        if isinstance(v,dict):out[name]={k:v.get(k) for k in fields if k in v and primitive(v.get(k))}
    for field in c["contract_projection"]["excluded_fields"]:stop(field not in out,"PRIVACY_LEAK")
    return out
def sanitize_diagnostic(obj,c):
    if not isinstance(obj,dict):return {}
    allow=set(c["diagnostic_projection"]["allowed_scalar_fields"]);limit=int(c["diagnostic_projection"]["max_string_chars"])
    out={}
    for k,v in obj.items():
        if k in allow and primitive(v):out[k]=v[:limit] if isinstance(v,str) else v
    return out
def parse_page(obj,c):
    if not isinstance(obj,dict) or not isinstance(obj.get("data"),list):return False,[],{}
    rows=obj["data"]
    if not all(isinstance(x,dict) for x in rows):return False,[],{}
    for x in rows:
        v=x.get("numeroControlePNCPCompra")
        if v is not None:stop(v==c["target"]["purchase_control"],"PURCHASE_IDENTITY")
    contracts=[sanitize_contract(x,c) for x in rows]
    meta={k:obj.get(k) for k in c["page_contract"]["metadata_fields"] if k in obj and primitive(obj.get(k))}
    if "numeroPagina" in meta and meta["numeroPagina"] is not None:stop(int(meta["numeroPagina"])==1,"PAGE")
    return True,contracts,meta
def classify(http_code,shape,page_valid,contracts,meta):
    if http_code==404 and shape=="OBJECT":return "LINKED_CONTRACT_PAGE1_HTTP404_SAFE_DIAGNOSTIC_CAPTURED"
    if http_code==200 and shape=="OBJECT" and page_valid:
        pages=meta.get("totalPaginas");remaining=meta.get("paginasRestantes");total=meta.get("totalRegistros")
        more=(isinstance(pages,int) and pages>1) or (isinstance(remaining,int) and remaining>0)
        if more:return "LINKED_CONTRACT_PAGE1_PARTIAL_MORE_PAGES"
        if len(contracts)==0 and total==0:return "LINKED_CONTRACT_PAGE1_COMPLETE_ZERO_ROWS"
        if len(contracts)>0 and (total is None or total==len(contracts)):return "LINKED_CONTRACT_PAGE1_COMPLETE_WITH_ROWS"
    return "LINKED_CONTRACT_PAGE1_UNRESOLVED"
def curl_get(url,*,c):
    p=c["probe"]
    with tempfile.NamedTemporaryFile(prefix="task277_",delete=False) as tmp:path=Path(tmp.name)
    try:
        cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(p["connect_timeout_seconds"]),"--max-time",str(p["max_time_seconds"]),"--max-filesize",str(p["max_body_bytes"]),"--output",str(path),"--header","Accept: */*","--user-agent","robo-dados-publicos-task277/0.8.0","--write-out","%{json}",url]
        q=subprocess.run(cmd,capture_output=True,text=True,timeout=p["max_time_seconds"]+15,check=False);body=path.read_bytes();stop(len(body)<=p["max_body_bytes"],"BODY_BOUND")
        m={}
        try:m=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
        except Exception:pass
        parsed=None;err=None
        try:parsed=json.loads(body.decode("utf-8"))
        except Exception as exc:err=type(exc).__name__
        shape="OBJECT" if isinstance(parsed,dict) else ("LIST" if isinstance(parsed,list) else "OTHER")
        page_valid,contracts,meta=parse_page(parsed,c) if isinstance(parsed,dict) else (False,[],{})
        diag=sanitize_diagnostic(parsed,c) if isinstance(parsed,dict) and not page_valid else {}
        keys=sorted(parsed.keys()) if isinstance(parsed,dict) else []
        outcome=classify(int(m.get("http_code") or 0),shape,page_valid,contracts,meta)
        return {"requested_url":url,"http_code":int(m.get("http_code") or 0),"content_type":m.get("content_type"),"url_effective":m.get("url_effective"),"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,"body_bytes":len(body),"body_sha256":hashlib.sha256(body).hexdigest() if body else None,"json_error":err,"json_shape":shape,"response_keys":keys,"page_contract_valid":page_valid,"page_meta":meta,"contracts":contracts,"contracts_sha256":hashlib.sha256(json.dumps(contracts,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if page_valid else None,"diagnostic_scalars":diag,"diagnostic_sha256":hashlib.sha256(json.dumps(diag,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if diag else None,"outcome":outcome,"remote_get_count":1,"raw_body_persisted":False}
    finally:path.unlink(missing_ok=True)
def validate_auth(a:Mapping[str,Any]|None,sha:str,c):
    if not a:return "STOP_TASK277_LIVE_NOT_AUTHORIZED"
    if not HEX40.fullmatch(sha or ""):return "STOP_TASK277_IMPLEMENTATION_SHA"
    t=c["target"]
    req={"task":"TASK_277_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_1_PNCP_LINKED_CONTRACT_HTTP404_DIAGNOSTIC_645","purchase_control":t["purchase_control"],"requested_url":t["url"],"pagina":1,"tamanhoPagina":50,"max_remote_get_count":1,"attempt_count":1,"owner_authorized":True,"source_network_authorized":True,"accept_header":"*/*","follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"automatic_pagination":False,"raw_body_persistence":False,"traverse_returned_contracts":False,"persist_supplier_identity":False,"persist_usuario_nome":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
    return "PASS_TASK277_LIVE_AUTHORIZATION" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK277_AUTHORIZATION_CONTRACT_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
    if not offline_test_mode:
        s=validate_auth(authorization,expected_implementation_sha,c)
        if s!="PASS_TASK277_LIVE_AUTHORIZATION":return {"schema":"TASK277_RESULT_V1","status":s,"source_get_count":0}
    r=getter(c["target"]["url"],c=c);stop(r["remote_get_count"]==1 and r["raw_body_persisted"] is False,"GET_BOUND")
    if r.get("url_effective"):stop(r["url_effective"]==c["target"]["url"],"URL_DRIFT")
    return {"schema":"TASK277_LINKED_CONTRACT_HTTP404_DIAGNOSTIC_RESULT_V1","status":"PASS_TASK277_SINGLE_LINKED_CONTRACT_DIAGNOSTIC","purchase_control":c["target"]["purchase_control"],**r,"retry_performed":False,"redirect_followed":False,"alternate_url_discovery_performed":False,"automatic_pagination_performed":False,"traverse_returned_contracts":False,"absence_inference_permanent":False}
