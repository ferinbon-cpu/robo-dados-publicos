import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "docs/evidence/TASK_219V_DESPESA_SCRIPT_SEMANTICS_CANONIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219V_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219v-despesa-script-semantics-once.yml"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219v_unique_dolink_contract_is_proven():
    c = load(CANON)
    a = c["action_adjudication"]
    assert a["unique_official_despesa_navigation_contract_proven"] is True
    assert a["kind"] == "doLink"
    assert a["parameter_template"] == "<CURRENT_SESSION_AreaId>**##**V1343[vl]"
    assert a["number_of_unique_contracts"] == 1
    assert a["number_of_visual_bindings_to_same_contract"] == 4
    assert a["action_executed_in_TASK219V"] is False


def test_task219v_all_four_scripts_converge():
    s = load(CANON)["script_semantics"]
    assert s["inline_script_count"] == 4
    assert s["inline_script_length_each"] == 787
    assert s["all_four_scripts_converge_to_same_contract"] is True
    assert s["generic_document_window_click_listeners_supply_no_competing_contract"] is True


def test_task219v_requires_fresh_session_areaid():
    c = load(CANON)
    assert c["same_session_despesa"]["AreaId_is_session_scoped"] is True
    assert c["action_adjudication"]["current_session_AreaId_must_be_resolved_fresh_before_execution"] is True


def test_task219v_remains_fail_closed():
    f = load(CANON)["fail_closed"]
    for key in ("clicks","typing","form_submissions","manual_fetch_xhr","direct_endpoint_calls","portal_action_triggers","layerinfo_replay","retries"):
        assert f[key] == 0
    assert f["empenho_3286_2026_queried"] is False
    assert f["coverage_after"] == 34


def test_task219v_single_use_workflow_removed_and_preserved():
    c = load(CANON)
    assert not LIVE.exists()
    assert blob_sha(HIST) == c["runtime"]["executed_workflow_blob_sha"]
