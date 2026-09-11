import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/rreo_2026_b1_b2_incremental.v1.json"
TASK188 = ROOT / "config/task188_rreo_rests_payable_2026.v1.json"
TASK190 = ROOT / "config/task190_rreo_education_spending_2026.v1.json"
TASK229 = ROOT / "config/rgf_2026_q1_primary.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_230_RREO_B1_B2_INCREMENTAL_0.8.0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def series_by_period(cfg):
    return {row["period"]: row for row in cfg["annex14_summary_series"]}


def test_exact_18_document_audit_and_no_coverage_change():
    cfg = load(CFG)
    ids = [row["doc_id"] for row in cfg["document_audit"]]
    expected = [
        "DOC-041","DOC-043","DOC-044","DOC-045","DOC-046","DOC-047",
        "DOC-048","DOC-050","DOC-052","DOC-053","DOC-055","DOC-056",
        "DOC-059","DOC-060","DOC-061","DOC-062","DOC-063","DOC-064",
    ]
    assert ids == expected
    assert len(ids) == len(set(ids)) == 18
    assert cfg["scope"]["contextual_coverage"] == "38/38_UNCHANGED"
    assert "NO_CONTEXTUAL_COVERAGE_CHANGE" in cfg["guards"]
    assert not any(cfg["remote_effects"].values())


def test_known_canonical_documents_are_not_double_promoted():
    cfg = load(CFG)
    audit = {row["doc_id"]: row for row in cfg["document_audit"]}
    assert audit["DOC-061"]["status"] == "FULLY_CANONICAL_TASK188"
    assert audit["DOC-062"]["status"] == "FULLY_CANONICAL_TASK188"
    assert audit["DOC-063"]["status"] == "FULLY_CANONICAL_TASK190"
    assert audit["DOC-048"]["status"] == "PARTIALLY_CANONICAL_TASK190"
    assert "SAME_FACT_DIFFERENT_ANNEX_NE_NEW_FACT" in cfg["guards"]


def test_annex14_b1_and_b2_exact_core_values():
    cfg = load(CFG)
    s = series_by_period(cfg)
    b1, b2 = s["2026-02"], s["2026-04"]

    assert b1["budget_execution"] == {
        "revenue_realized_cents": 32750625117,
        "expense_committed_cents": 151605225133,
        "expense_liquidated_cents": 20368294413,
        "expense_paid_cents": 12729375180,
        "budget_surplus_cents": 12382330704,
    }
    assert b2["budget_execution"] == {
        "revenue_realized_cents": 73725583852,
        "expense_committed_cents": 156988651443,
        "expense_liquidated_cents": 52941559688,
        "expense_paid_cents": 45378600706,
        "budget_surplus_cents": 20784024164,
    }
    assert b1["rcl"]["rcl_cents"] == 176906103437
    assert b2["rcl"]["rcl_cents"] == 179379027526
    assert b1["fiscal_results"]["primary_without_rpps_above_line_cents"] == 1436445490
    assert b2["fiscal_results"]["primary_without_rpps_above_line_cents"] == 8558002562
    assert b1["fiscal_results"]["nominal_without_rpps_below_line_cents"] == 17607272866
    assert b2["fiscal_results"]["nominal_without_rpps_below_line_cents"] == 26103602090


def test_partial_constitutional_tracking_is_not_annual_compliance():
    cfg = load(CFG)
    s = series_by_period(cfg)
    assert s["2026-02"]["constitutional_tracking"]["mde_applied_pct_bp"] == 2431
    assert s["2026-04"]["constitutional_tracking"]["mde_applied_pct_bp"] == 2427
    assert s["2026-02"]["constitutional_tracking"]["fundeb_professionals_pct_bp"] == 7703
    assert s["2026-04"]["constitutional_tracking"]["fundeb_professionals_pct_bp"] == 8867
    assert "CONSTITUTIONAL_PERCENT_PARTIAL_PERIOD_NE_ANNUAL_COMPLIANCE" in cfg["guards"]


def test_b1_annex8_is_new_period_and_stages_remain_distinct():
    cfg = load(CFG)
    row = cfg["education_b1_detail"]
    assert row["source_doc_id"] == "DOC-064"
    assert row["fundeb_received_cents"] == 3288218433
    assert row["fundeb_available_resources_cents"] == 3392970541
    assert row["fundeb_expense_committed_cents"] == 11985309856
    assert row["fundeb_expense_liquidated_cents"] == 2532192060
    assert row["fundeb_expense_paid_cents"] == 1236420327
    assert len({row["fundeb_expense_committed_cents"], row["fundeb_expense_liquidated_cents"], row["fundeb_expense_paid_cents"]}) == 3
    assert row["vaar_principal_realized_cents"] == 0
    assert row["vaar_financial_income_realized_cents"] == 901180
    assert "COMMITTED_NE_LIQUIDATED_NE_PAID" in cfg["guards"]


def test_b1_detailed_results_reconcile_exactly_to_annex14():
    cfg = load(CFG)
    s = series_by_period(cfg)["2026-02"]
    d = cfg["fiscal_b1_detail"]
    assert d["primary_result_without_rpps_above_line_cents"] == s["fiscal_results"]["primary_without_rpps_above_line_cents"]
    assert d["nominal_result_without_rpps_below_line_cents"] == s["fiscal_results"]["nominal_without_rpps_below_line_cents"]
    assert d["net_consolidated_debt_at_bimester_cents"] == 9633640055


def test_b2_rcl_reconciles_exactly_to_task229_primary_rgf():
    cfg = load(CFG)
    rgf = load(TASK229)
    b2 = series_by_period(cfg)["2026-04"]["rcl"]
    summary = rgf["domains"]["SIMPLIFIED_PRIMARY_SUMMARY"]
    assert b2["rcl_cents"] == summary["rcl_cents"]
    assert b2["rcl_adjusted_debt_cents"] == summary["rcl_adjusted_debt_cents"]
    assert b2["rcl_adjusted_personnel_cents"] == summary["rcl_adjusted_personnel_cents"]


def test_rests_payable_only_component_match_not_full_statement_equality():
    cfg = load(CFG)
    t188 = load(TASK188)
    obs = {row["observation_key"]: row for row in t188["observations"]}
    s = series_by_period(cfg)

    assert s["2026-02"]["rests_payable_summary"]["executive_processed_balance_cents"] == int(round(float(obs["2026-02:MUNICIPIO_TOTAL"]["processed"]["balance_brl"]) * 100))
    assert s["2026-04"]["rests_payable_summary"]["executive_processed_balance_cents"] == int(round(float(obs["2026-04:MUNICIPIO_TOTAL"]["processed"]["balance_brl"]) * 100))

    assert s["2026-02"]["rests_payable_summary"]["total_balance_cents"] != int(round(float(obs["2026-02:MUNICIPIO_TOTAL"]["total_balance_brl"]) * 100))
    assert s["2026-04"]["rests_payable_summary"]["total_balance_cents"] != int(round(float(obs["2026-04:MUNICIPIO_TOTAL"]["total_balance_brl"]) * 100))
    assert "PARTIAL_COMPONENT_MATCH_NE_FULL_STATEMENT_EQUALITY" in cfg["guards"]


def test_task190_scope_guard_is_preserved():
    cfg = load(CFG)
    t190 = load(TASK190)
    assert t190["contextual_reconciliation"]["rreo_anexo_2_function_education"]["equality_expected"] is False
    assert "RREO_ANEXO8_MDE_NE_ANEXO2_FUNCTION_EDUCATION" in cfg["guards"]


def test_evidence_contract():
    e = load(EVIDENCE)
    assert e["audit"]["document_count"] == 18
    assert e["incremental_value"]["new_b1_cross_domain_position"] is True
    assert e["incremental_value"]["new_b1_mde_fundeb_detail"] is True
    assert e["incremental_value"]["contextual_question_coverage_change"] is False
    assert e["remote_effects"] is False
