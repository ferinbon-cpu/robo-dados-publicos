from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task272_seven_history_v26_safe.v1.json"
EV=ROOT/"docs/evidence/TASK_272_PRELIVE_SEVEN_HISTORY_V26_SAFE_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError): pass
def stop(x,c):
    if not x: raise Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"))
    stop(c["schema"]=="TASK272_SEVEN_HISTORY_V26_SAFE_CARRIER_V1","CFG")
    stop(len(c["targets"])==7 and len({x["control"] for x in c["targets"]})==7,"TARGETS")
    stop(c["excluded_projection_fields"]==["usuarioNome"] and "usuarioNome" not in c["safe_projection"],"PRIVACY")
    p=c["probe"];stop(p["max_remote_get_count"]==7 and p["max_gets_per_target"]==1,"GET_BOUND")
    stop(not p["retry"] and not p["follow_redirects"] and not p["alternate_url_discovery"] and not p["pagination"],"NO_EXPANSION")
    stop(not p["raw_body_persistence"] and not p["traverse_exposed_links"],"NO_PERSIST_TRAVERSE")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"));stop(e["live_state"]=="NOT_EXECUTED","PRELIVE");return e
def primitive(v): return v is None or isinstance(v,(str,int,float,bool))
def project(row,fields): return {k:row.get(k) for k in fields if k in row and primitive(row.get(k))}
def identity_ok(row,t):
    if row.get("compraOrgaoCnpj") is not None and str(row["compraOrgaoCnpj"])!=t["cnpj"]: return False
    if row.get("compraAno") is not None and int(row["compraAno"])!=t["ano"]: return False
    if row.get("compraSequencial") is not None and int(row["compraSequencial"])!=t["sequencial"]: return False
    return True
def one_get(t,c):
    p=c["probe"]
    with tempfile.NamedTemporaryFile(prefix="task272_",delete=False) as tmp:path=Path(tmp.name)
    try:
        cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(p["connect_timeout_seconds"]),"--max-time",str(p["max_time_seconds_per_target"]),"--max-filesize",str(p["max_body_bytes_per_target"]),"--output",str(path),"--header","Accept: application/json","--user-agent","robo-dados-publicos-task272/0.8.0","--write-out","%{json}",t["url"]]
        q=subprocess.run(cmd,capture_output=True,text=True,timeout=p["max_time_seconds_per_target"]+15,check=False)
        body=path.read_bytes();stop(len(body)<=p["max_body_bytes_per_target"],"BODY_BOUND")
        meta={}
        try: meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
        except Exception: pass
        parsed=None;err=None
        try: parsed=json.loads(body.decode("utf-8"))
        except Exception as exc: err=type(exc).__name__
        if isinstance(parsed,list):
            rows=[x for x in parsed if isinstance(x,dict)]
            identity_valid=all(identity_ok(x,t) for x in rows)
            selected=[project(x,c["safe_projection"]) for x in rows] if identity_valid else []
            stop(all("usuarioNome" not in x for x in selected),"PRIVACY_LEAK")
            keys=sorted({k for x in rows for k in x.keys()})
            shape="LIST";count=len(parsed)
        else:
            identity_valid=False;selected=[];keys=[];shape="OBJECT" if isinstance(parsed,dict) else "OTHER";count=None
        ok=int(meta.get("http_code") or 0)==200 and shape=="LIST" and identity_valid
        return {"control":t["control"],"sequencial":t["sequencial"],"requested_url":t["url"],"http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,"body_bytes":len(body),"body_sha256":hashlib.sha256(body).hexdigest() if body else None,"json_error":err,"json_shape":shape,"event_count":count if ok else None,"event_keys":keys if ok else [],"identity_valid":identity_valid if shape=="LIST" else None,"safe_events":selected if ok else [],"safe_projection_sha256":hashlib.sha256(json.dumps(selected,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() if ok else None,"resolved":ok,"outcome":"HISTORY_V26_SAFE_HTTP200_LIST" if ok else "HISTORY_V26_SAFE_UNRESOLVED_OBSERVATION","remote_get_count":1,"raw_body_persisted":False}
    finally:path.unlink(missing_ok=True)
def validate_auth(a:Mapping[str,Any]|None,sha:str,c):
    if not a:return "STOP_TASK272_LIVE_NOT_AUTHORIZED"
    if not HEX40.fullmatch(sha or ""):return "STOP_TASK272_IMPLEMENTATION_SHA"
    req={"task":"TASK_272_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_7_REMAINING_PNCP_HISTORY_V26_SAFE_SNAPSHOT","target_controls":[x["control"] for x in c["targets"]],"target_urls":[x["url"] for x in c["targets"]],"max_remote_get_count":7,"max_gets_per_target":1,"attempt_count":1,"owner_authorized":True,"source_network_authorized":True,"authorization_mode":"BOUNDED_STANDING_OWNER_HISTORY_COMPLETION_FRANCHISE","owner_phrase":"Prossiga autorizado até compltar tudo","follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"pagination":False,"raw_body_persistence":False,"traverse_exposed_links":False,"persist_usuario_nome":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
    return "PASS_TASK272_LIVE_AUTHORIZATION" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK272_AUTHORIZATION_CONTRACT_MISMATCH"
def execute(c,e,*,getter=one_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
    if not offline_test_mode:
        s=validate_auth(authorization,expected_implementation_sha,c)
        if s!="PASS_TASK272_LIVE_AUTHORIZATION":return {"schema":"TASK272_RESULT_V1","status":s,"source_get_count":0}
    results=[]
    for t in c["targets"]: results.append(getter(t,c))
    stop(sum(x.get("remote_get_count",0) for x in results)==7,"SOURCE_GET_COUNT")
    resolved=[x for x in results if x["resolved"]];unresolved=[x for x in results if not x["resolved"]]
    outcome="SEVEN_REMAINING_HISTORY_CONTROLS_RESOLVED_SAFE" if len(resolved)==7 else "BOUNDED_MIXED_HISTORY_RESULT_WITH_EXACT_UNRESOLVED_TARGETS"
    return {"schema":"TASK272_SEVEN_HISTORY_V26_SAFE_RESULT_V1","status":"PASS_TASK272_BOUNDED_SEVEN_HISTORY_OBSERVATION","outcome":outcome,"resolved_count":len(resolved),"unresolved_count":len(unresolved),"source_get_count":7,"results":results,"unresolved_controls":[x["control"] for x in unresolved],"retry_performed":False,"redirect_followed":False,"alternate_url_discovery_performed":False,"pagination_performed":False,"traverse_exposed_links":False,"raw_body_persisted":False,"absence_inference_allowed":False}
