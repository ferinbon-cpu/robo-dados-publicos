from __future__ import annotations
import json
from pathlib import Path
from typing import Any,Mapping
from robo_dados_publicos.research.task265_pncp_items_route_probe_645 import curl_get
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task266_seven_remaining_pncp_items.v1.json";EV=ROOT/"docs/evidence/TASK_266_TASK265_ITEMS_ROUTE_CANONICAL_0.8.0.json";REPO="ferinbon-cpu/robo-dados-publicos"
def load_config(path=CFG):
 c=json.loads(Path(path).read_text());assert c["schema"]=="TASK266_SEVEN_REMAINING_PNCP_ITEMS_V1";assert len(c["targets"])==7;assert [x["sequencial"] for x in c["targets"]]==[646,639,648,655,653,654,69];assert c["probe"]["max_remote_get_count"]==7 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"];return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text());assert e["route_operationally_proven"] is True and e["expected_get_count"]==7;return e
def validate(a:Mapping[str,Any]|None,sha,c):
 if not a:return "STOP_TASK266_NOT_AUTHORIZED"
 req={"task":"TASK_266_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_SEVEN_REMAINING_PNCP_ITEMS_SNAPSHOT","target_controls":[x["control"] for x in c["targets"]],"max_remote_get_count":7,"attempt_count":1,"authorization_token_index":10,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"raw_body_persistence":False,"prior_authorization_reused":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK266_AUTH" if len(sha)==40 and all(a.get(k)==v for k,v in req.items()) else "STOP_TASK266_AUTH_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK266_AUTH":return {"schema":"TASK266_RESULT_V1","status":s,"source_get_count":0}
 p=c["probe"];obs=[]
 for t in c["targets"]:
  try:
   m=getter(t["url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds_per_target"],max_body_bytes=p["max_body_bytes_per_target"])
   exact=m.get("http_code")==200 and m.get("json_shape")=="LIST"
   obs.append({"control":t["control"],"url":t["url"],"outcome":"ITEMS_HTTP200_LIST" if exact else "ITEMS_UNRESOLVED_OBSERVATION","http_code":m.get("http_code"),"curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),"content_type":m.get("content_type"),"body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),"json_error":m.get("json_error"),"json_shape":m.get("json_shape"),"item_count":m.get("item_count") if exact else None,"selected_items":m.get("selected_items") if exact else [],"diagnostic_scalars":{} if exact else m.get("diagnostic_scalars"),"raw_body_persisted":False})
  except Exception as x:
   obs.append({"control":t["control"],"url":t["url"],"outcome":"ITEMS_TARGET_LOCAL_FAILURE","error_type":type(x).__name__,"error":str(x)[:200],"raw_body_persisted":False})
 ok=sum(x["outcome"]=="ITEMS_HTTP200_LIST" for x in obs)
 return {"schema":"TASK266_PNCP_SEVEN_ITEMS_RESULT_V1","status":"PASS_TASK266_FIXED_SEVEN_ITEMS_ATTEMPTS_COMPLETED","outcome":"ALL_SEVEN_ITEMS_RESOLVED" if ok==7 else "PARTIAL_SEVEN_ITEMS_RESOLUTION","resolved_count":ok,"unresolved_count":7-ok,"source_get_count":7,"observations":obs,"retry_performed":False,"redirect_followed":False,"alternate_url_discovery_performed":False,"raw_body_persisted":False,"absence_inference_allowed":False}
