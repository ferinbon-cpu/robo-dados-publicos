from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task274_linked_contract_probe_645.v1.json"
EV=ROOT/"docs/evidence/TASK_274_PRELIVE_LINKED_CONTRACT_645_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
    if not x: raise Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"))
    stop(c["schema"]=="TASK274_LINKED_CONTRACT_PROBE_645_V1","CFG")
    p=c["probe"]
    stop(p["max_remote_get_count"]==1 and not p["retry"] and not p["follow_redirects"] and not p["alternate_url_discovery"] and not p["pagination"],"BOUNDS")
    stop(not p["raw_body_persistence"] and not p["traverse_returned_contracts"],"NO_TRAVERSE")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"));stop(e["live_state"]=="NOT_EXECUTED","PRELIVE");return e
def primitive(v): return v is None or isinstance(v,(str,int,float,bool))
def sanitize(row,c):
    out={k:row.get(k) for k in c["projection"]["scalar_fields"] if k in row and primitive(row.get(k))}
    for name,fields in c["projection"]["nested_fields"].items():
        v=row.get(name)
        if isinstance(v,dict):
            out[name]={k:v.get(k) for k in fields if k in v and primitive(v.get(k))}
    for field in c["projection"]["excluded_fields"]:
        stop(field not in out,"PRIVACY_LEAK")
    return out
def curl_get(url,*,c):
    p=c["probe"]
    with tempfile.NamedTemporaryFile(prefix="task274_",delete=False) as tmp:path=Path(tmp.name)
    try:
        cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(p["connect_timeout_seconds"]),"--max-time",str(p["max_time_seconds"]),"--max-filesize",str(p["max_body_bytes"]),"--output",str(path),"--header","Accept: application/json","--user-agent","robo-dados-publicos-task274/0.8.0","--write-out","%{json}",url]
        q=subprocess.run(cmd,capture_output=True,text=True,timeout=p["max_time_seconds"]+15,check=False)
        body=path.read_bytes();stop(len(body)<=p["max_body_bytes"],"BODY_BOUND")
        meta={}
        try: meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
        except Exception: pass
        parsed=None;err=None
        try: parsed=json.loads(body.decode("utf-8"))
        except Exception as exc: err=type(exc).__name__
        shape="LIST" if isinstance(parsed,list) else ("OBJECT" if isinstance(parsed,dict) else "OTHER")
        rows=[x for x in parsed if isinstance(x,dict)] if isinstance(parsed,list) else []
        identity_valid=all(x.get("numeroControlePNCPCompra") in (None,c["target"]["purchase_control"]) for x in rows) if isinstance(parsed,list) else None
        selected=[sanitize(x,c) for x in rows] if identity_valid else []
        keys=sorted({k for x in rows for k in x.keys()})
        return {"requested_url":url,"http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,"body_bytes":len(body),"body_sha256":hashlib.sha256(body).hexdigest() if body else None,"json_error":err,"json_shape":shape,"row_count":len(parsed) if isinstance(parsed,list) else None,"item_keys":keys,"purchase_identity_valid":identity_valid,"contracts":selected,"contracts_sha256":hashlib.sha256(json.dumps(selected,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if isinstance(parsed,list) and identity_valid else None,"remote_get_count":1,"raw_body_persisted":False}
    finally:path.unlink(missing_ok=True)
def validate_auth(a:Mapping[str,Any]|None,sha:str,c):
    if not a:return "STOP_TASK274_LIVE_NOT_AUTHORIZED"
    if not HEX40.fullmatch(sha or ""):return "STOP_TASK274_IMPLEMENTATION_SHA"
    t=c["target"]
    req={"task":"TASK_274_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_1_PNCP_LINKED_CONTRACT_ROUTE_PROBE_645","purchase_control":t["purchase_control"],"requested_url":t["url"],"max_remote_get_count":1,"attempt_count":1,"owner_authorized":True,"source_network_authorized":True,"authorization_mode":"BOUNDED_STANDING_OWNER_LINKED_CONTRACT_PROBE_645_FRONTIER","owner_phrase":"Prossiga autorizado até compltar tudo","follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"pagination":False,"raw_body_persistence":False,"traverse_returned_contracts":False,"persist_supplier_identity":False,"persist_usuario_nome":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
    return "PASS_TASK274_LIVE_AUTHORIZATION" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK274_AUTHORIZATION_CONTRACT_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
    if not offline_test_mode:
        s=validate_auth(authorization,expected_implementation_sha,c)
        if s!="PASS_TASK274_LIVE_AUTHORIZATION":return {"schema":"TASK274_RESULT_V1","status":s,"source_get_count":0}
    m=getter(c["target"]["url"],c=c)
    stop(m["remote_get_count"]==1 and m["raw_body_persisted"] is False,"GET_BOUND")
    if m.get("url_effective"):stop(m["url_effective"]==c["target"]["url"],"URL_DRIFT")
    ok=m["http_code"]==200 and m["json_shape"]=="LIST" and m["purchase_identity_valid"] is True
    outcome="LINKED_CONTRACT_ROUTE_HTTP200_EMPTY_LIST" if ok and m["row_count"]==0 else ("LINKED_CONTRACT_ROUTE_HTTP200_LIST" if ok else "LINKED_CONTRACT_ROUTE_UNRESOLVED_OBSERVATION")
    return {"schema":"TASK274_LINKED_CONTRACT_RESULT_V1","status":"PASS_TASK274_SINGLE_LINKED_CONTRACT_OBSERVATION","outcome":outcome,"purchase_control":c["target"]["purchase_control"],**m,"retry_performed":False,"redirect_followed":False,"alternate_url_discovery_performed":False,"pagination_performed":False,"traverse_returned_contracts":False,"absence_inference_allowed":False}
