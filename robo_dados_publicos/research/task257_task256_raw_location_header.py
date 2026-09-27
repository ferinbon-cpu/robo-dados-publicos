from __future__ import annotations
import json, re, subprocess, tempfile
from pathlib import Path
from typing import Any, Mapping, Protocol

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_CONFIG=ROOT/"config/task257_task256_raw_location_header.v1.json"
DEFAULT_EVIDENCE=ROOT/"docs/evidence/TASK_257_TASK256_HTTP301_CANONICAL_0.8.0.json"
EXPECTED_REPOSITORY="ferinbon-cpu/robo-dados-publicos"
HEX40_RE=re.compile(r"^[0-9a-f]{40}$")

class Task257Stop(RuntimeError): pass
class HeaderTransport(Protocol):
    def get(self,url:str,*,connect_timeout:int,max_time:int)->dict[str,Any]: ...

def _stop(ok:bool,code:str)->None:
    if not ok: raise Task257Stop(code)

def load_config(path=DEFAULT_CONFIG):
    c=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(c.get("schema")=="TASK257_TASK256_RAW_LOCATION_HEADER_V1","TASK257_CONFIG_SCHEMA")
    _stop(c.get("issue")==847,"TASK257_ISSUE")
    _stop(c.get("base_main_sha")=="43a7325883597b19a2988d9a62f9cf4f97dfd287","TASK257_BASE")
    s=c["source_task256"]
    _stop(s["run_id"]==35298949213 and s["http_code"]==301,"TASK257_SOURCE")
    _stop(s["result_sha256"]=="4687efcfa59911f3b77a916901842a31315b279aa2040c592f1dc3e9fb4c394e","TASK257_SOURCE_SHA")
    p=c["probe"]
    _stop(p["max_remote_get_count"]==1 and p["retry"] is False and p["follow_redirects"] is False,"TASK257_BOUNDS")
    _stop(p["response_body_persistence"] is False and p["raw_header_persistence"] is False,"TASK257_PERSISTENCE")
    _stop(c["authorization"]["authorization_token_index"]==2,"TASK257_TOKEN")
    return c

def load_evidence(path=DEFAULT_EVIDENCE):
    e=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(e.get("schema")=="TASK257_TASK256_HTTP301_CANONICAL_V1","TASK257_EVIDENCE_SCHEMA")
    _stop(e["task256"]["http_code"]==301,"TASK257_EVIDENCE_HTTP")
    _stop(e["adjudication"]["redirect_destination_proven"] is False,"TASK257_EVIDENCE_DEST")
    return e

def build_curl_command(url:str,header_path:str,*,connect_timeout:int,max_time:int)->list[str]:
    return ["curl","--silent","--show-error","--request","GET","--retry","0","--max-redirs","0",
            "--connect-timeout",str(connect_timeout),"--max-time",str(max_time),
            "--dump-header",header_path,"--output","/dev/null",
            "--header","Accept: application/json","--user-agent","robo-dados-publicos-task257/0.8.0",
            "--write-out","%{json}",url]

def parse_location_headers(text:str)->list[str]:
    vals=[]
    for line in text.splitlines():
        if ":" not in line: continue
        k,v=line.split(":",1)
        if k.strip().lower()=="location":
            vals.append(v.strip())
    return vals

class CurlHeaderTransport:
    def get(self,url:str,*,connect_timeout:int,max_time:int)->dict[str,Any]:
        with tempfile.NamedTemporaryFile(prefix="task257_",suffix=".headers",delete=False) as tmp:
            hp=Path(tmp.name)
        try:
            proc=subprocess.run(build_curl_command(url,str(hp),connect_timeout=connect_timeout,max_time=max_time),
                                capture_output=True,text=True,timeout=max_time+15,check=False)
            raw_headers=hp.read_text(encoding="iso-8859-1",errors="replace") if hp.exists() else ""
            locs=parse_location_headers(raw_headers)
            meta={}
            if (proc.stdout or "").strip():
                try:
                    x=json.loads(proc.stdout)
                    if isinstance(x,dict): meta=x
                except json.JSONDecodeError: pass
            return {
                "requested_url":url,"curl_exit_code":int(proc.returncode),
                "curl_error":(proc.stderr or "").strip()[:240] or None,
                "http_code":int(meta.get("http_code") or 0),
                "url_effective":meta.get("url_effective") or None,
                "location_headers":locs,
                "location_header_count":len(locs),
                "remote_ip":meta.get("remote_ip") or None,
                "remote_port":meta.get("remote_port"),
                "time_namelookup":meta.get("time_namelookup"),
                "time_connect":meta.get("time_connect"),
                "time_appconnect":meta.get("time_appconnect"),
                "time_starttransfer":meta.get("time_starttransfer"),
                "time_total":meta.get("time_total"),
                "remote_get_count":1,"response_body_persisted":False,"raw_headers_persisted":False,
            }
        finally:
            try: hp.unlink(missing_ok=True)
            except Exception: pass

def validate_live_authorization(a:Mapping[str,Any]|None,*,expected_implementation_sha:str,config:Mapping[str,Any]):
    if not a: return {"status":"STOP_TASK257_LIVE_NOT_AUTHORIZED"}
    if not HEX40_RE.fullmatch(expected_implementation_sha or ""): return {"status":"STOP_TASK257_SHA"}
    p=config["probe"]
    req={
      "task":"TASK_257_LIVE_AUTHORIZATION","repository":EXPECTED_REPOSITORY,
      "implementation_branch":"main","runtime_branch":config["runtime"]["branch"],
      "implementation_sha":expected_implementation_sha,
      "operation":"EXACT_1_TASK256_FIRST_TARGET_NOFOLLOW_RAW_LOCATION_HEADER_CAPTURE",
      "control":p["control"],"requested_url":p["requested_url"],"max_remote_get_count":1,
      "attempt_count":1,"authorization_token_index":2,"authorization_token_budget":10,
      "owner_authorized":True,"source_network_authorized":True,"follow_redirects":False,
      "automatic_retry":False,"alternate_url_discovery":False,"response_body_persistence":False,
      "raw_header_persistence":False,"prior_authorization_reused":False,
      "drive_write_authorized":False,"publication_authorized":False,"serving_authorized":False,
      "promotion_authorized":False,"recurrence_authorized":False,"schedule_authorized":False,"consumed":False
    }
    if any(a.get(k)!=v for k,v in req.items()): return {"status":"STOP_TASK257_AUTHORIZATION_CONTRACT_MISMATCH"}
    return {"status":"PASS_TASK257_LIVE_AUTHORIZATION"}

def execute_probe(config,evidence,*,transport:HeaderTransport,authorization,expected_implementation_sha:str,offline_test_mode=False):
    _stop(evidence.get("schema")=="TASK257_TASK256_HTTP301_CANONICAL_V1","TASK257_EXEC_EVIDENCE")
    if not offline_test_mode:
        a=validate_live_authorization(authorization,expected_implementation_sha=expected_implementation_sha,config=config)
        if a["status"]!="PASS_TASK257_LIVE_AUTHORIZATION":
            return {"schema":"TASK257_PNCP_RAW_LOCATION_HEADER_RESULT_V1","status":a["status"],"source_get_count":0}
    p=config["probe"]
    m=transport.get(p["requested_url"],connect_timeout=p["connect_timeout_seconds"],max_time=p["max_time_seconds"])
    _stop(m["remote_get_count"]==1,"TASK257_GET_COUNT")
    _stop(m["requested_url"]==p["requested_url"],"TASK257_URL_DRIFT")
    _stop(m["response_body_persisted"] is False and m["raw_headers_persisted"] is False,"TASK257_PERSISTED_RAW")
    eff=m.get("url_effective")
    if eff: _stop(eff==p["requested_url"],"TASK257_EFFECTIVE_URL_DRIFT")
    locs=list(m.get("location_headers") or [])
    if len(locs)>1: outcome="MULTIPLE_LOCATION_HEADERS_OBSERVED"
    elif len(locs)==1: outcome="SINGLE_LOCATION_HEADER_CAPTURED"
    elif 300<=int(m.get("http_code") or 0)<400: outcome="REDIRECT_STATUS_WITHOUT_LOCATION_HEADER"
    else: outcome="NO_LOCATION_HEADER_NON_REDIRECT_STATUS"
    return {
      "schema":"TASK257_PNCP_RAW_LOCATION_HEADER_RESULT_V1",
      "status":"PASS_TASK257_SINGLE_NOFOLLOW_HEADER_CAPTURE_OBSERVED",
      "outcome":outcome,"control":p["control"],"requested_url":p["requested_url"],
      "curl_exit_code":m.get("curl_exit_code"),"curl_error":m.get("curl_error"),
      "http_code":int(m.get("http_code") or 0),"url_effective":eff,
      "location_header_count":len(locs),"location":locs[0] if len(locs)==1 else None,
      "remote_ip":m.get("remote_ip"),"remote_port":m.get("remote_port"),
      "time_namelookup":m.get("time_namelookup"),"time_connect":m.get("time_connect"),
      "time_appconnect":m.get("time_appconnect"),"time_starttransfer":m.get("time_starttransfer"),
      "time_total":m.get("time_total"),"source_get_count":1,
      "redirect_followed":False,"retry_performed":False,"remaining_seven_targets_queried":False,
      "response_body_persisted":False,"raw_headers_persisted":False,
      "absence_inference_allowed":False,"remaining_target_url_inference_allowed":False
    }
