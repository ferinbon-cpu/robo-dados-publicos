from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
from robo_dados_publicos.research.task259_first_official_consulta_route import select_fields
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task261_three_500_reobserve.v1.json";EV=ROOT/"docs/evidence/TASK_261_TASK260_PARTIAL_CANONICAL_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
 if not x: raise Stop(c)
def load_config(path=CFG):
 c=json.loads(Path(path).read_text());stop(c["schema"]=="TASK261_THREE_500_REOBSERVE_V1","CFG")
 stop([t["control"] for t in c["targets"]]==["45132495000140-1-000639/2026","45132495000140-1-000648/2026","45132495000140-1-000654/2026"],"TARGETS")
 stop(c["probe"]["max_remote_get_count"]==3 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"],"BOUNDS");return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text());stop(e["task260"]["resolved_count"]==4 and e["task260"]["unresolved_count"]==3,"EV");stop(e["adjudication"]["three_absent_proven"] is False,"ABS");return e
def scalar_projection(o):
 if not isinstance(o,dict):return {}
 r={}
 for k,v in o.items():
  if v is None or isinstance(v,(bool,int,float)):r[str(k)]=v
  elif isinstance(v,str):r[str(k)]=v[:400]
 return r
def curl_get(url,*,connect_timeout,max_time,max_body_bytes):
 with tempfile.NamedTemporaryFile(prefix="t261_",delete=False) as f:p=Path(f.name)
 try:
  cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(connect_timeout),"--max-time",str(max_time),"--max-filesize",str(max_body_bytes),"--output",str(p),"--header","Accept: application/json","--user-agent","robo-dados-publicos-task261/0.8.0","--write-out","%{json}",url]
  q=subprocess.run(cmd,capture_output=True,text=True,timeout=max_time+15,check=False);b=p.read_bytes();stop(len(b)<=max_body_bytes,"BODY")
  meta={};parsed=None;err=None
  try:meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
  except Exception:pass
  try:parsed=json.loads(b.decode())
  except Exception as x:err=type(x).__name__
  return {"requested_url":url,"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,
   "http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),
   "body_bytes":len(b),"body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_error":err,
   "top_level_keys":sorted(parsed.keys()) if isinstance(parsed,dict) else [],"selected":select_fields(parsed),"diagnostic_scalars":scalar_projection(parsed),
   "raw_body_persisted":False}
 finally:p.unlink(missing_ok=True)
def validate(a:Mapping[str,Any]|None,sha,c):
 if not a:return "STOP_TASK261_NOT_AUTHORIZED"
 if not HEX40.fullmatch(sha or ""):return "STOP_TASK261_SHA"
 req={"task":"TASK_261_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,
 "operation":"EXACT_THREE_PNCP_OFFICIAL_ROUTE_REOBSERVATION","target_controls":[t["control"] for t in c["targets"]],"max_remote_get_count":3,"attempt_count":1,
 "authorization_token_index":6,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,
 "alternate_url_discovery":False,"raw_body_persistence":False,"prior_authorization_reused":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,
 "promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK261_AUTH" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK261_AUTH_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK261_AUTH":return {"schema":"TASK261_RESULT_V1","status":s,"source_get_count":0}
 p=c["probe"];obs=[]
 for t in c["targets"]:
  try:
   m=getter(t["url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds_per_target"],max_body_bytes=p["max_body_bytes_per_target"])
   if m.get("url_effective"):stop(m["url_effective"]==t["url"],"URL")
   exact=m.get("http_code")==200 and (m.get("selected") or {}).get("numeroControlePNCP")==t["control"]
   obs.append({"control":t["control"],"url":t["url"],"outcome":"EXACT_CONTROL_RESOLVED" if exact else "UNRESOLVED_REOBSERVATION",
    "http_code":m.get("http_code"),"curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),"content_type":m.get("content_type"),
    "body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),"json_error":m.get("json_error"),"top_level_keys":m.get("top_level_keys"),
    "selected":m.get("selected") if exact else {},"diagnostic_scalars":{} if exact else m.get("diagnostic_scalars"),"raw_body_persisted":False})
  except Exception as x:
   obs.append({"control":t["control"],"url":t["url"],"outcome":"TARGET_LOCAL_TRANSPORT_OR_BOUND_FAILURE","error_type":type(x).__name__,"error":str(x)[:200],"raw_body_persisted":False})
 resolved=sum(o["outcome"]=="EXACT_CONTROL_RESOLVED" for o in obs);stop(len(obs)==3,"COUNT")
 return {"schema":"TASK261_PNCP_THREE_REOBSERVATION_RESULT_V1","status":"PASS_TASK261_FIXED_THREE_REOBSERVATIONS_COMPLETED",
  "outcome":"ALL_THREE_EXACTLY_RESOLVED" if resolved==3 else "PARTIAL_OR_UNRESOLVED_THREE_REOBSERVATIONS","resolved_count":resolved,"unresolved_count":3-resolved,
  "source_get_count":3,"observations":obs,"retry_performed":False,"raw_body_persisted":False,"absence_inference_allowed":False}
