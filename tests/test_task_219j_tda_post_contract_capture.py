import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219J_TDA_AUTOMATIC_POST_CONTRACT_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219J_SANITIZED_AUTOMATIC_POST_CONTRACT_PAYLOAD_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219J_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219j-tda-post-contract-capture-once.yml"
AUTH = ROOT / "docs/evidence/TASK_219J_OWNER_AUTHORIZATION_0.8.0.json"
CONFIG = ROOT / "config/task219j_tda_automatic_post_contract_capture.v1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219j_authorization_and_browser_boundary():
    auth = load(AUTH)
    assert auth["authorized_main_sha"] == "ee84959bc7b3889d7b2cf635214120450707d464"
    assert auth["browser_sessions"] == 1
    assert auth["manual_navigations"] == 1
    assert auth["clicks"] == 0
    assert auth["typing"] == 0
    assert auth["form_submissions"] == 0
    assert auth["manual_fetch_xhr"] == 0
    assert auth["direct_endpoint_calls"] == 0
    assert auth["retry"] == 0


def test_task219j_live_workflow_removed_and_source_preserved():
    ev = load(EVIDENCE)
    assert not LIVE.exists()
    assert blob_sha(HIST) == ev["runtime"]["executed_workflow_blob_sha"]
    assert ev["runtime"]["historical_source_exact_blob_match"] is True
    assert ev["runtime"]["workflow_removed_after_run"] is True


def test_task219j_exact_automatic_post_field_contract():
    ev = load(EVIDENCE)
    req = ev["request_contract_adjudication"]
    assert req["automatic_route_path"] == "/awsgetcontentareas.aspx"
    assert req["automatic_route_method"] == "POST"
    assert req["content_type"] == "application/x-www-form-urlencoded; charset=UTF-8"
    assert req["occurrence_count"] == 8
    assert req["field_set_proven"] is True
    assert req["field_names"] == ["LayerInfo"]
    assert req["only_one_field_per_request"] is True


def test_task219j_layerinfo_is_large_blob_without_raw_values():
    p = load(PAYLOAD)
    layer = p["request_contract"]["LayerInfo"]
    assert layer["value_class"] == "TEXT"
    assert layer["occurrences"] == 8
    assert layer["raw_value_persisted"] is False
    assert layer["length_min"] == 3119
    assert layer["length_max"] == 3954
    assert p["request_contract"]["all_requests_same_field_set"] is True


def test_task219j_all_response_bodies_were_sanitized_and_distinct():
    p = load(PAYLOAD)
    resp = p["response_contract"]
    assert resp["occurrence_count"] == 8
    assert resp["all_http_status"] == 200
    assert resp["all_mime_type"] == "text/html"
    assert resp["all_body_capture_status"] == "PASS_SANITIZED_STRUCTURE_ONLY"
    assert resp["unique_response_body_hash_count"] == 8
    assert resp["response_text_persisted"] is False
    assert len({r["body_sha256"] for r in resp["responses"]}) == 8


def test_task219j_response_serialization_stays_unproven():
    ev = load(EVIDENCE)
    r = ev["response_adjudication"]
    assert r["literal_html_structure_proven"] is False
    assert r["response_serialization_proven"] is False
    assert r["response_schema_proven"] is False


def test_task219j_no_direct_query_or_identity_promotion():
    ev = load(EVIDENCE)
    ff = ev["fail_closed"]
    assert ff["awsgetcontentareas_is_proven_accounting_endpoint"] is False
    assert ff["direct_query_contract_proven"] is False
    assert ff["commitment_3286_2026_queried"] is False
    assert ff["contract_45_2026_identity_proven"] is False
    assert ff["payment_attribution_proven"] is False
    assert ff["question_promotion_performed"] is False
    assert ff["contextual_paths_after"] == 34
    assert ff["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]


def test_task219j_future_network_requires_fresh_authorization():
    ev = load(EVIDENCE)
    c = ev["authorization_consumption"]
    assert c["task219j_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_LayerInfo_internal_structure_or_response_encoding_capture_or_any_direct_query"] is True
