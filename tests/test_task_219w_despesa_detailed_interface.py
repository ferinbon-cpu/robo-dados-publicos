import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "docs/evidence/TASK_219W_DESPESA_DETAILED_INTERFACE_CANONIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219W_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219w-execute-despesa-dolink-once.yml"
CARRIER = ROOT / "robo_dados_publicos/research/task219w_execute_despesa_dolink_once.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219w_executes_only_one_proven_action():
    c = load(CANON)
    a = c["action_execution"]
    assert a["proven_doLink_invocations"] == 1
    assert a["direct_element_clicks"] == 0
    assert a["fresh_AreaId_used"] is True
    assert a["manual_fetch_xhr"] == 0
    assert a["direct_endpoint_calls"] == 0
    assert a["retries"] == 0


def test_task219w_proves_detailed_dashboard_and_query_controls():
    c = load(CANON)
    p = c["post_action_portal"]
    q = c["explicit_query_controls_proven"]
    assert p["area_count_before"] == 8
    assert p["area_count_after"] == 17
    assert "Detalhe do Empenho" in p["new_detailed_area_names_proven"]
    assert q["exercise_selector"]["option_2026_present"] is True
    assert q["commitment_number_input"]["name"] == "Nro Empenho"
    assert q["commitment_number_input"]["type"] == "text"


def test_task219w_does_not_claim_target_submit_before_fresh_revalidation():
    q = load(CANON)["explicit_query_controls_proven"]
    assert q["exact_target_area_name_to_current_AreaId_mapping"].startswith("REQUIRES_FRESH")
    assert q["exact_submit_binding_for_target_area"].startswith("REQUIRES_FRESH")


def test_task219w_runtime_artifact_is_not_canonical_and_scalar_is_redacted():
    c = load(CANON)
    r = c["runtime"]
    s = c["carrier_sanitization_correction"]
    assert r["artifact_eligible_as_canonical_evidence"] is False
    assert r["artifact_retention_days"] == 1
    assert s["security_scalar_value_persisted_in_this_canonical_file"] is False
    assert s["security_scalar_reused"] is False
    serialized = CANON.read_text(encoding="utf-8")
    assert "vCSFRTOKEN" not in serialized


def test_task219w_carrier_no_longer_persists_control_values():
    text = CARRIER.read_text(encoding="utf-8")
    assert "const isControl=['input','select','textarea'].includes(tag);" in text
    assert "text:isControl?null" in text
    assert "safe_key.fullmatch" in text


def test_task219w_no_empenho_lookup_or_promotion_yet():
    s = load(CANON)["scientific_adjudication"]
    assert s["Empenho_3286_2026_queried"] is False
    assert s["contract_45_2026_identity_proven"] is False
    assert s["payment_attribution_proven"] is False
    assert s["coverage_after"] == 34


def test_task219w_single_use_workflow_removed_and_preserved():
    c = load(CANON)
    assert not LIVE.exists()
    assert blob_sha(HIST) == c["runtime"]["executed_workflow_blob_sha"]
