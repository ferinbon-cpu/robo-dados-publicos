import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task278_linked_contract_runtime_drift.v1.json"
EV=ROOT/"docs/evidence/TASK_278_LINKED_CONTRACT_RUNTIME_DRIFT_CANONICAL_0.8.0.json"
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def validate():
 c=load(CFG);e=load(EV)
 assert c["schema"]=="TASK278_LINKED_CONTRACT_RUNTIME_DRIFT_CANONIZATION_V1"
 assert e["status"]==c["status"]
 assert [x["http_code"] for x in c["observations"]][-2:]==[404,503]
 assert e["adjudication"]["http404_promoted_to_absence"] is False
 assert e["adjudication"]["source_or_backend_variability_observed"] is True
 assert all(v is False for v in [c["boundaries"]["contract_proven"],c["boundaries"]["payment_proven"],c["boundaries"]["pncp_to_tce_proven"]])
 return {"status":"PASS_TASK278_LINKED_CONTRACT_RUNTIME_DRIFT_CANONIZATION"}
