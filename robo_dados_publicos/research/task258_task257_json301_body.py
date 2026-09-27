from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping,Protocol
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task258_task257_json301_body.v1.json"
EV=ROOT/"docs/evidence/TASK_258_TASK257_HTTP301_NO_LOCATION_CANONICAL_0.8.0.json"
HEX40=re.compile(r"^[0-9a-f]{40}$"); REPO="ferinbon-cpu/robo-dados-publicos"
class Stop(RuntimeError): pass
class Transport(Protocol):
 def get(self,url:str,*,connect_timeout:int,max_time:int,max_body_bytes:int)->dict[str,Any]: ...
def stop(x,c):
 if not x: raise Stop(c)
def load_config(path=CFG):
 c=json.loads(Path(path).read_text())
 stop(c["schema"]=="TASK258_TASK257_JSON301_BODY_V1","CFG")
 stop(c["source_task257"]["http_code"]==301 and c["source_task257"]["location_header_count"]==0,"SRC")
 stop(c["probe"]["max_remote_get_count"]==1 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"],"BOUNDS")
 stop(c["authorization"]["authorization_token_index"]==3,"TOKEN")
 return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text()); stop(e["schema"]=="TASK258_TASK257_HTTP301_NO_LOCATION_CANONICAL_V1","EV")
 stop(e["adjudication"]["json_body_semantics_unobserved"] is True,"EVSTATE"); return e
def project(obj,depth=0):
 if depth>3:return "<depth-limit>"
 if obj is None or isinstance(obj,(bool,int,float)): return obj
 if isinstance(obj,str): return obj[:512]
 if isinstance(obj,list): return [project(x,depth+1) for x in obj[:20]]
 if isinstance(obj,dict): return {str(k)[:100]:project(v,depth+1) for k,v in list(obj.items())[:50]}
 return str(obj)[:200]
def command(url,path,*,connect_timeout,max_time,max_body_bytes):
 return ["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0",
 "--connect-timeout",str(connect_timeout),"--max-time",str(max_time),"--max-filesize",str(max_body_bytes),
 "--output",path,"--header","Accept: application/json","--user-agent","robo-dados-publicos-task258/0.8.0",
 "--write-out","%{json}",url]
class CurlBodyTransport:
 def get(self,url,*,connect_timeout,max_time,max_body_bytes):
  with tempfile.NamedTemporaryFile(prefix="t258_",suffix=".body",delete=False) as f:p=Path(f.name)
  try:
   q=subprocess.run(command(url,str(p),connect_timeout=connect_timeout,max_time=max_time,max_body_bytes=max_body_bytes),
    capture_output=True,text=True,timeout=max_time+15,check=False)
   b=p.read_bytes() if p.exists() else b""; stop(len(b)<=max_body_bytes,"BODY_TOO_LARGE")
   meta={}
   try: meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
   except json.JSONDecodeError: meta={}
   parsed=None; err=None
   try: parsed=json.loads(b.decode("utf-8"))
   except Exception as x: err=type(x).__name__
   return {"requested_url":url,"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,
    "http_code":int(meta.get("http_code") or 0),"url_effective":meta.get("url_effective") or None,
    "content_type":meta.get("content_type") or None,"body_bytes":len(b),
    "body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_parse_error":err,
    "json_projection":project(parsed) if err is None else None,"remote_get_count":1,"raw_body_persisted":False}
  finally:
   p.unlink(missing_ok=True)
def validate(a:Mapping[str,Any]|None,sha:str,c):
 if not a:return "STOP_TASK258_NOT_AUTHORIZED"
 if not HEX40.fullmatch(sha or ""):return "STOP_TASK258_SHA"
 p=c["probe"]; req={"task":"TASK_258_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main",
 "runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,
 "operation":"EXACT_1_TASK257_FIRST_TARGET_BOUNDED_JSON_301_BODY_INSPECTION",
 "control":p["control"],"requested_url":p["requested_url"],"max_remote_get_count":1,"attempt_count":1,
 "authorization_token_index":3,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,
 "follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"raw_body_persistence":False,
 "prior_authorization_reused":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,
 "promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK258_AUTH" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK258_AUTH_MISMATCH"
def execute(c,e,*,transport:Transport,authorization,expected_implementation_sha,offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK258_AUTH":return {"schema":"TASK258_RESULT_V1","status":s,"source_get_count":0}
 p=c["probe"];m=transport.get(p["requested_url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds"],max_body_bytes=p["max_body_bytes"])
 stop(m["remote_get_count"]==1 and m["requested_url"]==p["requested_url"],"GET")
 stop(m["raw_body_persisted"] is False,"RAW")
 if m.get("url_effective"):stop(m["url_effective"]==p["requested_url"],"URL_DRIFT")
 outcome="JSON_BODY_PARSED" if m.get("json_parse_error") is None else "BODY_NOT_JSON"
 return {"schema":"TASK258_PNCP_JSON301_BODY_RESULT_V1","status":"PASS_TASK258_SINGLE_BOUNDED_BODY_INSPECTION",
 "outcome":outcome,"control":p["control"],"requested_url":p["requested_url"],"curl_exit_code":m.get("curl_exit_code"),
 "curl_error":m.get("curl_error"),"http_code":m.get("http_code"),"content_type":m.get("content_type"),
 "body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),"json_parse_error":m.get("json_parse_error"),
 "json_projection":m.get("json_projection"),"source_get_count":1,"raw_body_persisted":False,
 "redirect_followed":False,"retry_performed":False,"remaining_seven_targets_queried":False,"absence_inference_allowed":False}
