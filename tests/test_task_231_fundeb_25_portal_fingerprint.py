import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/fundeb_25_portal_fingerprint.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_231_FUNDEB_25_PORTAL_FINGERPRINT_0.8.0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def inventory_by_id(cfg):
    return {row["doc_id"]: row for row in cfg["inventory"]}


def test_exact_50_document_inventory_and_family_counts():
    cfg = load(CFG)
    ids = [row["doc_id"] for row in cfg["inventory"]]
    expected = [f"DOC-{n:03d}" for n in range(20, 41)] + [f"DOC-{n:03d}" for n in range(68, 97)]
    assert ids == expected
    assert len(ids) == len(set(ids)) == 50
    assert len({row["filename"] for row in cfg["inventory"]}) == 50
    assert sum(row["family"] == "a" for row in cfg["inventory"]) == 21
    assert sum(row["family"] == "fundeb25a" for row in cfg["inventory"]) == 29
    assert cfg["scope"]["family_counts"] == {"a": 21, "fundeb25a": 29}


def test_filename_parser_round_trips_without_semantic_inference():
    cfg = load(CFG)
    pattern = re.compile(cfg["filename_contract"]["pattern"])
    for row in cfg["inventory"]:
        match = pattern.fullmatch(row["filename"])
        assert match is not None
        assert match.group(1) == row["family"]
        assert row["entity_token"] == "137"
        assert match.group(2) == row["selector_1"]
        assert match.group(3) == row["selector_2"]
        assert match.group(4) == row["filename_timestamp_token"]
        assert "generated_at" not in row
        assert "report_printed_date" not in row
        assert "position_date" not in row
    assert cfg["filename_contract"]["selector_semantics"] == "OPAQUE_UNPROVEN"
    assert cfg["filename_contract"]["filename_timestamp_semantics"] == "OPAQUE_UNPROVEN"


def test_family_titles_are_source_proven_not_filename_inferred():
    cfg = load(CFG)
    families = cfg["family_contracts"]
    assert families["a"]["report_title"] == "APLICACAO COM RECURSOS DO FUNDEB"
    assert families["fundeb25a"]["report_title"] == "APLICACAO DOS RECURSOS PROPRIOS EM ENSINO - POR DATA"
    assert families["a"]["title_status"] == "DIRECT_BODY_PROOF"
    assert families["fundeb25a"]["title_status"] == "DIRECT_BODY_PROOF"


def test_decisive_filename_timestamp_counterexample_is_preserved():
    cfg = load(CFG)
    inv = inventory_by_id(cfg)
    proof = cfg["direct_body_sample_proofs"]["DOC-074"]
    assert inv["DOC-074"]["filename_timestamp_token"] == "13022026173134"
    assert proof["report_printed_date"] == "2025-10-21"
    assert proof["position_date"] == "2025-09-30"
    assert proof["proof_status"] == "DIRECT_BODY_READ_COUNTEREXAMPLE_TO_FILENAME_TOKEN"
    assert "FILENAME_TIMESTAMP_TOKEN_NE_REPORT_PRINTED_DATE" in cfg["guards"]
    assert "FILENAME_TIMESTAMP_TOKEN_NE_FISCAL_POSITION_DATE" in cfg["guards"]


def test_same_filename_token_can_have_three_different_positions():
    cfg = load(CFG)
    inv = inventory_by_id(cfg)
    proofs = cfg["direct_body_sample_proofs"]
    ids = ["DOC-026", "DOC-032", "DOC-036"]
    assert {inv[doc]["filename_timestamp_token"] for doc in ids} == {"13022026173759"}
    assert {proofs[doc]["report_printed_date"] for doc in ids} == {"2026-02-13"}
    assert [proofs[doc]["position_date"] for doc in ids] == ["2025-10-31", "2025-11-30", "2025-12-31"]
    assert len({(inv[doc]["selector_1"], inv[doc]["selector_2"]) for doc in ids}) == 3
    assert "OPAQUE_SELECTOR_NE_SEMANTIC_DIMENSION" in cfg["guards"]


def test_direct_body_sample_proofs_are_bounded_and_separate_from_inventory():
    cfg = load(CFG)
    proofs = cfg["direct_body_sample_proofs"]
    assert len(proofs) == 10
    assert proofs["DOC-020"] == {"report_printed_date":"2025-09-01","position_date":"2025-07-31","proof_status":"DIRECT_BODY_READ"}
    assert proofs["DOC-021"] == {"report_printed_date":"2025-10-14","position_date":"2025-08-31","proof_status":"DIRECT_BODY_READ"}
    assert proofs["DOC-071"]["report_printed_date"] == "2026-06-23"
    assert proofs["DOC-071"]["position_date"] == "2026-05-31"


def test_may_2026_snapshots_are_corroboration_not_new_numeric_promotion():
    cfg = load(CFG)
    overlap = cfg["overlap_map"]
    a_may = next(row for row in overlap if row.get("example_doc_id") == "DOC-025")
    pct_may = next(row for row in overlap if row.get("example_doc_id") == "DOC-071")
    assert a_may["position_date"] == pct_may["position_date"] == "2026-05-31"
    assert a_may["status"] == "CORROBORATION_OF_F02_LOCAL_MONITORING_ONLY"
    assert pct_may["status"] == "CORROBORATION_OF_F02_LOCAL_MONITORING_ONLY"
    assert cfg["promotion_decision"]["numeric_facts_promoted"] == 0
    assert cfg["promotion_decision"]["fingerprints_promoted"] == 50
    assert "NO_DOUBLE_COUNT_WITH_F02_TASK190_TASK230" in cfg["guards"]


def test_no_contextual_coverage_or_remote_effects_change():
    cfg = load(CFG)
    assert cfg["scope"]["contextual_coverage"] == "38/38_UNCHANGED"
    assert cfg["scope"]["numeric_promotion"] is False
    assert "NO_CONTEXTUAL_COVERAGE_CHANGE" in cfg["guards"]
    assert not any(cfg["remote_effects"].values())


def test_evidence_matches_config_contract():
    cfg = load(CFG)
    evidence = load(EVIDENCE)
    assert evidence["corpus"]["document_count"] == cfg["scope"]["document_count"] == 50
    assert evidence["corpus"]["a_family_count"] == 21
    assert evidence["corpus"]["fundeb25a_family_count"] == 29
    assert evidence["temporal_contract"]["filename_timestamp_token"] == "OPAQUE_UNPROVEN"
    assert evidence["overlap_assessment"]["numeric_facts_promoted"] == 0
    assert evidence["overlap_assessment"]["contextual_coverage_change"] is False
    assert evidence["remote_effects"] is False
