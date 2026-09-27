import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219K_LAYERINFO_SCHEMA_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219K_LAYERINFO_SCHEMA_PASSIVE_PAYLOAD_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219K_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219k-layerinfo-schema-passive-once.yml"
AUTH = ROOT / "docs/evidence/TASK_219K_OWNER_AUTHORIZATION_0.8.0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219k_authorization_is_passive_only():
    a = load(AUTH)
    assert a["authorized_main_sha"] == "f12998d64b2b95a2021d4c0da6250eb80900002c"
    assert a["browser_sessions"] == 1
    assert a["manual_navigations"] == 1
    assert a["clicks"] == 0
    assert a["typing"] == 0
    assert a["form_submissions"] == 0
    assert a["manual_fetch_xhr"] == 0
    assert a["direct_endpoint_calls"] == 0
    assert a["retry"] == 0


def test_task219k_live_workflow_removed_and_preserved_exactly():
    ev = load(EVIDENCE)
    assert not LIVE.exists()
    assert blob_sha(HIST) == ev["runtime"]["executed_workflow_blob_sha"]
    assert ev["runtime"]["historical_source_exact_blob_match"] is True
    assert ev["runtime"]["workflow_removed_after_run"] is True


def test_task219k_layerinfo_is_stable_json_envelope():
    ev = load(EVIDENCE)
    x = ev["layerinfo_adjudication"]
    assert x["serialization_proven"] == "JSON"
    assert x["top_level_shape"] == "LIST_LENGTH_1_OF_OBJECT"
    assert x["stable_schema_across_eight_calls"] is True
    assert x["stable_key_set_across_eight_calls"] is True
    assert x["key_count"] == 17
    assert x["raw_scalar_values_persisted"] is False


def test_task219k_exact_layerinfo_key_set():
    ev = load(EVIDENCE)
    assert ev["layerinfo_adjudication"]["keys"] == [
        "changetitle", "env", "filter", "filterarea", "id", "info",
        "isdebug", "isduplic", "ispreview", "maindebugid", "newdebugid",
        "perf", "refreshtime", "runafter", "showfilter", "title", "updatemain",
    ]


def test_task219k_response_is_json_despite_text_html_mime():
    ev = load(EVIDENCE)
    r = ev["response_adjudication"]
    assert r["serialization_proven"] == "JSON"
    assert r["declared_mime_type"] == "text/html"
    assert r["declared_mime_type_is_misleading_for_payload_class"] is True
    assert r["actual_top_level_shape"] == "LIST_LENGTH_1_OF_OBJECT"
    assert r["all_eight_http_200"] is True
    assert r["all_eight_utf8"] is True


def test_task219k_request_and_response_typed_schema_are_equal():
    ev = load(EVIDENCE)
    req = ev["layerinfo_adjudication"]
    resp = ev["response_adjudication"]
    assert resp["same_17_keys_as_request"] is True
    assert resp["same_field_types_as_request"] is True
    assert resp["request_response_type_only_schema_equal"] is True
    assert req["type_only_schema_sha256"] == resp["type_only_schema_sha256"]
    assert req["type_only_schema_sha256"] == "e3140f95037307092e53805ee1cfc7a7b21caab8ebb03675281623537ef28d1b"


def test_task219k_nested_content_remains_unproven():
    ev = load(EVIDENCE)
    x = ev["layerinfo_adjudication"]
    assert x["info_field_is_text"] is True
    assert x["filterarea_field_is_text"] is True
    assert x["info_internal_serialization_proven"] is False
    assert x["filterarea_internal_serialization_proven"] is False


def test_task219k_no_direct_query_or_identity_promotion():
    ev = load(EVIDENCE)
    f = ev["fail_closed"]
    assert f["awsgetcontentareas_is_proven_accounting_endpoint"] is False
    assert f["direct_query_contract_proven"] is False
    assert f["expense_layer_identity_proven"] is False
    assert f["commitment_3286_2026_queried"] is False
    assert f["contract_45_2026_identity_proven"] is False
    assert f["payment_attribution_proven"] is False
    assert f["question_promotion_performed"] is False
    assert f["contextual_paths_after"] == 34
    assert f["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]


def test_task219k_authorization_consumed():
    ev = load(EVIDENCE)
    c = ev["authorization_consumption"]
    assert c["task219k_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_nested_info_filterarea_schema_capture_or_any_interactive_or_direct_query"] is True


def test_task219k_payload_has_no_raw_values():
    p = load(PAYLOAD)
    assert p["layerinfo_contract"]["raw_values_persisted"] is False
    assert p["response_contract"]["response_text_persisted"] is False
    assert p["hard_boundaries"]["layerinfo_replay"] == 0
    assert p["hard_boundaries"]["layerinfo_synthesis"] == 0
