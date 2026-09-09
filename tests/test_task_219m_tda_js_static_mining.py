import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219M_TDA_JS_STATIC_MINING_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219M_TDA_JS_STATIC_MINING_PAYLOAD_0.8.0.json"
AUTH = ROOT / "docs/evidence/TASK_219M_OWNER_AUTHORIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219M_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219m-tda-js-static-mining-once.yml"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219m_authorization_is_six_known_gets_only():
    a = load(AUTH)
    assert a["authorized_main_sha"] == "715c2a5369452c1a79e8db4235d1b747e1638f00"
    assert a["max_get_requests"] == 6
    assert a["retries"] == 0
    assert a["redirect_following"] is False
    assert a["posts"] == 0
    assert a["browser_sessions"] == 0
    assert a["direct_awsgetcontentareas_calls"] == 0
    assert a["commitment_lookup"] == 0


def test_task219m_single_use_workflow_removed_and_preserved():
    ev = load(EVIDENCE)
    assert not LIVE.exists()
    assert blob_sha(HIST) == ev["runtime"]["executed_workflow_blob_sha"]
    assert ev["runtime"]["historical_source_exact_blob_match"] is True
    assert ev["runtime"]["workflow_removed_after_run"] is True


def test_task219m_all_six_public_scripts_were_http_200():
    p = load(PAYLOAD)
    assert p["network_boundary"]["get_requests"] == 6
    assert p["network_boundary"]["posts"] == 0
    assert len(p["resources"]) == 6
    assert all(x["http_status"] == 200 for x in p["resources"])


def test_task219m_aportalclientjs_is_exact_transport_carrier():
    p = load(PAYLOAD)
    k = p["key_carrier"]
    assert k["path"] == "/aportalclientjs.aspx"
    assert k["LayerInfo_occurrences"] == 1
    assert k["awsgetcontentareas_occurrences"] == 1
    assert k["function"] == "window.appendAreasWS"
    assert k["transport_contract"] == {
        "route": "awsgetcontentareas.aspx",
        "method": "POST",
        "form_field": "LayerInfo",
        "request_value_source": "appendAreasWS(pinfo)",
    }


def test_task219m_layerinfo_id_directly_binds_returned_content_to_dom():
    p = load(PAYLOAD)
    d = p["key_carrier"]["dom_binding"]
    assert d["content_container_key"] == "v.id"
    assert d["content_payload"] == "v.info"
    assert d["filter_container_pattern"] == "AREAFILTER_<v.id>"
    assert d["filter_payload"] == "v.filterarea"
    assert d["title_container_pattern"] == "<v.id>_title"
    assert d["performance_container_pattern"] == "<v.id>_icoperf"
    assert d["autorefresh_action"] == "AUTOREFRESH"
    assert d["autorefresh_identity"] == "v.id"


def test_task219m_generated_client_exposes_typed_portal_and_area_state():
    p = load(PAYLOAD)
    g = p["generated_client"]
    assert g["server_class"] == "tdaportalclient"
    assert g["package_name"] == "TDA.Programs"
    assert g["portal_state_control"] == "vSDT_TDAPORTAL"
    assert g["portal_state_type"] == "SDT_TDAPortal"
    assert g["portal_state_top_fields"] == [
        "MainId", "MainDivId", "MainEnvironment", "MainOrientation", "Layers"
    ]
    assert g["area_state_type"] == "SDT_TDAPortal.Layer.Area"
    for field in ("AreaId", "AreaName", "AreaOrigin", "AreaType", "AreaLayerJson", "Parms", "Links"):
        assert field in g["area_state_fields"]


def test_task219m_static_source_eliminates_generic_dom_binding_step():
    ev = load(EVIDENCE)
    gain = ev["major_scientific_gain"]
    assert gain["runtime_inference_replaced_by_static_source_proof"] is True
    assert gain["dom_binding_task_is_no_longer_needed"] is True
    assert gain["new_primary_state_target"] == "vSDT_TDAPORTAL"


def test_task219m_generic_scripts_contain_no_accounting_module_identity():
    p = load(PAYLOAD)
    assert all(v == 0 for v in p["accounting_static_terms"].values())
    ev = load(EVIDENCE)
    assert ev["negative_static_result"]["explicit_accounting_terms_in_six_scripts"] is False
    assert ev["fail_closed"]["expense_layer_identity_proven"] is False


def test_task219m_no_procurement_promotion_or_commitment_lookup():
    ev = load(EVIDENCE)
    f = ev["fail_closed"]
    assert f["commitment_3286_2026_queried"] is False
    assert f["contract_45_2026_identity_proven"] is False
    assert f["payment_attribution_proven"] is False
    assert f["question_promotion_performed"] is False
    assert f["contextual_paths_after"] == 34


def test_task219m_future_state_capture_requires_fresh_authorization():
    ev = load(EVIDENCE)
    c = ev["authorization_consumption"]
    assert c["task219m_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_passive_vSDT_TDAPORTAL_state_capture_or_any_direct_or_interactive_query"] is True
