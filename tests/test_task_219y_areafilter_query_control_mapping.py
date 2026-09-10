import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/"docs/evidence/TASK_219Y_AREAFILTER_QUERY_CONTROL_MAPPING_CANONIZATION_0.8.0.json"
HIST=ROOT/"docs/evidence/TASK_219Y_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
LIVE=ROOT/".github/workflows/task-219y-map-areafilter-once.yml"

def load(): return json.loads(CANON.read_text(encoding="utf-8"))
def blob_sha(p):
    raw=p.read_bytes(); return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def test_no_query_or_retry():
    b=load()["boundary"]
    assert b["query_field_assignments"]==0 and b["filter_invocations"]==0 and b["retries"]==0
    assert b["Empenho_3286_2026_queried"] is False

def test_filter_root_architecture_proven():
    a=load()["architecture_proven"]
    assert a["detailed_area_count"]==17
    assert a["filter_container_pattern"]=="AREAFILTER_<AreaId>"
    assert a["query_controls_can_live_in_filter_root_separate_from_content_result_root"] is True

def test_detail_area_has_minimal_pair():
    rows={r["AreaName"]:r for r in load()["target_area_mappings"]}
    d=rows["Detalhe do Empenho"]
    assert d["Nro_Empenho_count"]==1 and d["Exercicio_2026_count"]==1
    assert d["select_count_in_filter"]==1 and d["text_input_count_in_filter"]==1
    assert d["minimal_exact_pair_for_commitment_lookup"] is True
    assert rows["Empenhado"]["complete_query_control_pair"] is False

def test_submmit_signature_corrected_without_overclaim():
    s=load()["submmitApply_signature_correction"]
    assert s["prior_same_AreaId_only_rule_rejected"] is True
    assert s["observed_onclick_template"]=="submmitApply('AREAFILTER_<AreaId>');"
    a=load()["scientific_adjudication"]
    assert a["exact_Detalhe_do_Empenho_submit_binding_proven"] is False
    assert a["query_contract_fully_proven"] is False
    assert a["coverage_after"]==34

def test_single_use_workflow_removed_and_preserved():
    c=load(); assert not LIVE.exists(); assert blob_sha(HIST)==c["runtime"]["executed_workflow_blob_sha"]
