from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping
from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import ITEM_ALLOW
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task265_pncp_items_route_probe_645.v1.json";EV=ROOT/"docs/evidence/TASK_265_PRELIVE_ITEMS_ROUTE_645_0.8.0.json"
REPO="ferinbon-cpu/robo-dados-publicos";HEX40=re.compile(r"^[0-9a-f]{40}$")
class Stop(RuntimeError):pass
def stop(x,c):
 if not x:raise Stop(c)
def load_config(path=CFG):
 c=json.loads(Path(path).read_text());stop(c["schema"]=="TASK265_PNCP_ITEMS_ROUTE_PROBE_645_V1","CFG");stop(c["target"]["control"]=="45132495000140-1-000645/2026","CTL");stop(c["probe"]["max_remote_get_count"]==1 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"],"BOUND");return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text());stop(e["task264_status"]=="8_OF_8_EXPLICIT_JOM_PNCP_IDS_CURRENTLY_RESOLVED_EXACTLY","EV");stop(e["adjudication"]["silent_detail_route_migration_applied_to_items"] is False,"MIGRATION");return e
def scalars(x):
 if not isinstance(x,dict):return {}
 return {str(k):(v[:500] if isinstance(v,str) else v) for k,v in x.items() if v is None or isinstance(v,(str,int,float,bool))}
def selected_item(x):
 return {k:x.get(k) for k in sorted(ITEM_ALLOW) if k in x and (x.get(k) is None or isinstance(x.get(k),(str,int,float,bool)))}
def curl_get(url,*,connect_timeout,max_time,max_body_bytes):
 with tempfile.NamedTemporaryFile(prefix="t265_",delete=False) as f:p=Path(f.name)
 try:
  cmd=["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(connect_timeout),"--max-time",str(max_time),"--max-filesize",str(max_body_bytes),"--output",str(p),"--header","Accept: application/json","--user-agent","robo-dados-publicos-task265/0.8.0","--write-out","%{json}",url]
  q=subprocess.run(cmd,capture_output=True,text=True,timeout=max_time+15,check=False);b=p.read_bytes();stop(len(b)<=max_body_bytes,"BODY")
  meta={};parsed=None;err=None
  try:meta=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
  except Exception:pass
  try:parsed=json.loads(b.decode())
  except Exception as x:err=type(x).__name__
  islist=isinstance(parsed,list);items=[selected_item(x) for x in parsed if isinstance(x,dict)] if islist else []
  return {"requested_url":url,"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,"http_code":int(meta.get("http_code") or 0),"content_type":meta.get("content_type"),"url_effective":meta.get("url_effective"),"body_bytes":len(b),"body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_error":err,"json_shape":"LIST" if islist else ("OBJECT" if isinstance(parsed,dict) else "OTHER"),"item_count":len(parsed) if islist else None,"selected_items":items,"diagnostic_scalars":scalars(parsed),"remote_get_count":1,"raw_body_persisted":False}
 finally:p.unlink(missing_ok=True)
def validate(a:Mapping[str,Any]|None,sha,c):
 if not a:return "STOP_TASK265_NOT_AUTHORIZED"
 if not HEX40.fullmatch(sha or ""):return "STOP_TASK265_SHA"
 t=c["target"];req={"task":"TASK_265_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,"operation":"EXACT_1_DOCUMENTED_PNCP_ITEMS_ROUTE_PROBE_645","control":t["control"],"requested_url":t["requested_url"],"max_remote_get_count":1,"attempt_count":1,"authorization_token_index":9,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,"alternate_url_discovery":False,"raw_body_persistence":False,"prior_authorization_reused":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,"promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK265_AUTH" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK265_AUTH_MISMATCH"
def execute(c,e,*,getter=curl_get,authorization=None,expected_implementation_sha="",offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK265_AUTH":return {"schema":"TASK265_RESULT_V1","status":s,"source_get_count":0}
 t=c["target"];p=c["probe"];m=getter(t["requested_url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds"],max_body_bytes=p["max_body_bytes"])
 stop(m["remote_get_count"]==1 and m["requested_url"]==t["requested_url"],"GET");stop(m["raw_body_persisted"] is False,"RAW")
 if m.get("url_effective"):stop(m["url_effective"]==t["requested_url"],"URL")
 ok=m["http_code"]==200 and m["json_shape"]=="LIST"
 outcome="DOCUMENTED_ITEMS_ROUTE_HTTP200_LIST" if ok else ("DOCUMENTED_ITEMS_ROUTE_MIGRATION_OR_ERROR_JSON" if m["json_shape"]=="OBJECT" else "DOCUMENTED_ITEMS_ROUTE_NON_LIST_RESPONSE")
 return {"schema":"TASK265_PNCP_ITEMS_ROUTE_PROBE_RESULT_V1","status":"PASS_TASK265_SINGLE_ITEMS_ROUTE_OBSERVATION","outcome":outcome,"control":t["control"],"requested_url":t["requested_url"],"http_code":m["http_code"],"content_type":m.get("content_type"),"curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),"body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),"json_error":m.get("json_error"),"json_shape":m.get("json_shape"),"item_count":m.get("item_count"),"selected_items":m.get("selected_items") if ok else [],"diagnostic_scalars":{} if ok else m.get("diagnostic_scalars"),"source_get_count":1,"retry_performed":False,"redirect_followed":False,"raw_body_persisted":False,"absence_inference_allowed":False}
