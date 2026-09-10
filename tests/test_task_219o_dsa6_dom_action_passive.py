import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_219O_DSA6_DOM_ACTION_CANONIZATION_0.8.0.json"
P=ROOT/"docs/evidence/TASK_219O_DSA6_DOM_ACTION_PASSIVE_PAYLOAD_0.8.0.json"
H=ROOT/"docs/evidence/TASK_219O_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
L=ROOT/".github/workflows/task-219o-despesa-dom-action-passive-once.yml"

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def blob_sha(p):
    b=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def test_task219o_single_use_workflow_removed():
    e=load(E)
    assert not L.exists()
    assert blob_sha(H)==e["runtime"]["executed_workflow_blob_sha"]
    assert e["runtime"]["workflow_removed_after_run"] is True

def test_task219o_exact_despesa_dom_node_not_found():
    p=load(P)
    assert p["target"]["AreaName"]=="Despesa"
    assert p["target"]["AreaId"].endswith("DSA6")
    assert p["runtime_result"]["target_dom_node_found_after_load"] is False
    assert p["runtime_result"]["action_count"]==0

def test_task219o_does_not_weaken_upstream_identity():
    e=load(E)
    a=e["adjudication"]
    assert a["upstream_despesa_area_identity_remains_proven"] is True
    assert a["top_level_DOM_node_with_exact_AreaId_found"] is False
    assert a["action_contract_proven"] is False

def test_task219o_no_interaction_or_commitment_lookup():
    p=load(P)
    b=p["boundary"]
    assert b["clicks"]==0
    assert b["typing"]==0
    assert b["form_submissions"]==0
    assert b["manual_fetch_xhr"]==0
    assert b["portal_action_triggers"]==0
    assert b["direct_endpoint_calls"]==0
    e=load(E)
    assert e["fail_closed"]["commitment_3286_2026_queried"] is False
    assert e["fail_closed"]["coverage_after"]==34

def test_task219o_second_authorized_slot_survives():
    e=load(E)
    c=e["authorization_consumption"]
    assert c["slot_1_of_2_complete"] is True
    assert c["slot_2_of_2_remains_authorized"] is True
