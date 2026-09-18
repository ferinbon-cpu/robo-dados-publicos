from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CFG=ROOT/"config/task267_pncp_items_8of8_canonization.v1.json";EV=ROOT/"docs/evidence/TASK_267_PNCP_ITEMS_8OF8_CANONICAL_0.8.0.json"
def load_config(path=CFG):return json.loads(Path(path).read_text())
def load_evidence(path=EV):return json.loads(Path(path).read_text())
def validate():
 c=load_config();e=load_evidence();assert c["schema"]=="TASK267_PNCP_ITEMS_8OF8_CANONIZATION_V1";assert e["status"]=="8_OF_8_PNCP_CONTROLS_HAVE_CURRENT_ITEMS_HTTP200_LIST"
 assert len(e["controls"])==8 and sum(x["item_count"] for x in e["controls"])==40
 assert sum(x["matches_detail_estimated_value"] for x in e["controls"])==7
 m=[x for x in e["controls"] if not x["matches_detail_estimated_value"]];assert len(m)==1 and m[0]["control"].endswith("000653/2026") and m[0]["difference"]==-16921.62
 assert e["diagnostic"]["status"]=="OPEN_DIAGNOSTIC_NO_CAUSE_INFERRED";assert e["authorization"]["tokens_remaining"]==0
 assert e["epistemic_limits"]["pncp_to_tce_chain_proven"] is False and e["epistemic_limits"]["history_queried"] is False
 return {"status":"PASS_TASK267_PNCP_ITEMS_8OF8_CANONIZATION","controls":8,"items":40}
