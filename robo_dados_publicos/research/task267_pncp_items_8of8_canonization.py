from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task267_pncp_items_8of8_canonization.v1.json"
EV=ROOT/"docs/evidence/TASK_267_PNCP_ITEMS_8OF8_CANONICAL_0.8.0.json"
FIX=ROOT/"docs/evidence/fixtures/task267/TASK_267_PNCP_ITEMS_8OF8_SUMMARY.jsonl"
class Task267Stop(RuntimeError): pass
def _stop(x,c):
    if not x: raise Task267Stop(c)
def load_config(path=CFG):
    c=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(c["schema"]=="TASK267_PNCP_ITEMS_8OF8_CANONIZATION_V1","TASK267_CONFIG")
    _stop(c["expected"]=={"controls":8,"item_rows":40,"material_rows":28,"service_rows":12,"all_items_status":"Em andamento"},"TASK267_EXPECTED")
    _stop(c["remote_effects"]["network"] is False,"TASK267_NETWORK")
    return c
def load_evidence(path=EV):
    e=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(e["status"]=="8_OF_8_PNCP_ITEMS_RESOLVED_40_SANITIZED_ITEM_ROWS","TASK267_STATUS")
    return e
def load_rows(path=FIX):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
def validate():
    c=load_config();e=load_evidence();rows=load_rows()
    _stop(len(rows)==8 and len({x["control"] for x in rows})==8,"TASK267_CONTROL_COUNT")
    _stop(sum(x["item_count"] for x in rows)==40,"TASK267_ITEM_COUNT")
    _stop(sum(x["material_count"] for x in rows)==28,"TASK267_MATERIAL_COUNT")
    _stop(sum(x["service_count"] for x in rows)==12,"TASK267_SERVICE_COUNT")
    _stop(all(x["http_code"]==200 for x in rows),"TASK267_HTTP")
    _stop(all(x["all_items_em_andamento"] is True for x in rows),"TASK267_STATUS_ROWS")
    _stop(all(re.fullmatch(r"[0-9a-f]{64}",x["body_sha256"]) for x in rows),"TASK267_BODY_HASH")
    _stop(all(re.fullmatch(r"[0-9a-f]{64}",x["selected_items_sha256"]) for x in rows),"TASK267_SELECTED_HASH")
    _stop(abs(sum(float(x["selected_valor_total_sum"]) for x in rows)-15415927.85)<0.001,"TASK267_DESCRIPTIVE_SUM")
    _stop(e["financial_adjudication"]["selected_valor_total_sum_is_payment"] is False,"TASK267_PAYMENT")
    _stop(e["financial_adjudication"]["pncp_to_tce_chain_proven"] is False,"TASK267_TCE")
    return {"status":"PASS_TASK267_PNCP_ITEMS_8OF8_CANONIZATION","controls":8,"item_rows":40}
