import json
import unittest
from decimal import Decimal
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import build_planning_overlay
from robo_dados_publicos.analytics.task190_rreo_education_spending import (
    build_fiscal_overlay,
    overlay_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_190_RREO_EDUCATION_SPENDING_FISCAL_SERIES_0.8.0.json"
GENERATED_AT = "2026-09-06T15:30:00+00:00"
SOFTWARE_VERSION = "0.8.0"


def current_products(*, task190: bool):
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
    if task190:
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


class TestTask190RreoEducationSpending(unittest.TestCase):
    def test_contract_stage_semantics_are_exact(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["metric_count"], 3)
        self.assertEqual(got["canonical_spending_metric"], "EDUCATION_EXPENDITURE")
        self.assertEqual(got["canonical_stage_semantic"], "LIQUIDATED_TO_DATE")
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])

    def test_exact_rreo_stage_values_are_preserved(self):
        rows = {row["metric_id"]: row for row in overlay_rows()}
        self.assertEqual(
            Decimal(str(rows["EDUCATION_COMMITTED_EXPENDITURE"]["value"])),
            Decimal("319000956.31"),
        )
        self.assertEqual(
            Decimal(str(rows["EDUCATION_EXPENDITURE"]["value"])),
            Decimal("138279835.79"),
        )
        self.assertEqual(
            Decimal(str(rows["EDUCATION_PAID_EXPENDITURE"]["value"])),
            Decimal("104176664.15"),
        )
        self.assertEqual(
            rows["EDUCATION_EXPENDITURE"]["stage_semantic"],
            "LIQUIDATED_TO_DATE",
        )
        self.assertEqual(
            rows["EDUCATION_PAID_EXPENDITURE"]["stage_semantic"],
            "PAID_TO_DATE",
        )
        self.assertTrue(all(row["source_family"] == "RREO" for row in rows.values()))
        self.assertTrue(all(
            row["source_sha256"] == "539144ae70edbcb3ca4662b9460c869ad4b21a6e6b027f3f3c332a0372e08361"
            for row in rows.values()
        ))

    def test_fiscal_overlay_adds_three_rows_without_per_student_or_real_claim(self):
        product = build_fiscal_overlay(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 41)
        ids = {row["metric_id"] for row in product["rows"]}
        self.assertIn("EDUCATION_COMMITTED_EXPENDITURE", ids)
        self.assertIn("EDUCATION_EXPENDITURE", ids)
        self.assertIn("EDUCATION_PAID_EXPENDITURE", ids)
        self.assertFalse(product["overlay_scope"]["annual_final"])
        self.assertFalse(product["overlay_scope"]["real_terms"])
        self.assertFalse(product["overlay_scope"]["per_student_metric_materialized"])
        self.assertFalse(product["overlay_scope"]["tcesp_equality_claim"])

    def test_answerability_transition_is_exact_and_semantically_bounded(self):
        before = question_answerability(current_products(task190=False))
        after = question_answerability(current_products(task190=True))
        self.assertEqual(
            before["status_counts"],
            {
                "EXPLICIT_GAP": 5,
                "MATERIALIZED_ANSWERABLE": 24,
                "MATERIALIZED_PARTIAL": 9,
            },
        )
        self.assertEqual(
            after["status_counts"],
            {
                "EXPLICIT_GAP": 3,
                "MATERIALIZED_ANSWERABLE": 25,
                "MATERIALIZED_PARTIAL": 10,
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
            {
                "FIN_Q1": ("MATERIALIZED_PARTIAL", "MATERIALIZED_ANSWERABLE"),
                "FIN_Q2": ("EXPLICIT_GAP", "MATERIALIZED_PARTIAL"),
                "FIN_Q4": ("EXPLICIT_GAP", "MATERIALIZED_PARTIAL"),
            },
        )
        self.assertEqual(after_by_id["FIN_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertIn(
            "BASIC_EDUCATION_ENROLLMENT",
            after_by_id["FIN_Q2"]["missing_or_insufficient_metrics"],
        )
        self.assertIn(
            "REAL_EDUCATION_EXPENDITURE",
            after_by_id["FIN_Q4"]["missing_or_insufficient_metrics"],
        )


    def test_canonical_evidence_pins_snapshot_and_safety_scope(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["status"], "PASS_OFFICIAL_RREO_EDUCATION_SPENDING_MATERIALIZED")
        self.assertEqual(e["fiscal_series"]["row_count"], 41)
        self.assertEqual(e["fiscal_series"]["snapshot_id"], "e130605546356808bd11800e")
        self.assertEqual(
            e["fiscal_series"]["content_sha256"],
            "e130605546356808bd11800e6cd7755e3d5d3b47a61e334474b35e4bd0a3dadc",
        )
        self.assertEqual(
            e["fiscal_series"]["json_sha256"],
            "616634a2b82ba511589f4a2977b68f0a64cc91e8601a4608da2c4917b91c4fce",
        )
        self.assertEqual(
            e["fiscal_series"]["gzip_sha256"],
            "7684de78c3b205524b3593b74184be170511d3f178e63810ad97f0d90113423a",
        )
        self.assertFalse(e["enrollment_candidate"]["materialized_in_task190"])
        self.assertTrue(e["enrollment_candidate"]["row_sum_verified"])
        self.assertEqual(e["enrollment_candidate"]["basic_education_enrollment_2025"], 22788)
        self.assertEqual(e["remote_effects"]["serving"], 0)
        self.assertEqual(e["remote_effects"]["publication"], 0)



if __name__ == "__main__":
    unittest.main()
