from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any,Mapping
from robo_dados_publicos.research.task261_three_500_reobserve import curl_get
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task262_final_648_resolution.v1.json";EV=ROOT/"docs/evidence/TASK_262_TASK261_TRANSIENT_JDBC_CANONICAL_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
 if not x:raise Stop(c)
def load_config(path=CFG):
 c=json.loads(Path(path).read_text());stop(c["schema"]=="TASK262_FINAL_648_RESOLUTION_V1","CFG")
 stop(c["target"]["control"]=="45132495000140-1-000648/2026","CTL")
 stop(c["probe"]["max_remote_get_count"]==1 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"],"BOUNDS");return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text());stop(e["adjudication"]["transient_backend_failure_proven_for_task261_observation"] is True,"EV")
 stop(e["adjudication"]["record_absence_proven"] is False,"ABS");return e
def validate(a:Mapping[str,Any]|None,sha,c):
 if not a:return "STOP_TASK262_NOT_AUTHORIZED"
 if not HEX40.fullmatch(sha or ""):return "STOP_TASK262_SHA"
 t=c["target"];req={"task":"TASK_262_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],
 "implementation_sha":sha,"operation":"EXACT_1_PNCP_FINAL_CONTROL_648_RESOLUTION","control":t["control"],"requested_url":t["url"],"max_remote_get_count":1,
 "attempt_count":1,"authorization_token_index":7,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,
 "follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"raw_body_persistence":False,"prior_authorization_reused":False,
 "drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK262_AUTH" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK262_AUTH_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK262_AUTH":return {"schema":"TASK262_RESULT_V1","status":s,"source_get_count":0}
 t=c["target"];p=c["probe"];m=getter(t["url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds"],max_body_bytes=p["max_body_bytes"])
 if m.get("url_effective"):stop(m["url_effective"]==t["url"],"URL")
 exact=m.get("http_code")==200 and (m.get("selected") or {}).get("numeroControlePNCP")==t["control"]
 return {"schema":"TASK262_PNCP_FINAL_648_RESULT_V1","status":"PASS_TASK262_SINGLE_FINAL_CONTROL_OBSERVATION",
  "outcome":"EXACT_CONTROL_RESOLVED" if exact else "FINAL_CONTROL_STILL_UNRESOLVED","control":t["control"],"requested_url":t["url"],
  "http_code":m.get("http_code"),"curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),"content_type":m.get("content_type"),
  "body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),"json_error":m.get("json_error"),"top_level_keys":m.get("top_level_keys"),
  "selected":m.get("selected") if exact else {},"diagnostic_scalars":{} if exact else m.get("diagnostic_scalars"),
  "source_get_count":1,"retry_performed":False,"raw_body_persisted":False,"absence_inference_allowed":False}
