from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task269_pncp_history_schema_drift.v1.json"
EV=ROOT/"docs/evidence/TASK_269_PNCP_HISTORY_SCHEMA_DRIFT_CANONICAL_0.8.0.json"
FIX=ROOT/"docs/evidence/fixtures/task269/TASK_269_HISTORY_SCHEMA_DRIFT.jsonl"
class Stop(RuntimeError): pass
def stop(x,c):
    if not x: raise Stop(c)
def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def validate():
    c=load(CFG);e=load(EV);f=load(FIX)
    stop(c["schema"]=="TASK269_PNCP_HISTORY_SCHEMA_DRIFT_CANONIZATION_V1","CFG")
    stop(e["status"]==c["status"],"STATUS")
    stop(c["source_task268"]["http_code"]==200 and c["source_task268"]["event_count"]==3,"OBS")
    stop(len(c["observed_keys"])==16 and len(set(c["observed_keys"]))==16,"KEYS")
    stop(c["observed_intersection"]==["justificativa"],"INTERSECTION")
    stop(e["schema_comparison"]["schema_drift_confirmed"] is True,"DRIFT")
    stop(e["observation"]["selected_history_actual_semantics_sufficient"] is False,"SEMANTICS")
    stop(c["excluded_fields"]==[{"field":"usuarioNome","reason":"MINIMIZE_PERSONAL_DATA_RETENTION"}],"PRIVACY")
    stop("usuarioNome" not in c["proposed_safe_v26_projection"],"PII")
    stop(set(c["proposed_safe_v26_projection"])==set(c["observed_keys"])-{"usuarioNome"},"SAFE")
    stop(e["adjudication"]["second_source_read_authorized"] is False,"NETWORK")
    stop(re.fullmatch(r"[0-9a-f]{64}",f["body_sha256"]) is not None,"HASH")
    return {"status":"PASS_TASK269_HISTORY_SCHEMA_DRIFT_CANONIZATION","event_count":3,"observed_key_count":16}
