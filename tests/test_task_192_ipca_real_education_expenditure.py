import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task191_annual_education_per_enrollment import build_task191_products
from robo_dados_publicos.analytics.task192_ipca_real_education_expenditure import (
    Task192Stop,
    build_task192_products,
    deflator_factor,
    load_contract,
    nominal_history_overlay_rows,
    real_overlay_rows,
    real_value,
    trend_summary,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_192_IPCA_REAL_EDUCATION_EXPENDITURE_2016_2025_0.8.0.json"
GENERATED_AT = "2026-09-06T20:30:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products(*, task192: bool):
    t188 = json.loads(TASK188.read_text(encoding="utf-8"))
    t186 = json.loads(TASK186.read_text(encoding="utf-8"))
    bundle = build_task184_bundle(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
    substantive = {
        k: v for k, v in bundle["products"].items()
        if k not in {"QUERY_PRODUCT_CATALOG", "PLANNING_DOCUMENT_INDEX"}
    }
    planning = build_planning_overlay(
        generated_at=GENERATED_AT,
        software_version=SOFTWARE_VERSION,
    )
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
    if task192:
        overlay = build_task192_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
    else:
        overlay = build_task191_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
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


class TestTask192IpcaRealEducationExpenditure(unittest.TestCase):
    def test_contract_real_values_and_trend_are_exact(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["base_price_period"], "2025-12")
        self.assertEqual(Decimal(str(deflator_factor(2025))), Decimal("1"))
        self.assertEqual(real_value(2016), Decimal("333866834.92"))
        self.assertEqual(real_value(2024), Decimal("477725620.83"))
        self.assertEqual(real_value(2025), Decimal("463766660.32"))
        self.assertEqual(
            trend_summary(),
            {
                "nominal_2016_to_2025_pct": "115.36",
                "real_2016_to_2025_pct": "38.91",
                "nominal_2024_to_2025_pct": "1.21",
                "real_2024_to_2025_pct": "-2.92",
            },
        )

    def test_overlay_rows_preserve_semantics_and_source_change(self):
        nominal = nominal_history_overlay_rows()
        real = real_overlay_rows()
        self.assertEqual(len(nominal), 9)
        self.assertEqual(len(real), 10)
        self.assertEqual([row["period"] for row in nominal], [str(y) for y in range(2016, 2025)])
        self.assertEqual([row["period"] for row in real], [str(y) for y in range(2016, 2026)])
        self.assertTrue(all(row["metric_id"] == "EDUCATION_EXPENDITURE" for row in nominal))
        self.assertTrue(all(row["metric_id"] == "REAL_EDUCATION_EXPENDITURE" for row in real))
        self.assertTrue(all(row["source_family"] == "SIOPE" for row in real[:-1]))
        self.assertEqual(real[-1]["source_family"], "RREO")
        self.assertEqual(real[-1]["unit"], "BRL_DEC_2025_EQUIVALENT")
        self.assertNotIn("2026", {row["period"] for row in real})

    def test_products_add_19_rows_and_preserve_2026_partial(self):
        products = build_task192_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        school = products["SCHOOL_INDICATOR_SERIES"]
        fiscal = products["FISCAL_SERIES"]
        self.assertEqual(school["row_count"], 1018)
        self.assertEqual(fiscal["row_count"], 61)
        self.assertEqual(fiscal["overlay_scope"]["task192_nominal_history_rows"], 9)
        self.assertEqual(fiscal["overlay_scope"]["task192_real_rows"], 10)
        self.assertFalse(fiscal["overlay_scope"]["annualized_2026"])
        self.assertFalse(fiscal["overlay_scope"]["monthly_weighted_deflation"])
        annual_nominal = [
            row for row in fiscal["rows"]
            if row["metric_id"] == "EDUCATION_EXPENDITURE"
            and row["period"] in {str(y) for y in range(2016, 2026)}
        ]
        annual_real = [
            row for row in fiscal["rows"]
            if row["metric_id"] == "REAL_EDUCATION_EXPENDITURE"
        ]
        self.assertEqual(len(annual_nominal), 10)
        self.assertEqual(len(annual_real), 10)
        current = [
            row for row in fiscal["rows"]
            if row["period"] == "2026-04"
            and row["metric_id"] == "EDUCATION_EXPENDITURE"
        ]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["stage_semantic"], "LIQUIDATED_TO_DATE")
        self.assertEqual(Decimal(str(current[0]["value"])), Decimal("138279835.79"))

    def test_answerability_changes_only_fin_q4(self):
        before = question_answerability(current_products(task192=False))
        after = question_answerability(current_products(task192=True))
        self.assertEqual(
            before["status_counts"],
            {
                "EXPLICIT_GAP": 2,
                "MATERIALIZED_ANSWERABLE": 26,
                "MATERIALIZED_PARTIAL": 10,
            },
        )
        self.assertEqual(
            after["status_counts"],
            {
                "EXPLICIT_GAP": 2,
                "MATERIALIZED_ANSWERABLE": 27,
                "MATERIALIZED_PARTIAL": 9,
            },
        )
        before_by_id = {row["question_id"]: row for row in before["questions"]}
        after_by_id = {row["question_id"]: row for row in after["questions"]}
        changed = {
            qid: (before_by_id[qid]["status"], after_by_id[qid]["status"])
            for qid in before_by_id
            if before_by_id[qid]["status"] != after_by_id[qid]["status"]
        }
        self.assertEqual(
            changed,
            {"FIN_Q4": ("MATERIALIZED_PARTIAL", "MATERIALIZED_ANSWERABLE")},
        )
        self.assertEqual(after_by_id["FIN_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(after_by_id["FIN_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(after_by_id["FIN_Q4"]["missing_or_insufficient_metrics"], [])

    def test_methodological_guards_fail_closed(self):
        obj = load_contract()
        obj["deflator"]["annual_flow_monthly_weighted"] = True
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad_weighting.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task192Stop, "TASK192_FLOW_WEIGHTING"):
                load_contract(path)

        obj = load_contract()
        obj["deflator"]["base_price_period"] = "2024-12"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad_base.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task192Stop, "TASK192_BASE_PRICE_PERIOD"):
                load_contract(path)

    def test_canonical_evidence_is_bounded(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["base_price_period"], "2025-12")
        self.assertFalse(e["methodology"]["monthly_weighted"])
        self.assertFalse(e["methodology"]["annualized_2026"])
        self.assertEqual(e["expected_products"]["fiscal_series_row_count"], 61)
        self.assertEqual(
            e["answerability"]["expected_after_status_counts"],
            {
                "EXPLICIT_GAP": 2,
                "MATERIALIZED_ANSWERABLE": 27,
                "MATERIALIZED_PARTIAL": 9,
            },
        )
        self.assertEqual(e["answerability"]["fin_q4"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(e["global_fiscal_status_must_remain"], "READY_PARTIAL_ONLY")
        self.assertEqual(e["remote_effects"]["serving"], 0)
        self.assertEqual(e["remote_effects"]["publication"], 0)

    def test_runtime_snapshot_probe(self):
        products = build_task192_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        print(
            "TASK192_RUNTIME_SNAPSHOTS="
            + json.dumps(
                {
                    "school_snapshot_id": products["SCHOOL_INDICATOR_SERIES"]["snapshot_id"],
                    "school_content_sha256": products["SCHOOL_INDICATOR_SERIES"]["content_sha256"],
                    "fiscal_snapshot_id": products["FISCAL_SERIES"]["snapshot_id"],
                    "fiscal_content_sha256": products["FISCAL_SERIES"]["content_sha256"],
                    "fiscal_row_count": products["FISCAL_SERIES"]["row_count"],
                    "trend": products["trend"],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
