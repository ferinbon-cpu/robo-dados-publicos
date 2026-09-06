import json
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle
from robo_dados_publicos.analytics.task189_loa_substantive_overlay import (
    build_planning_overlay,
    overlay_rows,
    validate_contract,
)

ROOT = Path(__file__).resolve().parents[1]
TASK188 = ROOT / "docs/evidence/TASK_188_RREO_RESTS_PAYABLE_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
GENERATED_AT = "2026-09-06T15:12:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask189LoaSubstantiveOverlay(unittest.TestCase):
    def test_contract_preserves_scoped_promotion_guards(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["segment_count"], 2)
        self.assertFalse(got["complete_loa_parse_claim"])
        self.assertEqual(got["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])

    def test_two_primary_substantive_loa_segments_are_exact(self):
        rows = overlay_rows()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["document_type"] == "LOA" for row in rows))
        self.assertTrue(all(row["evidence_role"] == "PRIMARY_SUBSTANTIVE" for row in rows))
        self.assertTrue(all(row["source_family"] == "LOA" for row in rows))
        self.assertTrue(all(
            row["source_sha256"] == "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
            for row in rows
        ))
        by_action = {row["budget_authorization"]["action_code"]: row for row in rows}
        transport = by_action["12.362.2001.2690"]["budget_authorization"]
        food = by_action["12.306.2001.2720"]["budget_authorization"]
        self.assertEqual(transport["appropriation_brl"], "6152000.00")
        self.assertEqual(transport["funding_sources_brl"]["01_TESOURO"], "943000.00")
        self.assertEqual(food["appropriation_brl"], "28000000.00")
        self.assertEqual(
            food["funding_sources_brl"]["05_TRANSFERENCIAS_E_CONVENIOS_FEDERAIS_VINCULADOS"],
            "19320000.00",
        )
        self.assertFalse(transport["eiti_specific"])
        self.assertFalse(food["eiti_specific"])

    def test_planning_overlay_preserves_task184_metadata_row_and_adds_substantive_loa(self):
        product = build_planning_overlay(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 9)
        loa = [row for row in product["rows"] if row["document_type"] == "LOA"]
        self.assertEqual(len(loa), 3)
        self.assertEqual(
            sum(row["evidence_role"] == "PRIMARY_METADATA_ONLY" for row in loa),
            1,
        )
        self.assertEqual(
            sum(row["evidence_role"] == "PRIMARY_SUBSTANTIVE" for row in loa),
            2,
        )
        self.assertFalse(product["overlay_scope"]["complete_loa_parse_claim"])
        self.assertFalse(product["overlay_scope"]["accounting_execution_proven_by_loa"])
        self.assertEqual(
            product["overlay_scope"]["eiti_financial_identity"],
            "EVIDENCIA_INSUFICIENTE",
        )

    def test_plan_q3_closes_only_when_substantive_loa_and_real_accounting_are_combined(self):
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
        products = _with_catalog(
            {
                **substantive,
                "PLANNING_DOCUMENT_INDEX": planning,
                "ACCOUNTING_LEDGER": accounting,
                "REVENUE_LEDGER": revenue,
            },
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        report = question_answerability(products)
        by_id = {row["question_id"]: row for row in report["questions"]}
        self.assertEqual(
            report["status_counts"],
            {
                "EXPLICIT_GAP": 5,
                "MATERIALIZED_ANSWERABLE": 22,
                "MATERIALIZED_PARTIAL": 11,
            },
        )
        self.assertEqual(by_id["PLAN_Q3"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["FIN_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["ACC_Q3"]["status"], "MATERIALIZED_ANSWERABLE")


if __name__ == "__main__":
    unittest.main()
