from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task264_jom_pncp_8of8_canonization.v1.json"
EV=ROOT/"docs/evidence/TASK_264_JOM_PNCP_8OF8_CANONICAL_0.8.0.json"
FIX=ROOT/"docs/evidence/fixtures/task264/TASK_264_JOM_PNCP_8OF8_IDENTITY.jsonl"
CONTROL_RE=re.compile(r"^(45132495000140)-1-(\d{6})/(2026)$")
class Stop(RuntimeError):pass
def stop(x,c):
    if not x: raise Stop(c)
def load_config(path=CFG): return json.loads(Path(path).read_text(encoding="utf-8"))
def load_evidence(path=EV): return json.loads(Path(path).read_text(encoding="utf-8"))
def load_rows(path=FIX):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
def validate():
    c=load_config();e=load_evidence();rows=load_rows()
    stop(c["schema"]=="TASK264_JOM_PNCP_8OF8_CANONIZATION_V1","CFG")
    stop(e["status"]=="8_OF_8_EXPLICIT_JOM_PNCP_IDS_CURRENTLY_RESOLVED_EXACTLY","STATUS")
    stop(len(rows)==8 and len({r["control"] for r in rows})==8,"COUNT")
    stop([r["seq"] for r in rows]==[646,639,645,648,655,653,654,69],"ORDER")
    for r in rows:
        m=CONTROL_RE.fullmatch(r["control"]);stop(bool(m),"CONTROL")
        stop(int(m.group(2))==r["seq"],"SEQ")
        stop(r["cnpj"]=="45132495000140" and r["year"]==2026,"ORG")
        stop(r["exact_identity_proven"] is True,"IDENTITY")
        stop(r["jom_admin_process_equals_pncp_processo"] is False,"PROCESS_EQUIV")
        stop(r["descriptive_fields_are_identity"] is False,"SEMANTIC_ID")
    stop(sum(1 for r in rows if r.get("prior_transient_observations"))==1,"TRANSIENT")
    stop(next(r for r in rows if r["seq"]==648)["pncp_proof_task"]==263,"648")
    stop(next(r for r in rows if r["seq"]==645).get("revalidated_task263") is True,"645_REVALIDATED")
    stop(e["adjudication"]["pncp_to_tce_chain_proven"] is False,"TCE")
    return {"status":"PASS_TASK264_8OF8_JOM_PNCP_EXACT_IDENTITY_CANONIZATION","count":8}
