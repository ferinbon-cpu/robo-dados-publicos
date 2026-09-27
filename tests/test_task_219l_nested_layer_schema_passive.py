import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219L_NESTED_LAYER_SCHEMA_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219L_NESTED_LAYER_SCHEMA_PASSIVE_PAYLOAD_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219L_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219l-nested-layer-schema-passive-once.yml"
AUTH = ROOT / "docs/evidence/TASK_219L_OWNER_AUTHORIZATION_0.8.0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219l_authorization_is_single_passive_session():
    a = load(AUTH)
    assert a["authorized_main_sha"] == "4ef5fa00b5ffd893d87d1372c5ce887d7f15ea3d"
    assert a["browser_sessions"] == 1
    assert a["manual_navigations"] == 1
    assert a["clicks"] == 0
    assert a["typing"] == 0
    assert a["form_submissions"] == 0
    assert a["manual_fetch_xhr"] == 0
    assert a["direct_endpoint_calls"] == 0
    assert a["layerinfo_replay"] == 0
    assert a["layerinfo_synthesis"] == 0
    assert a["commitment_lookup"] == 0
    assert a["retry"] == 0


def test_task219l_live_workflow_removed_and_historical_source_exact():
    ev = load(EVIDENCE)
    assert not LIVE.exists()
    assert blob_sha(HIST) == ev["runtime"]["executed_workflow_blob_sha"]
    assert ev["runtime"]["historical_source_exact_blob_match"] is True
    assert ev["runtime"]["workflow_removed_after_run"] is True


def test_task219l_all_eight_envelopes_were_valid():
    ev = load(EVIDENCE)
    n = ev["nested_adjudication"]
    assert n["all_eight_layer_envelopes_valid_in_request"] is True
    assert n["all_eight_layer_envelopes_valid_in_response"] is True
    assert n["request_filterarea_empty_in_all_eight"] is True


def test_task219l_no_accounting_layer_candidate():
    ev = load(EVIDENCE)
    n = ev["nested_adjudication"]
    assert n["safe_structural_identifier_count"] == 0
    assert n["explicit_accounting_structural_terms_found"] == []
    assert n["accounting_structural_candidate_count"] == 0
    assert n["accounting_structural_candidate_ordinals"] == []
    assert n["expense_layer_identity_proven"] is False


def test_task219l_query_string_label_is_fail_closed_reclassified():
    ev = load(EVIDENCE)
    q = ev["query_like_reclassification"]
    assert q["raw_runtime_parser_label"] == "QUERY_STRING"
    assert q["canonical_label"] == "QUERY_LIKE_DELIMITED_WITHOUT_SAFE_KEYS"
    assert q["query_contract_proven"] is False
    assert q["nested_key_names_proven"] is False


def test_task219l_ordinal7_size_does_not_promote():
    p = load(PAYLOAD)
    row7 = next(x for x in p["per_layer_shape"] if x["ordinal"] == 7)
    assert row7["response_info_pair_count"] == 15348
    assert row7["response_info_length_bucket"] == "65537+"
    ev = load(EVIDENCE)
    assert ev["nested_adjudication"]["accounting_structural_candidate_ordinals"] == []
    assert ev["fail_closed"]["expense_layer_identity_proven"] is False


def test_task219l_no_commitment_lookup_or_question_promotion():
    ev = load(EVIDENCE)
    f = ev["fail_closed"]
    assert f["commitment_3286_2026_queried"] is False
    assert f["contract_45_2026_identity_proven"] is False
    assert f["payment_attribution_proven"] is False
    assert f["question_promotion_performed"] is False
    assert f["contextual_paths_after"] == 34
    assert f["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]


def test_task219l_raw_nested_values_never_persisted():
    p = load(PAYLOAD)
    assert p["boundary"]["raw_nested_values_persisted"] is False
    assert p["boundary"]["visible_text_persisted"] is False
    assert p["boundary"]["response_text_persisted"] is False


def test_task219l_future_network_requires_new_authorization():
    ev = load(EVIDENCE)
    c = ev["authorization_consumption"]
    assert c["task219l_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_DOM_layer_binding_or_visible_label_capture_or_any_interactive_or_direct_query"] is True
