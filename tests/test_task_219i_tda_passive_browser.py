import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219I_TDA_PASSIVE_BROWSER_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219I_PASSIVE_BROWSER_PAYLOAD_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219I_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219i-tda-passive-browser-once.yml"
AUTH = ROOT / "docs/evidence/TASK_219I_OWNER_AUTHORIZATION_0.8.0.json"
CONFIG = ROOT / "config/task219i_tda_passive_browser_inspection.v1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219i_authorization_is_passive_browser_only():
    auth = load(AUTH)
    assert auth["authorized_main_sha"] == "36927b31ce455c1479b380edc90ef429c51b55db"
    assert auth["browser_sessions"] == 1
    assert auth["manual_navigations"] == 1
    assert auth["clicks"] == 0
    assert auth["typing"] == 0
    assert auth["form_submissions"] == 0
    assert auth["authentication"] is False
    assert auth["endpoint_guessing"] is False


def test_task219i_live_workflow_removed_and_historical_source_exact():
    ev = load(EVIDENCE)
    assert not LIVE.exists()
    assert blob_sha(HIST) == ev["runtime"]["executed_workflow_blob_sha"]
    assert ev["runtime"]["historical_source_exact_blob_match"] is True
    assert ev["runtime"]["workflow_removed_after_run"] is True


def test_task219i_public_browser_surface_loaded_without_manual_authentication():
    p = load(PAYLOAD)
    ev = load(EVIDENCE)
    assert p["status"] == "PASS_PASSIVE_BROWSER_OBSERVATION"
    assert p["page"]["final_url_host"] == "transparencia.limeira.sp.gov.br"
    assert p["page"]["final_url_path"] == "/tdaportalclient.aspx"
    assert p["page"]["title"] == "Prefeitura Municipal de Limeira"
    assert ev["adjudication"]["browser_level_public_surface_is_loadable_without_manual_authentication"] is True


def test_task219i_observed_same_host_automatic_content_route():
    p = load(PAYLOAD)
    xhr = p["network"]["same_host_automatic_xhr"]
    assert len(xhr) == 1
    assert xhr[0] == {
        "method": "POST",
        "path": "/awsgetcontentareas.aspx",
        "http_status": 200,
        "mime_type": "text/html",
        "initiator_type": "script",
        "occurrence_count": 8,
    }


def test_task219i_route_is_structural_seed_not_machine_api_or_accounting_identity():
    ev = load(EVIDENCE)
    obs = ev["observation"]
    adj = ev["adjudication"]
    assert obs["machine_readable_get_route_found"] is False
    assert obs["acceptable_machine_route_count"] == 0
    assert adj["awsgetcontentareas_route_family_observed_from_page_itself"] is True
    assert adj["awsgetcontentareas_is_proven_accounting_endpoint"] is False
    assert adj["awsgetcontentareas_direct_query_authorized"] is False
    assert adj["request_payload_contract_proven"] is False
    assert adj["response_schema_proven"] is False


def test_task219i_did_not_query_commitment_or_promote_questions():
    ev = load(EVIDENCE)
    adj = ev["adjudication"]
    assert adj["commitment_3286_2026_queried"] is False
    assert adj["procurement_identity_proven"] is False
    assert adj["payment_attribution_proven"] is False
    assert adj["question_promotion_performed"] is False
    assert adj["contextual_paths_after"] == 34
    assert adj["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]


def test_task219i_vendor_host_observation_is_static_only():
    p = load(PAYLOAD)
    v = p["network"]["vendor_host_observation"]
    assert v["host"] == "bi.etransparencia.com.br"
    assert v["request_count"] == 8
    assert v["all_observed_requests_static_images"] is True
    assert v["machine_route_observed"] is False


def test_task219i_future_network_requires_new_authorization():
    ev = load(EVIDENCE)
    c = ev["authorization_consumption"]
    assert c["task219i_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_payload_or_response_structure_capture_or_any_direct_route_query"] is True
