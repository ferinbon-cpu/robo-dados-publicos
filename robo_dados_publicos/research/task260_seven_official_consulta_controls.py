from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any,Mapping
from robo_dados_publicos.research.task259_first_official_consulta_route import Curl
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task260_seven_official_consulta_controls.v1.json";EV=ROOT/"docs/evidence/TASK_260_TASK259_FIRST_CONTROL_CANONICAL_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
 if not x:raise Stop(c)
def load_config(path=CFG):
 c=json.loads(Path(path).read_text());stop(c["schema"]=="TASK260_SEVEN_OFFICIAL_CONSULTA_CONTROLS_V1","CFG")
 stop(len(c["targets"])==7 and len({x["control"] for x in c["targets"]})==7,"TARGETS")
 for t in c["targets"]:
  expected=c["route_template"].format(cnpj="45132495000140",ano=2026,sequencial=t["sequencial"]);stop(t["url"]==expected,"URL")
 stop(c["probe"]["max_remote_get_count"]==7 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"],"BOUNDS");return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text());stop(e["route_operationally_proven_by_task259"] is True,"EV");stop(e["expected_batch_get_count"]==7,"EVCOUNT");return e
def validate(a:Mapping[str,Any]|None,sha,c):
 if not a:return "STOP_TASK260_NOT_AUTHORIZED"
 if not HEX40.fullmatch(sha or ""):return "STOP_TASK260_SHA"
 req={"task":"TASK_260_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,
 "operation":"EXACT_SEVEN_REMAINING_OFFICIAL_CONSULTA_CONTROL_RESOLUTION","target_controls":[t["control"] for t in c["targets"]],"max_remote_get_count":7,
 "attempt_count":1,"authorization_token_index":5,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,
 "follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"raw_body_persistence":False,"prior_authorization_reused":False,
 "drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK260_AUTH" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK260_AUTH_MISMATCH"
def execute(c,e,*,transport,authorization,expected_implementation_sha,offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK260_AUTH":return {"schema":"TASK260_RESULT_V1","status":s,"source_get_count":0}
 p=c["probe"];obs=[];attempts=0
 for t in c["targets"]:
  attempts+=1
  try:
   m=transport.get(t["url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds_per_target"],max_body_bytes=p["max_body_bytes_per_target"])
   exact=m.get("http_code")==200 and (m.get("selected") or {}).get("numeroControlePNCP")==t["control"]
   obs.append({"control":t["control"],"url":t["url"],"outcome":"EXACT_CONTROL_RESOLVED" if exact else "UNRESOLVED_OBSERVATION",
    "http_code":m.get("http_code"),"curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),"body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),
    "json_error":m.get("json_error"),"selected":m.get("selected"),"raw_body_persisted":False})
  except Exception as x:
   obs.append({"control":t["control"],"url":t["url"],"outcome":"TARGET_LOCAL_TRANSPORT_OR_BOUND_FAILURE","error_type":type(x).__name__,"error":str(x)[:200],"raw_body_persisted":False})
 stop(attempts==7,"ATTEMPTS")
 resolved=sum(o["outcome"]=="EXACT_CONTROL_RESOLVED" for o in obs)
 return {"schema":"TASK260_PNCP_SEVEN_CONTROL_RESOLUTION_RESULT_V1","status":"PASS_TASK260_FIXED_SEVEN_ATTEMPTS_COMPLETED",
 "outcome":"ALL_SEVEN_EXACTLY_RESOLVED" if resolved==7 else "PARTIAL_SEVEN_CONTROL_RESOLUTION","resolved_count":resolved,"unresolved_count":7-resolved,
 "source_get_count":7,"observations":obs,"retry_performed":False,"redirect_followed":False,"alternate_url_discovery_performed":False,
 "raw_body_persisted":False,"absence_inference_allowed":False}
