import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_219P_DSA6_ACTION_EMPENHO_GATED_CANONIZATION_0.8.0.json"
P=ROOT/"docs/evidence/TASK_219P_DSA6_ACTION_EMPENHO_GATED_PAYLOAD_0.8.0.json"
H=ROOT/"docs/evidence/TASK_219P_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
L=ROOT/".github/workflows/task-219p-dsa6-action-empenho-gated-once.yml"
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def blob_sha(p):
 b=p.read_bytes(); return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def test_task219p_single_use_workflow_removed():
 e=load(E)
 assert not L.exists()
 assert blob_sha(H)==e["runtime"]["executed_workflow_blob_sha"]
 assert e["runtime"]["workflow_removed_after_run"] is True

def test_task219p_saw_eight_automatic_requests_but_no_DSA6_returned_id():
 p=load(P)
 assert p["automatic_capture"]["awsgetcontentareas_request_count"]==8
 assert p["automatic_capture"]["exact_returned_id_equal_to_AreaId_DSA6_count"]==0
 assert p["automatic_capture"]["selection_policy"]=="EXACT_EQUALITY_ONLY"

def test_task219p_rejects_AreaId_equals_returned_id_hypothesis():
 e=load(E)
 a=e["adjudication"]
 assert a["AreaId_equals_LayerInfo_returned_id_hypothesis"]=="REJECTED_FOR_THIS_PUBLIC_STATE"
 assert a["despesa_area_identity_from_TASK219N_remains_proven"] is True
 assert a["official_despesa_action_contract_proven"] is False

def test_task219p_executes_nothing_after_gate_failure():
 p=load(P)
 x=p["interactions_executed"]
 assert x=={"official_despesa_action":0,"text_entry":0,"query_submit":0,"commitment_lookup":0}
 e=load(E)
 f=e["fail_closed"]
 assert f["no_second_browser_session"] is True
 assert f["no_retry"] is True
 assert f["commitment_3286_2026_queried"] is False

def test_task219p_static_reconciliation_requires_mapping_not_inference():
 e=load(E)
 s=e["static_source_reconciliation"]
 assert s["TASK219M_proved_returned_v_id_is_DOM_destination"] is True
 assert s["TASK219N_proved_AreaId_DSA6_is_Despesa"] is True
 assert s["TASK219O_proved_no_stable_top_level_DOM_node_named_DSA6_after_load"] is True
 assert s["TASK219P_proved_no_returned_v_id_exactly_equals_DSA6"] is True
 assert "mapping" in s["safe_conclusion"].lower()

def test_task219p_two_slot_authorization_fully_consumed():
 e=load(E)
 c=e["authorization_consumption"]
 assert c["slot_1_TASK219O_complete"] is True
 assert c["slot_2_TASK219P_complete"] is True
 assert c["two_large_leap_authorization_fully_consumed"] is True
 assert c["new_authorization_required_for_future_network"] is True

def test_task219p_no_identity_or_question_promotion():
 e=load(E)
 f=e["fail_closed"]
 assert f["contract_45_2026_identity_proven"] is False
 assert f["payment_attribution_proven"] is False
 assert f["question_promotion_performed"] is False
 assert f["coverage_after"]==34
