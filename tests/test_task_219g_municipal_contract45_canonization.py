import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_219G_MUNICIPAL_CONTRACT45_CANONIZATION_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_219G_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"
HISTORICAL = ROOT / "docs/evidence/TASK_219G_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE_WORKFLOW = ROOT / ".github/workflows/task-219g-contract45-municipal-live-once.yml"
AUTH = ROOT / "docs/evidence/TASK_219G_OWNER_AUTHORIZATION_0.8.0.json"
CONFIG = ROOT / "config/task219g_municipal_contract45_live.v1.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha(path):
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219g_exact_query_and_authorization_scope():
    auth = _load(AUTH)
    cfg = _load(CONFIG)
    assert auth["canonical_main_sha_at_authorization"] == "aa86c2c60640cbb99d54b873c456662fc6ed8b98"
    assert auth["max_http_requests"] == 3
    assert auth["retry"] == 0
    assert auth["same_origin_only"] is True
    assert cfg["query"]["match_keys"] == {
        "year": 2026,
        "contract_number": "45/2026",
        "cnpj": "37457979000131",
        "contractor": "Med Doctor Acessórios Ltda",
    }


def test_task219g_historical_workflow_is_exact_and_live_workflow_removed():
    evidence = _load(EVIDENCE)
    assert _git_blob_sha(HISTORICAL) == evidence["runtime"]["executed_workflow_blob_sha"]
    assert evidence["runtime"]["historical_source_exact_blob_match"] is True
    assert evidence["runtime"]["workflow_removed_after_run"] is True
    assert not LIVE_WORKFLOW.exists()


def test_task219g_runtime_completed_without_transport_failure():
    payload = _load(PAYLOAD)
    evidence = _load(EVIDENCE)
    assert payload["request_count"] == 3
    assert [r["http_status"] for r in payload["requests"]] == [200, 200, 200]
    assert all(r["scheme"] == "https" for r in payload["requests"])
    assert all(r["host"] == "serv42.limeira.sp.gov.br" for r in payload["requests"])
    assert all(r["bytes_received"] > 0 for r in payload["requests"])
    assert evidence["transport"]["transport_or_edge_failure"] is False


def test_task219g_form_and_relay_were_proven_and_result_table_interpretable():
    payload = _load(PAYLOAD)
    ev = payload["resolver_result"]["evidence"]
    assert ev["form_discovery"]["status"] == "PASS_FORM_DISCOVERY"
    assert ev["submission"]["autosubmit_relay"]["status"] == "PASS_PROVEN_AUTOSUBMIT_RELAY"
    assert ev["submission"]["relay_followup"]["table_rows"] == 17


def test_task219g_no_match_is_bounded_not_universal_absence():
    payload = _load(PAYLOAD)
    evidence = _load(EVIDENCE)
    assert payload["resolver_result"]["status"] == "NO_MATCH"
    assert payload["resolver_result"]["candidates"] == []
    assert evidence["adjudication"]["bounded_municipal_query_completed"] is True
    assert evidence["adjudication"]["bounded_municipal_no_match_valid"] is True
    assert evidence["adjudication"]["universal_contract_absence_proven"] is False
    assert evidence["adjudication"]["municipal_contract_identity_bridge_proven"] is False


def test_task219g_does_not_promote_questions_or_other_identity_layers():
    evidence = _load(EVIDENCE)
    adj = evidence["adjudication"]
    assert adj["jom_contract_45_2026_seed_remains_primary_evidence"] is True
    assert adj["pncp_identity_proven"] is False
    assert adj["tce_commitment_identity_proven"] is False
    assert adj["payment_or_execution_identity_proven"] is False
    assert adj["question_promotion_performed"] is False
    assert adj["contextual_paths_after"] == 34
    assert adj["remaining_blockers"] == ["CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"]


def test_task219g_authorization_is_consumed_at_scope_completion():
    evidence = _load(EVIDENCE)
    c = evidence["authorization_consumption"]
    assert c["task219g_scope_complete"] is True
    assert c["authorization_exhausted_for_future_network"] is True
    assert c["new_authorization_required_for_any_additional_source_or_query"] is True
