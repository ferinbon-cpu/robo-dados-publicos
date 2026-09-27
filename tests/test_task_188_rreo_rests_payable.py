import json
import unittest
from pathlib import Path

from robo_dados_publicos.accounting.rreo_rests_payable import (
    build_rests_payable_observations,
    validate_contract,
)
from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.observatory_products import build_accounting_ledger
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle

ROOT = Path(__file__).resolve().parents[1]
TASK187 = ROOT / "docs/evidence/TASK_187_TCESP_RICH_ACCOUNTING_LEDGER_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
EVIDENCE = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
GENERATED_AT = "2026-09-06T15:05:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask188RreoRestsPayable(unittest.TestCase):
    def test_contract_and_arithmetic_pass(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["source_count"], 2)
        self.assertEqual(got["observation_count"], 4)
        self.assertEqual(got["tcesp_granular_record_count_historical_observation"], 7425)
        self.assertFalse(got["network"])

    def test_exact_bimonthly_balances_are_preserved(self):
        rows = build_rests_payable_observations()
        by_key = {
            (
                row["event_month"],
                row["rests_payable_status"]["scope_name"],
            ): row
            for row in rows
        }
        feb_total = by_key[(2, "RESTOS A PAGAR (EXCETO INTRAORCAM.) (I)")]
        apr_total = by_key[(4, "RESTOS A PAGAR (EXCETO INTRAORCAM.) (I)")]
        feb_edu = by_key[(2, "SECRETARIA DE EDUCACAO")]
        apr_edu = by_key[(4, "SECRETARIA DE EDUCACAO")]

        self.assertEqual(feb_total["amount_brl"], "85839786.43")
        self.assertEqual(apr_total["amount_brl"], "51053179.39")
        self.assertEqual(feb_edu["amount_brl"], "5358705.13")
        self.assertEqual(apr_edu["amount_brl"], "3010505.55")
        self.assertEqual(
            apr_total["rests_payable_status"]["processed"]["balance_brl"],
            "16476433.49",
        )
        self.assertEqual(
            apr_total["rests_payable_status"]["nonprocessed"]["balance_brl"],
            "34576745.90",
        )

    def test_education_scope_is_hint_not_policy_identity(self):
        rows = build_rests_payable_observations()
        education = [
            row for row in rows
            if row["rests_payable_status"]["scope_name"] == "SECRETARIA DE EDUCACAO"
        ]
        self.assertEqual(len(education), 2)
        self.assertTrue(all("EDUCATION" in row["policy_domain_hints"] for row in education))
        self.assertTrue(all(row["policy_identity_proven"] is False for row in education))
        self.assertTrue(all(row["financial_policy_identity_proven"] is False for row in education))

    def test_rreo_rows_preserve_budget_execution_source_family(self):
        product = build_accounting_ledger(
            build_rests_payable_observations(),
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 4)
        self.assertIn("RESTS_PAYABLE", product["capabilities"])
        self.assertTrue(all(row["source_family"] == "BUDGET_EXECUTION" for row in product["rows"]))
        self.assertTrue(all(
            row["caution"] == "OFFICIAL_RREO_AGGREGATE_NE_GRANULAR_ACCOUNTING_TRANSACTION"
            for row in product["rows"]
        ))

    def test_rests_payable_capability_closes_acc_q3_only(self):
        t187 = json.loads(TASK187.read_text(encoding="utf-8"))
        t186 = json.loads(TASK186.read_text(encoding="utf-8"))
        bundle = build_task184_bundle(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        substantive = {
            k: v for k, v in bundle["products"].items()
            if k != "QUERY_PRODUCT_CATALOG"
        }
        accounting = {
            "product_name": "ACCOUNTING_LEDGER",
            "product_schema": "ACCOUNTING_LEDGER_V1",
            "snapshot_id": "TASK188_CAPABILITY_FIXTURE",
            "content_sha256": "b" * 64,
            "row_count": 39783,
            "generated_at": GENERATED_AT,
            "software_version": SOFTWARE_VERSION,
            "rows": [],
            "capabilities": sorted(set(
                t187["accounting_ledger"]["capabilities"] + ["RESTS_PAYABLE"]
            )),
            "observed_stages": ["COMMITMENT", "LIQUIDATION", "PAYMENT", "REVERSAL", "OTHER_REVIEW"],
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
        products = _with_catalog(
            {**substantive, "ACCOUNTING_LEDGER": accounting, "REVENUE_LEDGER": revenue},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        report = question_answerability(products)
        by_id = {x["question_id"]: x for x in report["questions"]}
        self.assertEqual(
            report["status_counts"],
            {
                "EXPLICIT_GAP": 5,
                "MATERIALIZED_ANSWERABLE": 21,
                "MATERIALIZED_PARTIAL": 12,
            },
        )
        self.assertEqual(by_id["ACC_Q3"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["FIN_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["PLAN_Q3"]["status"], "MATERIALIZED_PARTIAL")


    def test_canonical_evidence_pins_snapshot_and_answerability(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(e["status"], "PASS_REAL_RREO_RESTS_PAYABLE_MATERIALIZED")
        self.assertEqual(e["source"]["materialized_observation_count"], 4)
        self.assertEqual(e["accounting_ledger"]["row_count"], 39783)
        self.assertEqual(e["accounting_ledger"]["snapshot_id"], "64503339d8352a2f61e1ee85")
        self.assertIn("RESTS_PAYABLE", e["accounting_ledger"]["capabilities"])
        self.assertEqual(
            e["answerability"]["after_status_counts"],
            {
                "EXPLICIT_GAP": 5,
                "MATERIALIZED_ANSWERABLE": 21,
                "MATERIALIZED_PARTIAL": 12,
            },
        )
        self.assertEqual(
            e["tcesp_granular_enrichment"]["current_task188_transport_status"],
            "SOURCE_TRANSPORT_UNAVAILABLE_NOT_NO_DATA",
        )
        self.assertFalse(e["tcesp_granular_enrichment"]["raw_payload_currently_custodied"])
        self.assertEqual(e["remote_effects"]["serving"], 0)



if __name__ == "__main__":
    unittest.main()
