from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task270_pncp_history_v26_safe_645.v1.json"
EV=ROOT/"docs/evidence/TASK_270_PRELIVE_HISTORY_V26_SAFE_645_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError): pass
def stop(x,c):
    if not x: raise Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"))
    stop(c["schema"]=="TASK270_PNCP_HISTORY_V26_SAFE_SEMANTIC_CARRIER_V1","CFG")
    stop(c["target"]["control"]=="45132495000140-1-000645/2026","CONTROL")
    stop(c["excluded_projection_fields"]==["usuarioNome"],"EXCLUDED")
    stop("usuarioNome" not in c["safe_projection"],"PRIVACY")
    stop(len(c["safe_projection"])==15 and len(set(c["safe_projection"]))==15,"PROJECTION")
    p=c["probe"];stop(p["max_remote_get_count"]==1 and not p["retry"] and not p["follow_redirects"] and not p["alternate_url_discovery"],"BOUNDS")
    stop(not p["raw_body_persistence"] and not p["traverse_exposed_links"],"PERSIST")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"))
    stop(e["live_state"]=="NOT_AUTHORIZED_NOT_EXECUTED","PRELIVE")
    stop(e["prior_observation"]["semantic_values_sufficient"] is False,"NEED")
    return e
def primitive(v): return v is None or isinstance(v,(str,int,float,bool))
def project(row:dict[str,Any],fields:list[str])->dict[str,Any]:
    return {k:row.get(k) for k in fields if k in row and primitive(row.get(k))}
def validate_identity(row:dict[str,Any],c:dict[str,Any])->None:
    iv=c["identity_validation"]
    if "compraOrgaoCnpj" in row and row["compraOrgaoCnpj"] is not None: stop(str(row["compraOrgaoCnpj"])==iv["compraOrgaoCnpj"],"CNPJ_IDENTITY")
    if "compraAno" in row and row["compraAno"] is not None: stop(int(row["compraAno"])==iv["compraAno"],"YEAR_IDENTITY")
    if "compraSequencial" in row and row["compraSequencial"] is not None: stop(int(row["compraSequencial"])==iv["compraSequencial"],"SEQUENCE_IDENTITY")
def curl_get(url,*,connect_timeout,max_time,max_body_bytes,c):
    with tempfile.NamedTemporaryFile(prefix="task270_",delete=False) as tmp:p=Path(tmp.name)
    try:
        cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(connect_timeout),"--max-time",str(max_time),"--max-filesize",str(max_body_bytes),"--output",str(p),"--header","Accept: application/json","--user-agent","robo-dados-publicos-task270/0.8.0","--write-out","%{json}",url]
        q=subprocess.run(cmd,capture_output=True,text=True,timeout=max_time+15,check=False);b=p.read_bytes();stop(len(b)<=max_body_bytes,"BODY_BOUND")
        meta={}
        try:meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
        except Exception:pass
        parsed=None;err=None
        try:parsed=json.loads(b.decode("utf-8"))
        except Exception as exc:err=type(exc).__name__
        if isinstance(parsed,list):
            rows=[x for x in parsed if isinstance(x,dict)]
            for row in rows: validate_identity(row,c)
            selected=[project(row,c["safe_projection"]) for row in rows]
            stop(all("usuarioNome" not in x for x in selected),"PRIVACY_LEAK")
            keys=sorted({k for row in rows for k in row.keys()})
            shape="LIST";count=len(parsed);diag={}
        else:
            selected=[];keys=[];shape="OBJECT" if isinstance(parsed,dict) else "OTHER";count=None
            diag={str(k):(v[:500] if isinstance(v,str) else v) for k,v in (parsed.items() if isinstance(parsed,dict) else []) if primitive(v)}
        return {"requested_url":url,"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,"http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),"body_bytes":len(b),"body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_error":err,"json_shape":shape,"event_count":count,"event_keys":keys,"safe_events":selected,"diagnostic_scalars":diag,"remote_get_count":1,"raw_body_persisted":False}
    finally:p.unlink(missing_ok=True)
def validate_live_authorization(a:Mapping[str,Any]|None,sha:str,c):
    if not a:return "STOP_TASK270_LIVE_NOT_AUTHORIZED"
    if not HEX40.fullmatch(sha or ""):return "STOP_TASK270_IMPLEMENTATION_SHA"
    t=c["target"]
    req={"task":"TASK_270_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_1_PNCP_HISTORY_V26_SAFE_SEMANTIC_REOBSERVATION_645","control":t["control"],"requested_url":t["requested_url"],"max_remote_get_count":1,"attempt_count":1,"owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"raw_body_persistence":False,"traverse_exposed_links":False,"persist_usuario_nome":False,"prior_authorization_reused":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
    return "PASS_TASK270_LIVE_AUTHORIZATION" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK270_AUTHORIZATION_CONTRACT_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
    if not offline_test_mode:
        s=validate_live_authorization(authorization,expected_implementation_sha,c)
        if s!="PASS_TASK270_LIVE_AUTHORIZATION":return {"schema":"TASK270_RESULT_V1","status":s,"source_get_count":0}
    p=c["probe"];t=c["target"]
    m=getter(t["requested_url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds"],max_body_bytes=p["max_body_bytes"],c=c)
    stop(m["remote_get_count"]==1 and m["requested_url"]==t["requested_url"],"GET")
    stop(m["raw_body_persisted"] is False,"RAW")
    if m.get("url_effective"):stop(m["url_effective"]==t["requested_url"],"URL")
    ok=m["http_code"]==200 and m["json_shape"]=="LIST"
    safe=m["safe_events"] if ok else []
    stop(all("usuarioNome" not in x for x in safe),"PRIVACY_OUT")
    projection_sha=hashlib.sha256(json.dumps(safe,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if ok else None
    return {"schema":"TASK270_PNCP_HISTORY_V26_SAFE_RESULT_V1","status":"PASS_TASK270_SINGLE_SAFE_HISTORY_REOBSERVATION","outcome":"HISTORY_V26_SAFE_HTTP200_LIST" if ok else "HISTORY_V26_SAFE_UNRESOLVED_OBSERVATION","control":t["control"],"http_code":m["http_code"],"content_type":m.get("content_type"),"curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),"body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),"json_error":m.get("json_error"),"json_shape":m.get("json_shape"),"event_count":m.get("event_count") if ok else None,"event_keys":m.get("event_keys") if ok else [],"safe_events":safe,"safe_projection_sha256":projection_sha,"excluded_fields":["usuarioNome"],"diagnostic_scalars":{} if ok else m.get("diagnostic_scalars"),"source_get_count":1,"retry_performed":False,"redirect_followed":False,"traverse_exposed_links":False,"raw_body_persisted":False,"absence_inference_allowed":False}
