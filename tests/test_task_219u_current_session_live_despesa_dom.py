import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "docs/evidence/TASK_219U_OWNER_AUTHORIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219U_CURRENT_SESSION_LIVE_DESPESA_DOM_PAYLOAD_0.8.0.json"
CANON = ROOT / "docs/evidence/TASK_219U_CURRENT_SESSION_LIVE_DOM_CANONIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219U_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219u-current-session-live-despesa-dom-once.yml"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219u_authorization_is_exactly_one_passive_session():
    auth = load(AUTH)
    assert auth["authorized_main_sha"] == "30db2414069565f8572aad1b32dd96d9cad5cd09"
    assert auth["owner_instruction"] == "Autorizado proximo grande salto"
    assert auth["browser_sessions"] == 1
    assert auth["manual_navigations"] == 1
    for key in (
        "clicks", "typing", "form_submissions", "manual_fetch_xhr",
        "direct_endpoint_calls", "portal_action_triggers", "layerinfo_replay",
        "layerinfo_synthesis", "retries", "commitment_lookup",
    ):
        assert auth[key] == 0


def test_task219u_single_use_workflow_removed_and_exactly_preserved():
    canon = load(CANON)
    assert not LIVE.exists()
    assert blob_sha(HIST) == canon["runtime"]["executed_workflow_blob_sha"]
    assert canon["runtime"]["historical_source_exact_blob_match"] is True
    assert canon["runtime"]["workflow_removed_after_run"] is True
    assert canon["runtime"]["single_runtime_run_count_after_removal"] == 1


def test_task219u_uses_current_session_despesa_identity():
    payload = load(PAYLOAD)
    area = payload["current_despesa"]
    assert payload["portal_state"]["portal_read"] is True
    assert payload["portal_state"]["target_match_count"] == 1
    assert area["AreaName"] == "Despesa"
    assert area["AreaOrigin"] == "2_92_guestuser_207_6_DSL0_VIS1343"
    assert area["AreaId"].endswith("DSA6")
    assert area["same_session_selector"] is True


def test_task219u_proves_live_root_is_rendered_chart_container():
    canon = load(CANON)
    live = canon["live_dom_adjudication"]
    assert live["current_session_root_exists"] is True
    assert live["root_tag"] == "div"
    assert live["root_class"] == "chart selected"
    assert live["root_contains_rendered_public_expense_summary"] is True
    assert live["tag_counts"]["script"] == 4
    assert live["inline_script_count"] == 4


def test_task219u_finds_no_accepted_explicit_html_action():
    canon = load(CANON)
    live = canon["live_dom_adjudication"]
    assert live["explicit_anchor_count"] == 0
    assert live["explicit_button_count"] == 0
    assert live["form_count"] == 0
    assert live["explicit_href_count"] == 0
    assert live["explicit_onclick_count"] == 0
    assert live["accepted_explicit_action_count"] == 0


def test_task219u_does_not_promote_zero_explicit_actions_to_universal_absence():
    payload = load(PAYLOAD)
    assert payload["runtime_provisional_adjudication"]["official_action_absence_proven_by_carrier_rule"] is True
    assert payload["carrier_rule_qualification"]["official_action_absence_proven_by_carrier_rule_is_canonical"] is False
    canon = load(CANON)
    action = canon["action_adjudication"]
    assert action["carrier_absence_flag_is_canonical"] is False
    assert action["runtime_carrier_provisional_absence_flag"] == "SUPERSEDED_BY_CANONIZATION"
    assert action["official_explicit_action_contract_proven"] is False
    assert action["universal_action_absence_proven"] is False


def test_task219u_records_delegated_listener_boundary_without_promotion():
    canon = load(CANON)
    d = canon["delegation_boundary"]
    assert d["document_click_listener_count"] == 3
    assert d["window_click_listener_count"] == 1
    assert d["generic_listener_presence_promotes_action"] is False
    assert d["listener_source_or_inline_script_semantics_inspected"] is False


def test_task219u_resolves_old_dom_problem_and_narrows_next_gargalo():
    canon = load(CANON)
    gain = canon["major_scientific_gain"]
    assert gain["stale_AreaId_DOM_problem"] == "RESOLVED"
    assert gain["current_session_live_root_problem"] == "RESOLVED"
    assert gain["post_render_DOM_shape"] == "PROVEN_CHART_CONTAINER"
    assert "inline chart scripts" in gain["new_single_gargalo"]


def test_task219u_no_interaction_identity_or_question_promotion():
    canon = load(CANON)
    fail = canon["fail_closed"]
    for key in (
        "clicks", "typing", "form_submissions", "manual_fetch_xhr",
        "direct_endpoint_calls", "portal_action_triggers", "layerinfo_replay", "retries",
    ):
        assert fail[key] == 0
    assert fail["commitment_3286_2026_queried"] is False
    assert fail["contract_45_2026_identity_proven"] is False
    assert fail["payment_attribution_proven"] is False
    assert fail["question_promotion_performed"] is False
    assert fail["coverage_after"] == 34


def test_task219u_future_script_semantics_requires_fresh_authorization():
    canon = load(CANON)
    c = canon["authorization_consumption"]
    assert c["task219u_scope_complete"] is True
    assert c["authorized_browser_session_consumed"] is True
    assert c["no_second_browser_session_used"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_delegated_script_semantic_capture_or_any_interactive_query"] is True
