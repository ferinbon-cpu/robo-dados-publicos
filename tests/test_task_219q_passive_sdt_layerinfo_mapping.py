import hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_219Q_PASSIVE_SDT_LAYERINFO_MAPPING_CANONIZATION_0.8.0.json"
P=ROOT/"docs/evidence/TASK_219Q_PASSIVE_SDT_LAYERINFO_MAPPING_PAYLOAD_0.8.0.json"
OLD=ROOT/"docs/evidence/TASK_219N_TDA_PORTAL_STATE_PASSIVE_PAYLOAD_0.8.0.json"
H=ROOT/"docs/evidence/TASK_219Q_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
L=ROOT/".github/workflows/task-219q-despesa-layerinfo-mapping-passive-once.yml"

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def blob_sha(p):
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def test_task219q_single_use_workflow_removed():
    e=load(E)
    assert not L.exists()
    assert blob_sha(H)==e["runtime"]["executed_workflow_blob_sha"]
    assert e["runtime"]["historical_source_exact_blob_match"] is True
    assert e["runtime"]["workflow_removed_after_run"] is True

def test_task219q_maps_all_eight_areas_exactly():
    p=load(P)
    assert p["mapping_summary"]["automatic_call_count"]==8
    assert p["mapping_summary"]["mapped_area_count"]==8
    assert p["mapping_summary"]["unique_one_to_one_mapping_count"]==8
    assert p["mapping_summary"]["request_response_id_equal_count"]==8
    assert len(p["mappings"])==8
    assert all(m["current_AreaId"]==m["current_LayerInfoId"] for m in p["mappings"])

def test_task219q_despesa_mapping_is_direct_and_current_session():
    e=load(E)
    a=e["adjudication"]
    assert a["despesa_mapping_proven"] is True
    assert a["despesa_AreaName"]=="Despesa"
    assert a["despesa_AreaOrigin"]=="2_92_guestuser_207_6_DSL0_VIS1343"
    assert a["despesa_current_session_AreaId"]==a["despesa_current_session_LayerInfoId"]
    assert a["despesa_current_session_AreaId"].endswith("DSA6")

def test_task219q_request_contains_exact_despesa_area_origin_and_id():
    p=load(P)
    d=next(x for x in p["mappings"] if x["AreaName"]=="Despesa")
    assert d["exact_request_hits"]["AreaId"]==["$.id","$.info"]
    assert d["exact_request_hits"]["AreaOrigin"]==["$.info"]
    assert d["request_response_id_equal"] is True

def test_task219q_proves_full_area_id_is_session_scoped():
    old=load(OLD)
    new=load(P)
    old_id=old["despesas_identity"]["AreaId"]
    new_id=new["mapping_summary"]["despesa_current_AreaId"]
    assert old_id!=new_id
    assert old_id.endswith("DSA6") and new_id.endswith("DSA6")
    assert old["despesas_identity"]["AreaOrigin"]==new["mapping_summary"]["despesa_AreaOrigin"]
    assert re.fullmatch(r"[0-9a-f]{32}DSA6",old_id)
    assert re.fullmatch(r"[0-9a-f]{32}DSA6",new_id)

def test_task219q_supersedes_distinct_namespace_conclusion():
    e=load(E)
    c=e["cross_session_correction"]
    assert c["full_AreaId_stable_across_sessions"] is False
    assert c["TASK219P_distinct_identifier_layer_conclusion"]=="SUPERSEDED"
    assert "Within one session" in c["corrected_model"]
    assert "same-session current AreaId" in c["safe_runtime_selector"]

def test_task219q_no_response_action_or_empenho_interaction():
    e=load(E)
    f=e["fail_closed"]
    assert f["clicks"]==0
    assert f["typing"]==0
    assert f["form_submissions"]==0
    assert f["portal_action_triggers"]==0
    assert f["commitment_3286_2026_queried"] is False
    assert f["official_despesa_action_contract_proven"] is False
    assert f["coverage_after"]==34

def test_task219q_conditional_response_inspection_failure_is_not_mapping_failure():
    e=load(E)
    c=e["conditional_response_inspection"]
    assert c["performed"] is False
    assert c["does_not_reduce_mapping_proof"] is True

def test_task219q_future_network_needs_fresh_authorization():
    e=load(E)
    c=e["authorization_consumption"]
    assert c["single_authorized_browser_session_consumed"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_current_session_Despesa_info_action_capture_or_any_interactive_query"] is True
