import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "docs/evidence/TASK_219X_EMPENHADO_AREA_NEGATIVE_CANONIZATION_0.8.0.json"
HIST = ROOT / "docs/evidence/TASK_219X_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE = ROOT / ".github/workflows/task-219x-query-empenho-3286-once.yml"


def load():
    return json.loads(CANON.read_text(encoding="utf-8"))


def blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def test_task219x_revalidates_top_level_and_unique_empenhado_area():
    c = load()
    assert c["top_level"]["despesa_match_count"] == 1
    assert c["top_level"]["four_chart_bindings_revalidated"] is True
    assert c["top_level"]["top_level_doLink_invocations"] == 1
    assert c["detailed_dashboard"]["area_count"] == 17
    assert c["detailed_dashboard"]["Empenhado_area_match_count"] == 1


def test_task219x_rejects_empenhado_as_query_form():
    q = load()["exact_Empenhado_subtree_control_result"]
    assert q["Nro_Empenho_input_count"] == 0
    assert q["Exercicio_select_count"] == 0
    assert q["same_AreaId_filter_node_count"] == 0
    assert q["same_AreaId_submmitApply_script_binding_count"] == 0
    assert q["conclusion"].startswith("EMPENHADO_IS_NOT_THE_QUERY_FORM_AREA")


def test_task219x_no_query_was_executed():
    f = load()["fail_closed_boundary"]
    assert f["controlled_query_field_assignments"] == 0
    assert f["same_area_filter_invocations"] == 0
    assert f["same_record_detail_drilldowns"] == 0
    assert f["retries"] == 0
    assert f["Empenho_3286_2026_queried"] is False


def test_task219x_does_not_promote_identity_or_absence():
    s = load()["scientific_adjudication"]
    assert s["Empenhado_area_as_query_form_rejected"] is True
    assert s["absence_of_query_form_elsewhere_proven"] is False
    assert s["contract_45_2026_to_empenho_3286_2026_proven"] is False
    assert s["payment_attribution_proven"] is False
    assert s["coverage_after"] == 34


def test_task219x_single_use_workflow_removed_and_preserved():
    c = load()
    assert not LIVE.exists()
    assert blob_sha(HIST) == c["runtime"]["executed_workflow_blob_sha"]
