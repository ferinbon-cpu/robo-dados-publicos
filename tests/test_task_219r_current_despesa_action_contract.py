import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_219R_CURRENT_DESPESA_ACTION_CONTRACT_CANONIZATION_0.8.0.json"
P=ROOT/"docs/evidence/TASK_219R_CURRENT_DESPESA_ACTION_CONTRACT_PAYLOAD_0.8.0.json"
H=ROOT/"docs/evidence/TASK_219R_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
L=ROOT/".github/workflows/task-219r-current-despesa-action-contract-once.yml"

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def blob_sha(p):
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def test_task219r_single_use_workflow_removed():
    e=load(E)
    assert not L.exists()
    assert blob_sha(H)==e["runtime"]["executed_workflow_blob_sha"]
    assert e["runtime"]["historical_source_exact_blob_match"] is True
    assert e["runtime"]["workflow_removed_after_run"] is True

def test_task219r_resolves_current_session_despesa_uniquely():
    e=load(E)
    b=e["binding_adjudication"]
    assert b["current_session_portal_state_read"] is True
    assert b["unique_Despesa_state_match"] is True
    assert b["selector"]["AreaName"]=="Despesa"
    assert b["selector"]["AreaOrigin"]=="2_92_guestuser_207_6_DSL0_VIS1343"
    assert b["current_session_AreaId"].endswith("DSA6")

def test_task219r_binds_exactly_one_of_eight_automatic_responses():
    p=load(P)
    b=p["automatic_binding"]
    assert b["automatic_request_count"]==8
    assert b["same_session_request_match_count"]==1
    assert b["request_ordinal"]==3
    assert b["current_AreaId_equals_request_id"] is True
    assert b["current_AreaId_equals_response_id"] is True
    assert b["request_response_id_equal"] is True

def test_task219r_selected_response_is_exact_current_despesa():
    p=load(P)
    d=p["current_session_despesa"]
    b=p["automatic_binding"]
    assert d["AreaName"]=="Despesa"
    assert d["AreaOrigin"]=="2_92_guestuser_207_6_DSL0_VIS1343"
    assert d["AreaId"]==b["request_layerinfo_id"]==b["response_layerinfo_id"]

def test_task219r_does_not_claim_action_absence_from_wrong_decoder():
    e=load(E)
    a=e["action_adjudication"]
    assert a["interactive_node_count"]==0
    assert a["official_action_count_under_that_decoder"]==0
    assert a["official_action_contract_proven"] is False
    assert a["official_action_absence_proven"] is False
    assert "not proven equivalent" in a["why_absence_is_not_proven"]

def test_task219r_reconciles_219l_and_219m():
    p=load(P)
    r=p["cross_task_reconciliation"]
    assert r["TASK219L_response_info_classification"]=="QUERY_LIKE_DELIMITED_WITHOUT_SAFE_KEYS"
    assert r["TASK219L_response_info_query_like_count"]==8
    assert r["TASK219M_client_transform"]=="public client applies unescapeHTML(v.info) before rendering"

def test_task219r_no_interaction_and_no_empenho_lookup():
    e=load(E)
    f=e["fail_closed"]
    for k in ("clicks","typing","form_submissions","manual_fetch_xhr","direct_endpoint_calls","portal_action_triggers","layerinfo_replay","retries"):
        assert f[k]==0
    assert f["commitment_3286_2026_queried"] is False
    assert f["coverage_after"]==34

def test_task219r_future_network_requires_fresh_authorization():
    e=load(E)
    c=e["authorization_consumption"]
    assert c["task219r_single_session_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
