import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task271_history_645_semantic_canonization.v1.json"
EV=ROOT/"docs/evidence/TASK_271_HISTORY_645_SEMANTIC_CANONICAL_0.8.0.json"
FIX=ROOT/"docs/evidence/fixtures/task271/TASK_271_HISTORY_645_SAFE_EVENTS.jsonl"
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def rows(): return [json.loads(x) for x in FIX.read_text(encoding="utf-8").splitlines() if x.strip()]
def validate():
 c=load(CFG);e=load(EV);r=rows()
 assert c["schema"]=="TASK271_HISTORY_645_SEMANTIC_CANONIZATION_V1"
 assert e["status"]==c["status"] and len(r)==3
 assert sum(x["categoriaLogManutencaoNome"]=="Contratação" for x in r)==1
 assert sum(x["categoriaLogManutencaoNome"]=="Documento de Contratação" for x in r)==2
 assert all(x["tipoLogManutencaoNome"]=="Inclusão" for x in r)
 assert sum(x.get("itemResultadoNumero") is not None or x.get("itemResultadoSequencial") is not None for x in r)==0
 assert sum(x.get("itemNumero") is not None for x in r)==0
 assert all("usuarioNome" not in x for x in r)
 assert e["adjudication"]["result_absence_is_permanent_claim"] is False
 assert e["adjudication"]["payment_or_execution_proven"] is False
 return {"status":"PASS_TASK271_HISTORY_645_SEMANTIC_CANONIZATION","events":3}
