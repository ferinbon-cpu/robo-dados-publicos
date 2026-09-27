import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "docs/evidence/TASK_219S_CLIENT_DECODER_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219S_CLIENT_UNESCAPEHTML_DESPESA_PASSIVE_PAYLOAD_0.8.0.json"
STATIC = ROOT / "docs/evidence/TASK_219S_CLIENT_DECODER_STATIC_SOURCE_0.8.0.json"
AUTH = ROOT / "docs/evidence/TASK_219S_OWNER_AUTHORIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219S_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219s-client-unescapehtml-despesa-once.yml"
CARRIER = ROOT / "robo_dados_publicos/research/task219s_client_unescapehtml_despesa_passive.py"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219s_authorization_is_one_passive_session():
    a = load(AUTH)
    assert a["authorized_main_sha"] == "d2bf447e124732f4700d5c948f8c53b0a80ace0a"
    assert a["browser_sessions"] == 1
    assert a["manual_navigations"] == 1
    assert a["clicks"] == 0
    assert a["typing"] == 0
    assert a["form_submissions"] == 0
    assert a["manual_fetch_xhr"] == 0
    assert a["direct_endpoint_calls"] == 0
    assert a["portal_action_triggers"] == 0
    assert a["commitment_lookup"] == 0


def test_task219s_single_use_workflow_removed_and_preserved():
    e = load(CANON)
    assert not LIVE.exists()
    assert blob_sha(HIST) == e["runtime"]["executed_workflow_blob_sha"]
    assert e["runtime"]["historical_source_exact_blob_match"] is True
    assert e["runtime"]["workflow_removed_after_run"] is True
    assert blob_sha(CARRIER) == e["runtime"]["executed_carrier_blob_sha"]


def test_task219s_same_session_despesa_response_is_still_exact():
    e = load(CANON)
    b = e["same_session_binding_adjudication"]
    assert b["current_session_portal_state_read"] is True
    assert b["unique_Despesa_state_match"] is True
    assert b["AreaName"] == "Despesa"
    assert b["AreaOrigin"] == "2_92_guestuser_207_6_DSL0_VIS1343"
    assert b["current_session_AreaId"].endswith("DSA6")
    assert b["automatic_request_count"] == 8
    assert b["matching_LayerInfo_request_count"] == 1
    assert b["current_session_despesa_response_binding_proven"] is True


def test_task219s_runtime_proves_unescapehtml_is_not_global_callable():
    p = load(PAYLOAD)
    r = p["runtime_decoder_probe"]
    assert r["window_unescapeHTML_callable"] is False
    assert r["candidate_global_count"] == 0
    assert r["resolved_name"] is None
    assert r["transformed_output_produced"] is False


def test_task219s_static_source_proves_actual_decoder_expression():
    s = load(STATIC)
    assert s["literal_search"]["unescapeHTML_literal_count_across_archived_public_scripts"] == 0
    d = s["exact_decoder_contract"]
    assert d["appendAreasWS_function_start_line"] == 666
    assert d["response_info_decode_line"] == 680
    assert d["response_info_decode_expression"] == "$('<textarea />').html(v.info).text()"
    assert d["response_info_decode_line_sha256"] == "92cb92a24dfe2f7d9effe09b35b853a2e9067f63a43dc22bb07093c7ff8e988a"
    assert d["content_target_line"] == 683
    assert d["content_append_line"] == 684
    assert d["response_filterarea_decode_line"] == 722
    assert d["runafter_execution_line"] == 770


def test_task219s_supersedes_function_shorthand_not_decoder_fact():
    e = load(CANON)
    d = e["decoder_adjudication"]
    assert d["runtime_global_unescapeHTML_function_found"] is False
    assert d["previous_unescapeHTML_function_shorthand"] == "SUPERSEDED"
    assert d["actual_public_client_decoder_contract_proven"] is True
    assert d["actual_decoder_expression"] == "$('<textarea />').html(v.info).text()"
    assert d["runafter_is_separate_from_decoder"] is True


def test_task219s_does_not_claim_python_equivalence_or_action_absence():
    e = load(CANON)
    c = e["scientific_correction"]
    assert c["python_html_unescape_equivalence_to_textarea_decoder_proven"] is False
    assert c["official_action_contract_proven"] is False
    assert c["official_action_absence_proven"] is False


def test_task219s_fail_closed_and_coverage_unchanged():
    e = load(CANON)
    f = e["fail_closed"]
    for key in (
        "clicks",
        "typing",
        "form_submissions",
        "manual_fetch_xhr",
        "direct_endpoint_calls",
        "portal_action_triggers",
        "layerinfo_replay",
        "retries",
    ):
        assert f[key] == 0
    assert f["commitment_3286_2026_queried"] is False
    assert f["contract_45_2026_identity_proven"] is False
    assert f["payment_attribution_proven"] is False
    assert f["question_promotion_performed"] is False
    assert f["coverage_after"] == 34
    assert f["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]


def test_task219s_future_network_requires_fresh_authorization():
    e = load(CANON)
    c = e["authorization_consumption"]
    assert c["task219s_scope_complete"] is True
    assert c["authorized_browser_session_consumed"] is True
    assert c["no_second_browser_session_used"] is True
    assert c["authorization_exhausted_for_future_network"] is True
