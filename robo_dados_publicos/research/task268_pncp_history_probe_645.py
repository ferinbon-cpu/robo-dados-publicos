from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import HISTORY_ALLOW
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task268_pncp_history_probe_645.v1.json"
EV=ROOT/"docs/evidence/TASK_268_PRELIVE_PNCP_HISTORY_645_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos"
HEX40=re.compile(r"^[0-9a-f]{40}$")
class Task268Stop(RuntimeError): pass
def _stop(x,c):
    if not x: raise Task268Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(c["schema"]=="TASK268_PNCP_HISTORY_PROBE_645_V1","TASK268_CONFIG")
    _stop(c["source_task267"]["required_status"]=="8_OF_8_PNCP_ITEMS_RESOLVED_40_SANITIZED_ITEM_ROWS","TASK268_SOURCE")
    _stop(c["target"]["control"]=="45132495000140-1-000645/2026","TASK268_CONTROL")
    _stop(c["target"]["requested_url"].endswith("/2026/645/historico"),"TASK268_URL")
    _stop(c["history_allow"]==sorted(HISTORY_ALLOW),"TASK268_HISTORY_ALLOW")
    p=c["probe"];_stop(p["max_remote_get_count"]==1 and p["retry"] is False and p["follow_redirects"] is False and p["alternate_url_discovery"] is False,"TASK268_BOUNDS")
    _stop(p["raw_body_persistence"] is False and p["traverse_exposed_links"] is False,"TASK268_PERSIST")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(e["schema"]=="TASK268_PRELIVE_PNCP_HISTORY_645_V1","TASK268_EVIDENCE")
    _stop(e["live_state"]=="NOT_AUTHORIZED_NOT_EXECUTED","TASK268_PRELIVE")
    return e
def _primitive(v): return v is None or isinstance(v,(str,int,float,bool))
def _selected(x):
    return {k:x.get(k) for k in sorted(HISTORY_ALLOW) if k in x and _primitive(x.get(k))}
def _scalars(x):
    if not isinstance(x,dict): return {}
    return {str(k):(v[:500] if isinstance(v,str) else v) for k,v in x.items() if _primitive(v)}
def curl_get(url,*,connect_timeout,max_time,max_body_bytes):
    with tempfile.NamedTemporaryFile(prefix="task268_",delete=False) as tmp: p=Path(tmp.name)
    try:
        cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0",
             "--connect-timeout",str(connect_timeout),"--max-time",str(max_time),"--max-filesize",str(max_body_bytes),
             "--output",str(p),"--header","Accept: application/json","--user-agent","robo-dados-publicos-task268/0.8.0",
             "--write-out","%{json}",url]
        q=subprocess.run(cmd,capture_output=True,text=True,timeout=max_time+15,check=False)
        b=p.read_bytes();_stop(len(b)<=max_body_bytes,"TASK268_BODY_BOUND")
        meta={}
        try: meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
        except Exception: pass
        parsed=None;json_error=None
        try: parsed=json.loads(b.decode("utf-8"))
        except Exception as exc: json_error=type(exc).__name__
        if isinstance(parsed,list):
            selected=[_selected(x) for x in parsed if isinstance(x,dict)]
            event_keys=sorted({k for x in parsed if isinstance(x,dict) for k in x.keys()})
            shape="LIST";event_count=len(parsed);diag={}
        else:
            selected=[];event_keys=[];shape="OBJECT" if isinstance(parsed,dict) else "OTHER";event_count=None;diag=_scalars(parsed)
        return {"requested_url":url,"curl_exit_code":int(q.returncode),"curl_error":(q.stderr or "").strip()[:240] or None,
                "http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),
                "body_bytes":len(b),"body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_error":json_error,
                "json_shape":shape,"event_count":event_count,"event_keys":event_keys,"selected_history":selected,
                "diagnostic_scalars":diag,"remote_get_count":1,"raw_body_persisted":False}
    finally:
        p.unlink(missing_ok=True)
def validate_live_authorization(a:Mapping[str,Any]|None,sha:str,c):
    if not a: return "STOP_TASK268_LIVE_NOT_AUTHORIZED"
    if not HEX40.fullmatch(sha or ""): return "STOP_TASK268_IMPLEMENTATION_SHA"
    t=c["target"]
    req={"task":"TASK_268_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],
         "implementation_sha":sha,"operation":"EXACT_1_DOCUMENTED_PNCP_HISTORY_ROUTE_PROBE_645","control":t["control"],
         "requested_url":t["requested_url"],"max_remote_get_count":1,"attempt_count":1,"owner_authorized":True,
         "source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,
         "raw_body_persistence":False,"traverse_exposed_links":False,"prior_authorization_reused":False,
         "drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,
         "recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
    return "PASS_TASK268_LIVE_AUTHORIZATION" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK268_AUTHORIZATION_CONTRACT_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
    if not offline_test_mode:
        status=validate_live_authorization(authorization,expected_implementation_sha,c)
        if status!="PASS_TASK268_LIVE_AUTHORIZATION":
            return {"schema":"TASK268_PNCP_HISTORY_RESULT_V1","status":status,"source_get_count":0}
    t=c["target"];p=c["probe"]
    m=getter(t["requested_url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds"],max_body_bytes=p["max_body_bytes"])
    _stop(m["remote_get_count"]==1 and m["requested_url"]==t["requested_url"],"TASK268_GET")
    _stop(m["raw_body_persisted"] is False,"TASK268_RAW")
    if m.get("url_effective"): _stop(m["url_effective"]==t["requested_url"],"TASK268_EFFECTIVE_URL_DRIFT")
    ok=m["http_code"]==200 and m["json_shape"]=="LIST"
    outcome="DOCUMENTED_HISTORY_ROUTE_HTTP200_LIST" if ok else ("DOCUMENTED_HISTORY_ROUTE_ERROR_JSON" if m["json_shape"]=="OBJECT" else "DOCUMENTED_HISTORY_ROUTE_NON_LIST_RESPONSE")
    selected=m["selected_history"] if ok else []
    selected_sha=hashlib.sha256(json.dumps(selected,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if ok else None
    return {"schema":"TASK268_PNCP_HISTORY_RESULT_V1","status":"PASS_TASK268_SINGLE_HISTORY_ROUTE_OBSERVATION","outcome":outcome,
            "control":t["control"],"requested_url":t["requested_url"],"http_code":m["http_code"],"content_type":m.get("content_type"),
            "curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),"body_bytes":m.get("body_bytes"),
            "body_sha256":m.get("body_sha256"),"json_error":m.get("json_error"),"json_shape":m.get("json_shape"),
            "event_count":m.get("event_count") if ok else None,"event_keys":m.get("event_keys") if ok else [],
            "selected_history":selected,"selected_history_sha256":selected_sha,"diagnostic_scalars":{} if ok else m.get("diagnostic_scalars"),
            "source_get_count":1,"retry_performed":False,"redirect_followed":False,"alternate_url_discovery_performed":False,
            "traverse_exposed_links":False,"raw_body_persisted":False,"absence_inference_allowed":False}
