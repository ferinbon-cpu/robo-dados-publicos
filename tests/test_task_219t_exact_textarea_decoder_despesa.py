import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "docs/evidence/TASK_219T_OWNER_AUTHORIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219T_EXACT_TEXTAREA_DECODER_DESPESA_PAYLOAD_0.8.0.json"
CANON = ROOT / "docs/evidence/TASK_219T_EXACT_TEXTAREA_DECODER_CANONIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219T_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219t-exact-textarea-decoder-once.yml"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def test_task219t_authorization_is_one_passive_session():
    auth = load(AUTH)
    assert auth["authorized_main_sha"] == "92370c3b27520854a993560ca7a80fba094700b5"
    assert auth["owner_instruction"] == "Prossiga"
    assert auth["browser_sessions"] == 1
    assert auth["manual_navigations"] == 1
    for key in (
        "clicks",
        "typing",
        "form_submissions",
        "manual_fetch_xhr",
        "direct_endpoint_calls",
        "portal_action_triggers",
        "layerinfo_replay",
        "layerinfo_synthesis",
        "retries",
        "commitment_lookup",
    ):
        assert auth[key] == 0


def test_task219t_single_use_workflow_removed_and_preserved_exactly():
    canon = load(CANON)
    assert not LIVE.exists()
    assert blob_sha(HIST) == canon["runtime"]["executed_workflow_blob_sha"]
    assert canon["runtime"]["historical_source_exact_blob_match"] is True
    assert canon["runtime"]["workflow_removed_after_run"] is True


def test_task219t_binds_exact_current_session_despesa_response():
    payload = load(PAYLOAD)
    area = payload["same_session_despesa"]
    binding = payload["automatic_binding"]
    assert area["AreaName"] == "Despesa"
    assert area["AreaOrigin"] == "2_92_guestuser_207_6_DSL0_VIS1343"
    assert area["AreaId"].endswith("DSA6")
    assert binding["automatic_request_count"] == 8
    assert binding["same_session_request_match_count"] == 1
    assert binding["request_ordinal"] == 3
    assert binding["all_three_equal"] is True
    assert area["AreaId"] == binding["request_LayerInfo_id"] == binding["response_LayerInfo_id"]


def test_task219t_applies_exact_public_client_decoder_in_real_page():
    canon = load(CANON)
    decoder = canon["decoder_adjudication"]
    assert decoder["actual_decoder_expression"] == "$('<textarea />').html(v.info).text()"
    assert decoder["decoder_source_proven_by_TASK219S"] is True
    assert decoder["jquery_available"] is True
    assert decoder["jquery_version"] == "3.2.1"
    assert decoder["decoder_executed_inside_loaded_public_page"] is True
    assert decoder["decoder_input_length"] == 11305
    assert decoder["decoder_output_length"] == 9313
    assert decoder["exact_public_client_decoder_runtime_application_proven"] is True
    assert decoder["python_html_unescape_is_no_longer_needed_as_model"] is True


def test_task219t_decoder_output_is_real_html_with_four_scripts():
    canon = load(CANON)
    decoded = canon["decoded_structure_adjudication"]
    assert decoded["serialization"] == "HTML_LIKE"
    assert decoded["all_tag_count"] == 52
    assert decoded["tag_counts"]["div"] == 29
    assert decoded["tag_counts"]["script"] == 4
    assert decoded["script_count"] == 4
    assert decoded["form_count_in_inert_DOM"] == 0
    assert decoded["interactive_node_count_in_inert_DOM"] == 0
    assert decoded["explicit_action_count_in_inert_DOM"] == 0


def test_task219t_does_not_promote_inert_zero_nodes_to_action_absence():
    payload = load(PAYLOAD)
    assert payload["runtime_provisional_adjudication"]["official_action_absence_proven_by_carrier_rule"] is True
    assert payload["carrier_rule_qualification"]["official_action_absence_proven_by_carrier_rule_is_canonical"] is False
    canon = load(CANON)
    action = canon["action_adjudication"]
    assert action["official_action_contract_proven"] is False
    assert action["official_action_ambiguity_proven"] is False
    assert action["official_action_absence_proven"] is False
    assert action["runtime_carrier_provisional_absence_flag"] == "SUPERSEDED_BY_CANONIZATION"
    assert "four script elements" in action["reason"]


def test_task219t_supersedes_stale_task219o_dom_probe_route():
    canon = load(CANON)
    gain = canon["major_scientific_gain"]
    assert gain["same_session_response_selection_problem"] == "RESOLVED"
    assert gain["decoder_contract_problem"] == "RESOLVED"
    assert gain["decoded_serialization_problem"] == "RESOLVED_HTML_LIKE"
    assert gain["TASK219O_stale_DOM_probe_model"] == "SUPERSEDED"
    assert "current-session" in gain["why_TASK219O_is_superseded"]


def test_task219t_no_interaction_or_empenho_lookup():
    canon = load(CANON)
    fail = canon["fail_closed"]
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
        assert fail[key] == 0
    assert fail["commitment_3286_2026_queried"] is False
    assert fail["contract_45_2026_identity_proven"] is False
    assert fail["payment_attribution_proven"] is False
    assert fail["question_promotion_performed"] is False
    assert fail["coverage_after"] == 34


def test_task219t_future_network_requires_fresh_authorization():
    canon = load(CANON)
    consumption = canon["authorization_consumption"]
    assert consumption["task219t_scope_complete"] is True
    assert consumption["authorized_browser_session_consumed"] is True
    assert consumption["no_second_browser_session_used"] is True
    assert consumption["authorization_exhausted_for_future_network"] is True
    assert consumption["new_authorization_required_for_current_session_live_DOM_action_capture_or_any_interactive_query"] is True
