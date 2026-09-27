from __future__ import annotations
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
from typing import Any,Mapping,Protocol
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task259_first_official_consulta_route.v1.json";EV=ROOT/"docs/evidence/TASK_259_PNCP_ROUTE_MIGRATION_CANONICAL_0.8.0.json"
HEX40=re.compile(r"^[0-9a-f]{40}$");REPO="ferinbon-cpu/robo-dados-publicos"
class Stop(RuntimeError):pass
class Transport(Protocol):
 def get(self,url:str,*,connect_timeout:int,max_time:int,max_body_bytes:int)->dict[str,Any]:...
def stop(x,c):
 if not x:raise Stop(c)
def load_config(path=CFG):
 c=json.loads(Path(path).read_text());stop(c["schema"]=="TASK259_FIRST_OFFICIAL_CONSULTA_ROUTE_V1","CFG")
 t=c["target"];stop(c["route_template"].format(cnpj=t["cnpj"],ano=t["ano"],sequencial=t["sequencial"])==t["url"],"ROUTE")
 stop(c["probe"]["max_remote_get_count"]==1 and not c["probe"]["retry"] and not c["probe"]["follow_redirects"],"BOUNDS");return c
def load_evidence(path=EV):
 e=json.loads(Path(path).read_text());stop(e["route_template_proven"] is True,"EV");return e
FIELDS=["numeroControlePNCP","anoCompra","sequencialCompra","numeroCompra","processo","objetoCompra","valorTotalEstimado","valorTotalHomologado","modalidadeNome","situacaoCompraNome","dataPublicacaoPncp","dataAberturaProposta","dataEncerramentoProposta","linkSistemaOrigem"]
def select_fields(o):
 if not isinstance(o,dict):return {}
 r={k:o.get(k) for k in FIELDS if k in o}
 org=o.get("orgaoEntidade")
 if isinstance(org,dict):r["orgaoEntidade"]={k:org.get(k) for k in ("cnpj","razaoSocial","poderId","esferaId") if k in org}
 unidade=o.get("unidadeOrgao")
 if isinstance(unidade,dict):r["unidadeOrgao"]={k:unidade.get(k) for k in ("ufSigla","municipioNome","codigoUnidade","nomeUnidade") if k in unidade}
 return r
def cmd(url,path,*,connect_timeout,max_time,max_body_bytes):
 return ["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0","--connect-timeout",str(connect_timeout),"--max-time",str(max_time),"--max-filesize",str(max_body_bytes),"--output",path,"--header","Accept: application/json","--user-agent","robo-dados-publicos-task259/0.8.0","--write-out","%{json}",url]
class Curl:
 def get(self,url,*,connect_timeout,max_time,max_body_bytes):
  with tempfile.NamedTemporaryFile(prefix="t259_",delete=False) as f:p=Path(f.name)
  try:
   q=subprocess.run(cmd(url,str(p),connect_timeout=connect_timeout,max_time=max_time,max_body_bytes=max_body_bytes),capture_output=True,text=True,timeout=max_time+15,check=False)
   b=p.read_bytes();stop(len(b)<=max_body_bytes,"BODY")
   m={}
   try:m=json.loads((q.stdout or "").strip()) if (q.stdout or "").strip() else {}
   except:pass
   parsed=None;err=None
   try:parsed=json.loads(b.decode())
   except Exception as x:err=type(x).__name__
   return {"requested_url":url,"curl_exit_code":q.returncode,"curl_error":(q.stderr or "").strip()[:240] or None,
   "http_code":int(m.get("http_code") or 0),"content_type":m.get("content_type"),"url_effective":m.get("url_effective"),
   "body_bytes":len(b),"body_sha256":hashlib.sha256(b).hexdigest() if b else None,"json_error":err,
   "top_level_keys":sorted(parsed.keys()) if isinstance(parsed,dict) else [],"selected":select_fields(parsed),
   "remote_get_count":1,"raw_body_persisted":False}
  finally:p.unlink(missing_ok=True)
def validate(a:Mapping[str,Any]|None,sha,c):
 if not a:return "STOP_TASK259_NOT_AUTHORIZED"
 if not HEX40.fullmatch(sha or ""):return "STOP_TASK259_SHA"
 t=c["target"];req={"task":"TASK_259_LIVE_AUTHORIZATION","repository":REPO,"implementation_branch":"main","runtime_branch":c["runtime"]["branch"],"implementation_sha":sha,
 "operation":"EXACT_1_FIRST_CONTROL_OFFICIAL_CONSULTA_ROUTE_RESOLUTION","control":t["control"],"requested_url":t["url"],"max_remote_get_count":1,"attempt_count":1,
 "authorization_token_index":4,"authorization_token_budget":10,"owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,"automatic_retry":False,
 "alternate_url_discovery":False,"raw_body_persistence":False,"prior_authorization_reused":False,"drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,
 "promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False}
 return "PASS_TASK259_AUTH" if all(a.get(k)==v for k,v in req.items()) else "STOP_TASK259_AUTH_MISMATCH"
def execute(c,e,*,transport:Transport,authorization,expected_implementation_sha,offline_test_mode=False):
 if not offline_test_mode:
  s=validate(authorization,expected_implementation_sha,c)
  if s!="PASS_TASK259_AUTH":return {"schema":"TASK259_RESULT_V1","status":s,"source_get_count":0}
 t=c["target"];p=c["probe"];m=transport.get(t["url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds"],max_body_bytes=p["max_body_bytes"])
 stop(m["remote_get_count"]==1 and m["requested_url"]==t["url"],"GET");stop(m["raw_body_persisted"] is False,"RAW")
 if m.get("url_effective"):stop(m["url_effective"]==t["url"],"URL")
 identity=m.get("selected",{}).get("numeroControlePNCP")
 outcome="EXACT_CONTROL_RESOLVED" if m.get("http_code")==200 and identity==t["control"] else "NOT_EXACTLY_RESOLVED"
 return {"schema":"TASK259_PNCP_FIRST_CONTROL_RESOLUTION_RESULT_V1","status":"PASS_TASK259_SINGLE_OFFICIAL_ROUTE_OBSERVATION","outcome":outcome,
 "control":t["control"],"requested_url":t["url"],"http_code":m.get("http_code"),"content_type":m.get("content_type"),"curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),
 "body_bytes":m.get("body_bytes"),"body_sha256":m.get("body_sha256"),"json_error":m.get("json_error"),"top_level_keys":m.get("top_level_keys"),"selected":m.get("selected"),
 "source_get_count":1,"raw_body_persisted":False,"remaining_seven_targets_queried":False,"absence_inference_allowed":False}
