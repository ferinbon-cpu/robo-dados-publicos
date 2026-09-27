import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/"docs/evidence/TASK_219Z_DETAIL_QUERY_GATE_NEGATIVE_CANONIZATION_0.8.0.json"
HIST=ROOT/"docs/evidence/TASK_219Z_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE=ROOT/".github/workflows/task-219z-query-detail-empenho-3286-once.yml"

def load(): return json.loads(CANON.read_text(encoding="utf-8"))
def blob_sha(p):
    raw=p.read_bytes(); return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def test_detail_target_stable_but_session_id_dynamic():
    c=load()["same_session_target"]
    assert c["AreaName"]=="Detalhe do Empenho"
    assert c["AreaOrigin"]=="2_92_guestuser_200_8_DSL0_VIS706"
    assert c["target_match_count"]==1 and c["content_root_exists"] and c["filter_root_exists"]

def test_structural_pair_reproduced_but_semantic_gate_did_not():
    g=load()["gate_result"]
    assert g["filter_text_input_total"]==1 and g["filter_select_total"]==1
    assert g["semantic_Nro_Empenho_match_count"]==0
    assert g["semantic_Exercicio_2026_match_count"]==0
    assert g["exact_filter_id_submmitApply_binding_count"]==0
    x=load()["cross_session_comparison_with_TASK219Y"]
    assert x["same_filter_root_structural_control_counts_1_text_plus_1_select"] is True
    assert x["universal_absence_inference_allowed"] is False

def test_no_query_or_identity_promotion():
    b=load()["boundary"]
    assert b["query_field_assignments"]==0 and b["target_filter_invocations"]==0 and b["retries"]==0
    assert b["Empenho_3286_2026_queried"] is False
    s=load()["scientific_adjudication"]
    assert s["exact_submit_contract_proven"] is False
    assert s["contract_45_2026_to_empenho_3286_2026_proven"] is False
    assert s["payment_attribution_proven"] is False and s["coverage_after"]==34

def test_single_use_workflow_removed_and_preserved():
    c=load(); assert not LIVE.exists(); assert blob_sha(HIST)==c["runtime"]["executed_workflow_blob_sha"]
