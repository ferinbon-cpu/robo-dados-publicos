import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task190_rreo_education_spending import build_fiscal_overlay
from robo_dados_publicos.analytics.task191_annual_education_per_enrollment import (
    Task191Stop,
    annual_fiscal_overlay_row,
    build_task191_products,
    derive_spending_per_enrollment,
    load_contract,
    school_overlay_row,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_191_ANNUAL_EDUCATION_PER_ENROLLMENT_2025_0.8.0.json"
GENERATED_AT = "2026-09-06T16:20:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products(*, task191: bool):
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
    if task191:
        overlay = build_task191_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        substantive["SCHOOL_INDICATOR_SERIES"] = overlay["SCHOOL_INDICATOR_SERIES"]
        substantive["FISCAL_SERIES"] = overlay["FISCAL_SERIES"]
    else:
        substantive["FISCAL_SERIES"] = build_fiscal_overlay(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
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


class TestTask191AnnualEducationPerEnrollment(unittest.TestCase):
    def test_contract_and_ratio_are_exact(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["period"], "2025")
        self.assertEqual(Decimal(got["annual_spending_brl"]), Decimal("463766660.32"))
        self.assertEqual(got["enrollment"], 22788)
        self.assertEqual(Decimal(got["spending_per_enrollment_brl"]), Decimal("20351.35"))

        derived = derive_spending_per_enrollment()
        self.assertEqual(derived["value"], "20351.35")
        self.assertTrue(derived["same_year_verified"])
        self.assertFalse(derived["individual_student_cost_claim"])

    def test_rows_preserve_product_semantics(self):
        school = school_overlay_row()
        fiscal = annual_fiscal_overlay_row()
        self.assertEqual(school["indicator_id"], "BASIC_EDUCATION_ENROLLMENT")
        self.assertEqual(school["period"], "2025")
        self.assertEqual(school["value"], 22788)
        self.assertEqual(school["source_family"], "CENSO_ESCOLAR")
        self.assertEqual(fiscal["metric_id"], "EDUCATION_EXPENDITURE")
        self.assertEqual(fiscal["period"], "2025")
        self.assertEqual(Decimal(str(fiscal["value"])), Decimal("463766660.32"))
        self.assertEqual(fiscal["stage_semantic"], "COMMITTED_FINAL_BIMESTER")
        self.assertEqual(fiscal["source_family"], "RREO")

    def test_materialized_products_add_exactly_two_source_rows(self):
        products = build_task191_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        school = products["SCHOOL_INDICATOR_SERIES"]
        fiscal = products["FISCAL_SERIES"]
        self.assertEqual(school["row_count"], 1018)
        self.assertEqual(fiscal["row_count"], 42)
        self.assertEqual(school["overlay_scope"]["task191_rows"], 1)
        self.assertEqual(fiscal["overlay_scope"]["task190_rows"], 3)
        self.assertEqual(fiscal["overlay_scope"]["task191_rows"], 1)
        self.assertEqual(
            fiscal["overlay_scope"]["current_2026_canonical_stage_preserved"],
            "LIQUIDATED_TO_DATE",
        )
        rows_2026 = [
            row for row in fiscal["rows"]
            if row["period"] == "2026-04" and row["metric_id"] == "EDUCATION_EXPENDITURE"
        ]
        self.assertEqual(len(rows_2026), 1)
        self.assertEqual(rows_2026[0]["stage_semantic"], "LIQUIDATED_TO_DATE")
        self.assertEqual(Decimal(str(rows_2026[0]["value"])), Decimal("138279835.79"))

    def test_answerability_changes_only_fin_q2(self):
        before = question_answerability(current_products(task191=False))
        after = question_answerability(current_products(task191=True))
        self.assertEqual(
            before["status_counts"],
            {
                "EXPLICIT_GAP": 3,
                "MATERIALIZED_ANSWERABLE": 25,
                "MATERIALIZED_PARTIAL": 10,
            },
        )
        self.assertEqual(
            after["status_counts"],
            {
                "EXPLICIT_GAP": 3,
                "MATERIALIZED_ANSWERABLE": 26,
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
            {"FIN_Q2": ("MATERIALIZED_PARTIAL", "MATERIALIZED_ANSWERABLE")},
        )
        self.assertEqual(after_by_id["FIN_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(after_by_id["FIN_Q4"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(after_by_id["FIN_Q2"]["missing_or_insufficient_metrics"], [])

    def test_period_mismatch_fails_closed(self):
        obj = load_contract()
        obj["enrollment_source"]["period"] = "2024"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(Task191Stop, "TASK191_PERIOD_ALIGNMENT"):
                load_contract(path)

    def test_canonical_evidence_is_semantically_bounded(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["period"], "2025")
        self.assertEqual(e["derived"]["value"], "20351.35")
        self.assertFalse(e["derived"]["individual_student_cost_claim"])
        self.assertEqual(e["expected_products"]["school_indicator_series_row_count"], 1018)
        self.assertEqual(e["expected_products"]["fiscal_series_row_count"], 42)
        self.assertEqual(
            e["answerability"]["expected_after_status_counts"],
            {
                "EXPLICIT_GAP": 3,
                "MATERIALIZED_ANSWERABLE": 26,
                "MATERIALIZED_PARTIAL": 9,
            },
        )
        self.assertEqual(e["answerability"]["fin_q4_must_remain"], "MATERIALIZED_PARTIAL")
        self.assertEqual(e["remote_effects"]["serving"], 0)
        self.assertEqual(e["remote_effects"]["publication"], 0)

    def test_runtime_snapshot_probe(self):
        products = build_task191_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        print(
            "TASK191_RUNTIME_SNAPSHOTS="
            + json.dumps(
                {
                    "school_snapshot_id": products["SCHOOL_INDICATOR_SERIES"]["snapshot_id"],
                    "school_content_sha256": products["SCHOOL_INDICATOR_SERIES"]["content_sha256"],
                    "fiscal_snapshot_id": products["FISCAL_SERIES"]["snapshot_id"],
                    "fiscal_content_sha256": products["FISCAL_SERIES"]["content_sha256"],
                    "ratio": products["derived"]["value"],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
