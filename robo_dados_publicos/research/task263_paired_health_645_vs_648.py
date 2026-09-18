from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any,Mapping
from robo_dados_publicos.research.task261_three_500_reobserve import curl_get
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task263_paired_health_645_vs_648.v1.json";EV=ROOT/"docs/evidence/TASK_263_TASK262_648_UNAVAILABLE_CANONICAL_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
 if not x:raise Stop(c)
def load_config(path=CFG):
 c=json.loads(Path(path).read_text());stop(c["schema"]=="TASK263_PAIRED_HEALTH_645_VS_648_V1","CFG")
 stop([t["role"] for t in c["targets"]]==["HEALTH_CONTROL","UNRESOLVED_TARGET"],"ORDER")
 stop([t["control"] for t in c["targets"]]==["45132495000140-1-000645/2026","45132495000140-1-000648/2026"],"TARGETS")
 stop(c["probe"]["max_remote_get_count"]==2 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"],"BOUNDS");return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text());stop(e["adjudication"]["seven_of_eight_exact"] is True,"EV")
 stop(e["adjudication"]["648_absence_proven"] is False,"ABS");return e
def validate(a:Mapping[str,Any]|None,sha,c):
 if not a:return "STOP_TASK263_NOT_AUTHORIZED"
 if not HEX40.fullmatch(sha or ""):return "STOP_TASK263_SHA"
 req={"task":"TASK_263_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,
 "operation":"PAIRED_PNCP_HEALTH_645_VS_TARGET_648","target_controls":[t["control"] for t in c["targets"]],"max_remote_get_count":2,"attempt_count":1,
 "authorization_token_index":8,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,
 "alternate_url_discovery":False,"raw_body_persistence":False,"prior_authorization_reused":False,"drive_write_authorized":False,"publication_authorized":False,
 "serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK263_AUTH" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK263_AUTH_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK263_AUTH":return {"schema":"TASK263_RESULT_V1","status":s,"source_get_count":0}
 p=c["probe"];obs=[]
 for t in c["targets"]:
  try:
   m=getter(t["url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds_per_target"],max_body_bytes=p["max_body_bytes_per_target"])
   if m.get("url_effective"):stop(m["url_effective"]==t["url"],"URL")
   exact=m.get("http_code")==200 and (m.get("selected") or {}).get("numeroControlePNCP")==t["control"]
   obs.append({"role":t["role"],"control":t["control"],"url":t["url"],"exact":exact,"http_code":m.get("http_code"),"curl_exit_code":m.get("curl_exit_code"),
    "curl_error":m.get("curl_error"),"content_type":m.get("content_type"),"body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),
    "json_error":m.get("json_error"),"selected":m.get("selected") if exact else {},"diagnostic_scalars":{} if exact else m.get("diagnostic_scalars"),"raw_body_persisted":False})
  except Exception as x:
   obs.append({"role":t["role"],"control":t["control"],"url":t["url"],"exact":False,"error_type":type(x).__name__,"error":str(x)[:200],"raw_body_persisted":False})
 stop(len(obs)==2,"COUNT");h,t=obs
 if t.get("exact"):outcome="TARGET_648_EXACTLY_RESOLVED"
 elif h.get("exact"):outcome="HEALTH_CONTROL_OK_TARGET_648_UNRESOLVED"
 else:outcome="SERVICE_HEALTH_UNRESOLVED_AND_TARGET_648_UNRESOLVED"
 return {"schema":"TASK263_PNCP_PAIRED_HEALTH_RESULT_V1","status":"PASS_TASK263_PAIRED_OBSERVATION_COMPLETED","outcome":outcome,
  "health_control_exact":bool(h.get("exact")),"target_648_exact":bool(t.get("exact")),"source_get_count":2,"observations":obs,
  "retry_performed":False,"raw_body_persisted":False,"absence_inference_allowed":False}
