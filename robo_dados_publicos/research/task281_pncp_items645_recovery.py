from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Mapping
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task281_pncp_items645_recovery.v1.json"
EV=ROOT/"docs/evidence/TASK_281_PRELIVE_PNCP_ITEMS645_RECOVERY_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
    if not x: raise Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"));stop(c["schema"]=="TASK281_PNCP_ITEMS645_RECOVERY_CARRIER_V1","CFG")
    p=c["probe"];stop(p["max_remote_get_count"]==1 and not p["retry"] and not p["follow_redirects"] and not p["alternate_url_discovery"],"BOUNDS")
    stop(not p["raw_body_persistence"] and not p["persist_item_content"],"PERSIST")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"));stop(e["live_state"]=="NOT_AUTHORIZED_NOT_EXECUTED","PRELIVE");return e
def request(url,c):
    p=c["probe"]
    with tempfile.NamedTemporaryFile(prefix="task281_",delete=False) as tmp:path=Path(tmp.name)
    try:
        cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(p["connect_timeout_seconds"]),"--max-time",str(p["max_time_seconds"]),"--max-filesize",str(p["max_body_bytes"]),"--output",str(path),"--header","Accept: application/json","--user-agent","robo-dados-publicos-task281/0.8.0","--write-out","%{json}",url]
        q=subprocess.run(cmd,capture_output=True,text=True,timeout=p["max_time_seconds"]+15,check=False);b=path.read_bytes();stop(len(b)<=p["max_body_bytes"],"BODY")
        meta={}
        try:meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
        except Exception:pass
        parsed=None;err=None
        try:parsed=json.loads(b.decode("utf-8"))
        except Exception as exc:err=type(exc).__name__
        shape="LIST" if isinstance(parsed,list) else ("OBJECT" if isinstance(parsed,dict) else "OTHER")
        return {"requested_url":url,"http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,"body_bytes":len(b),"body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_shape":shape,"json_error":err,"item_count":len(parsed) if isinstance(parsed,list) else None,"item_content_persisted":False,"raw_body_persisted":False,"remote_get_count":1}
    finally:path.unlink(missing_ok=True)
def classify(r):
    if r["http_code"]==200 and r["json_shape"]=="LIST":return "PNCP_ITEMS_645_RECOVERED_HTTP200_LIST"
    if r["http_code"] in (502,503,504):return "PNCP_ITEMS_645_STILL_UNAVAILABLE"
    return "PNCP_ITEMS_645_RECOVERY_AMBIGUOUS"
def validate_auth(a:Mapping|None,sha:str,c):
    if not a:return "STOP_TASK281_LIVE_NOT_AUTHORIZED"
    if not HEX40.fullmatch(sha or ""):return "STOP_TASK281_IMPLEMENTATION_SHA"
    req={"task":"TASK_281_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_1_PNCP_ITEMS645_RECOVERY_HEALTH","requested_url":c["target"]["url"],"max_remote_get_count":1,"attempt_count":1,"owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"raw_body_persistence":False,"persist_item_content":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
    return "PASS_TASK281_LIVE_AUTHORIZATION" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK281_AUTHORIZATION_CONTRACT_MISMATCH"
def execute(c,e,*,getter=request,authorization=None,expected_implementation_sha="",offline_test_mode=False):
    if not offline_test_mode:
        s=validate_auth(authorization,expected_implementation_sha,c)
        if s!="PASS_TASK281_LIVE_AUTHORIZATION":return {"schema":"TASK281_RESULT_V1","status":s,"source_get_count":0}
    r=getter(c["target"]["url"],c);stop(r["remote_get_count"]==1 and r["raw_body_persisted"] is False and r["item_content_persisted"] is False,"BOUND")
    if r.get("url_effective"):stop(r["url_effective"]==c["target"]["url"],"URL")
    return {"schema":"TASK281_PNCP_ITEMS645_RECOVERY_RESULT_V1","status":"PASS_TASK281_SINGLE_RECOVERY_HEALTH_OBSERVATION","outcome":classify(r),"control":c["target"]["control"],**r,"retry_performed":False,"absence_inference_allowed":False}
