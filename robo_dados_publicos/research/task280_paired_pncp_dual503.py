import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task280_paired_pncp_dual503.v1.json"
EV=ROOT/"docs/evidence/TASK_280_PAIRED_PNCP_DUAL503_CANONICAL_0.8.0.json"
def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def validate():
 c=load(CFG);e=load(EV)
 assert c["schema"]=="TASK280_PAIRED_PNCP_DUAL503_CANONIZATION_V1"
 assert e["status"]==c["status"]
 assert c["health"]["http_code"]==503 and c["target"]["http_code"]==503
 assert c["health"]["body_sha256"]==c["target"]["body_sha256"]
 assert c["adjudication"]["linked_route_isolated_failure_proven"] is False
 assert c["adjudication"]["broader_tested_source_unavailability_observed"] is True
 assert c["adjudication"]["global_pncp_outage_proven"] is False
 assert c["boundaries"]["retry_now"] is False
 return {"status":"PASS_TASK280_PAIRED_PNCP_DUAL503_CANONIZATION"}
