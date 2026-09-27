import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219N_TDA_PORTAL_STATE_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219N_TDA_PORTAL_STATE_PASSIVE_PAYLOAD_0.8.0.json"
AUTH = ROOT / "docs/evidence/TASK_219N_OWNER_AUTHORIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219N_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219n-tda-portal-state-passive-once.yml"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219n_authorization_is_one_passive_session():
    a = load(AUTH)
    assert a["authorized_main_sha"] == "cb4d5de3accb50d95fd7fad37ef19fb3e22a06bb"
    assert a["browser_sessions"] == 1
    assert a["manual_navigations"] == 1
    assert a["clicks"] == 0
    assert a["typing"] == 0
    assert a["form_submissions"] == 0
    assert a["manual_fetch_xhr"] == 0
    assert a["direct_endpoint_calls"] == 0
    assert a["layerinfo_replay"] == 0
    assert a["portal_action_trigger"] == 0
    assert a["commitment_lookup"] == 0
    assert a["retry"] == 0


def test_task219n_single_use_workflow_removed_and_preserved():
    ev = load(EVIDENCE)
    assert not LIVE.exists()
    assert blob_sha(HIST) == ev["runtime"]["executed_workflow_blob_sha"]
    assert ev["runtime"]["historical_source_exact_blob_match"] is True
    assert ev["runtime"]["workflow_removed_after_run"] is True


def test_task219n_geneXus_read_only_getter_is_proven_available():
    ev = load(EVIDENCE)
    g = ev["getter_adjudication"]
    assert g["geneXus_global_present"] is True
    assert g["gx_fn_present"] is True
    assert g["gx_fn_getControlValue_present"] is True
    assert g["vSDT_TDAPORTAL_read_succeeded"] is True
    assert g["vSDT_TDAPORTAL_decoded_type"] == "OBJECT"


def test_task219n_portal_has_one_layer_and_eight_areas():
    ev = load(EVIDENCE)
    p = ev["portal_state_adjudication"]
    assert p["layer_count"] == 1
    assert p["area_count"] == 8
    assert p["area_names"] == [
        "Exercício",
        "Receita",
        "Despesa",
        "WhatsApp",
        "Resumo",
        "Estatística de Acessos",
        "Acesso Rápido",
        "",
    ]


def test_task219n_unique_despesa_area_identity_is_proven():
    ev = load(EVIDENCE)
    d = ev["despesas_area_adjudication"]
    assert d["identity_proven"] is True
    assert d["unique_accounting_area_under_strong_direct_name_rule"] is True
    assert d["layer_index"] == 1
    assert d["area_index"] == 3
    assert d["AreaName"] == "Despesa"
    assert d["AreaId"] == "0e1483cd46954696a3e9b01c5be19e23DSA6"
    assert d["AreaDivId"] == d["AreaId"]
    assert d["AreaOrigin"] == "2_92_guestuser_207_6_DSL0_VIS1343"
    assert d["AreaType"] == "content"
    assert d["AreaFormat"] == "HTML Template"
    assert d["AreaAgg"] == "HTMLTemplate"


def test_task219n_payload_map_matches_canonical_despesa_area():
    p = load(PAYLOAD)
    areas = p["areas"]
    assert len(areas) == 8
    d = [x for x in areas if x["AreaName"] == "Despesa"]
    assert len(d) == 1
    assert d[0]["area_index"] == 3
    assert d[0]["AreaId"].endswith("DSA6")
    assert d[0]["AreaOrigin"].endswith("VIS1343")
    assert p["despesas_identity"]["proven"] is True
    assert p["despesas_identity"]["unique"] is True


def test_task219n_no_heuristic_size_or_ordinal_identity_needed():
    ev = load(EVIDENCE)
    gain = ev["major_scientific_gain"]
    assert gain["expense_area_identity_now_proven"] is True
    assert gain["ordinal_or_payload_size_inference_no_longer_needed"] is True
    assert "DSA6" in gain["exact_target_for_future_route_work"]
    assert "VIS1343" in gain["exact_target_for_future_route_work"]


def test_task219n_does_not_open_despesa_or_query_commitment():
    ev = load(EVIDENCE)
    f = ev["fail_closed"]
    assert f["expense_area_was_opened_or_triggered"] is False
    assert f["direct_query_contract_for_despesa_proven"] is False
    assert f["commitment_3286_2026_queried"] is False
    assert f["contract_45_2026_identity_proven"] is False
    assert f["payment_attribution_proven"] is False
    assert f["question_promotion_performed"] is False
    assert f["contextual_paths_after"] == 34
    assert f["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]


def test_task219n_raw_portal_state_and_security_values_not_persisted():
    p = load(PAYLOAD)
    b = p["boundary"]
    assert b["raw_portal_state_persisted"] is False
    assert b["raw_har_persisted"] is False
    assert b["cookies_tokens_persisted"] is False


def test_task219n_future_interaction_requires_fresh_authorization():
    ev = load(EVIDENCE)
    c = ev["authorization_consumption"]
    assert c["task219n_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_exact_despesa_action_contract_capture_or_any_direct_or_interactive_query"] is True
