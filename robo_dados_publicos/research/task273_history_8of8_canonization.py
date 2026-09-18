import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/"config/task273_history_8of8_canonization.v1.json";EV=ROOT/"docs/evidence/TASK_273_HISTORY_8OF8_CANONICAL_0.8.0.json";FIX=ROOT/"docs/evidence/fixtures/task273/TASK_273_HISTORY_8OF8_SUMMARY.jsonl"
def load(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def rows():return [json.loads(x) for x in FIX.read_text(encoding="utf-8").splitlines() if x.strip()]
def validate():
 c=load(CFG);e=load(EV);r=rows()
 assert c["schema"]=="TASK273_HISTORY_8OF8_CANONIZATION_V1" and len(r)==8
 assert sum(x["event_count"] for x in r)==49
 cats={};types={};docs={}
 for x in r:
  for k,v in x["categories"].items():cats[k]=cats.get(k,0)+v
  for k,v in x["types"].items():types[k]=types.get(k,0)+v
  for k,v in x["document_types"].items():docs[k]=docs.get(k,0)+v
  assert x["result_reference_count"]==0
  assert re.fullmatch(r"[0-9a-f]{64}",x["body_sha256"])
  assert re.fullmatch(r"[0-9a-f]{64}",x["safe_projection_sha256"])
 assert cats==c["expected"]["categories"] and types==c["expected"]["types"] and docs==c["expected"]["document_types"]
 assert sum(len(x["item_numbers"]) for x in r)==9
 assert e["adjudication"]["result_reference_zero_is_permanent_absence_claim"] is False
 assert e["privacy"]["usuarioNome_persisted"] is False
 return {"status":"PASS_TASK273_HISTORY_8OF8_CANONIZATION","controls":8,"events":49}
