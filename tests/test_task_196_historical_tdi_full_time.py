import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task194k_miest_class_count_materialization import build_task194k_products
from robo_dados_publicos.analytics.task196_historical_tdi_full_time_overlay import (
    build_task196_products,
    full_time_overlay_rows,
    load_contract,
    tdi_anchor_overlay_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_196_HISTORICAL_TDI_FULL_TIME_0.8.0.json"
GENERATED_AT = "2026-09-07T15:45:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products(*, task196: bool):
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    substantive = {
        k: v for k, v in bundle["products"].items()
        if k not in {"QUERY_PRODUCT_CATALOG", "PLANNING_DOCUMENT_INDEX"}
    }
    planning = build_planning_overlay(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    accounting = {
        "product_name": "ACCOUNTING_LEDGER",
        "product_schema": "ACCOUNTING_LEDGER_V1",
        "snapshot_id": t188["accounting_ledger"]["snapshot_id"],
        "content_sha256": t188["accounting_ledger"]["content_sha256"],
        "row_count": t188["accounting_ledger"]["row_count"],
        "generated_at": GENERATED_AT,
        "software_version": SOFTWARE_VERSION,
        "rows": [],
        "capabilities": t188["accounting_ledger"]["capabilities"],
        "observed_stages": t188["accounting_ledger"]["observed_stages"],
    }
    revenue = {
        "product_name": "REVENUE_LEDGER",
        "product_schema": t186["revenue_ledger"]["product_schema"],
        "snapshot_id": t186["revenue_ledger"]["snapshot_id"],
        "content_sha256": t186["revenue_ledger"]["content_sha256"],
        "row_count": t186["revenue_ledger"]["row_count"],
        "generated_at": GENERATED_AT,
        "software_version": SOFTWARE_VERSION,
        "rows": [],
        "capabilities": t186["revenue_ledger"]["capabilities"],
    }
    overlay = (
        build_task196_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        if task196
        else build_task194k_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
    )
    substantive["SCHOOL_INDICATOR_SERIES"] = overlay["SCHOOL_INDICATOR_SERIES"]
    substantive["FISCAL_SERIES"] = overlay["FISCAL_SERIES"]
    return _with_catalog(
        {
            **substantive,
            "PLANNING_DOCUMENT_INDEX": planning,
            "ACCOUNTING_LEDGER": accounting,
            "REVENUE_LEDGER": revenue,
        },
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )


class TestTask196HistoricalTdiFullTime(unittest.TestCase):
    def test_contract_is_fail_closed_and_hash_honest(self):
        result = validate_contract()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["full_time_periods"], 8)
        self.assertEqual(result["tdi_anchor_periods"], 7)
        cfg = load_contract()
        self.assertIsNone(cfg["file_library_text_evidence"]["sha256"])
        self.assertEqual(cfg["file_library_text_evidence"]["hash_status"], "NOT_AVAILABLE_NOT_INVENTED")

    def test_full_time_series_has_exact_scope_and_values(self):
        rows = full_time_overlay_rows()
        self.assertEqual(len(rows), 8)
        self.assertEqual([r["period"] for r in rows], [str(y) for y in range(2018, 2026)])
        self.assertEqual([r["value"] for r in rows], [11.1,13.2,11.5,9.2,14.9,26.7,30.0,30.7])
        self.assertTrue(all(r["scope_id"] == "3526902:MUNICIPAL:YEARS_INITIAL_ACTIVE_EDITION" for r in rows))
        self.assertIn("2018_77_UNITS_NE_CURRENT_69_FIXED_PANEL", rows[0]["caution"])

    def test_tdi_materializes_only_explicit_anchors(self):
        rows = tdi_anchor_overlay_rows()
        self.assertEqual(
            [(r["period"], r["value"]) for r in rows],
            [("2006",3.4),("2011",0.9),("2012",0.9),("2017",4.0),("2023",1.0),("2024",1.0),("2025",1.0)],
        )
        self.assertTrue(all("NO_INTERPOLATION" in r["caution"] for r in rows))

    def test_products_add_15_rows_and_preserve_fiscal(self):
        before = build_task194k_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        after = build_task196_products(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        self.assertEqual(before["SCHOOL_INDICATOR_SERIES"]["row_count"], 1020)
        self.assertEqual(after["SCHOOL_INDICATOR_SERIES"]["row_count"], 1035)
        self.assertEqual(before["FISCAL_SERIES"]["row_count"], 61)
        self.assertEqual(after["FISCAL_SERIES"]["row_count"], 61)
        self.assertEqual(before["FISCAL_SERIES"]["content_sha256"], after["FISCAL_SERIES"]["content_sha256"])
        self.assertEqual(after["FULL_TIME_SHARE"]["change_pp_2018_2025"], 19.6)
        self.assertFalse(after["TDI"]["complete_annual_table_materialized"])

    def test_exactly_two_questions_move_to_answerable(self):
        before = question_answerability(current_products(task196=False))
        after = question_answerability(current_products(task196=True))
        self.assertEqual(
            before["status_counts"],
            {"EXPLICIT_GAP": 2, "MATERIALIZED_ANSWERABLE": 28, "MATERIALIZED_PARTIAL": 8},
        )
        self.assertEqual(
            after["status_counts"],
            {"EXPLICIT_GAP": 2, "MATERIALIZED_ANSWERABLE": 30, "MATERIALIZED_PARTIAL": 6},
        )
        b = {r["question_id"]: r for r in before["questions"]}
        a = {r["question_id"]: r for r in after["questions"]}
        changed = {qid for qid in b if b[qid]["status"] != a[qid]["status"]}
        self.assertEqual(changed, {"NETWORK_Q2","LEARN_Q3"})
        self.assertEqual(a["NETWORK_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(a["LEARN_Q3"]["status"], "MATERIALIZED_ANSWERABLE")

    def test_evidence_preserves_scope_and_partial_tdi_semantics(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["full_time"]["values_percent"][-1], 30.7)
        self.assertEqual(e["full_time"]["change_pp_2018_2025"], 19.6)
        self.assertFalse(e["tdi"]["complete_annual_table_materialized"])
        self.assertEqual(e["answerability_expected"]["changed_questions"], ["NETWORK_Q2","LEARN_Q3"])
        self.assertEqual(e["remote_effects"]["serving"], 0)


if __name__ == "__main__":
    unittest.main()
