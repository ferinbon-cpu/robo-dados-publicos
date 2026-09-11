from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/rgf_2026_q1_primary.v1.json"


class TestTask229Rgf2026Q1PrimaryAuthority(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.domains = self.obj["domains"]

    def test_scope_and_exact_primary_source_set(self) -> None:
        self.assertEqual(self.obj["schema"], "RGF_2026_Q1_PRIMARY_V1")
        self.assertEqual(self.obj["task"], "TASK_229")
        self.assertEqual(self.obj["issue"], 773)
        self.assertEqual(self.obj["classification"], "PRIMARY_SOURCE_AUTHORITY_UPGRADE")
        self.assertFalse(self.obj["scope"]["new_fact_claim"])
        self.assertEqual(self.obj["scope"]["contextual_coverage"], "38/38_UNCHANGED")
        sources = {row["source_doc_id"]: row for row in self.obj["sources"]}
        self.assertEqual(set(sources), {"DOC-042", "DOC-049", "DOC-051", "DOC-054", "DOC-057", "DOC-058"})
        self.assertEqual({row["annex"] for row in sources.values()}, {1, 2, 3, 4, 5, 6})
        self.assertTrue(all(row["direct_primary_recheck"] for row in sources.values()))
        self.assertTrue(all("BYTE_HASH_NOT_PROVEN" in row["identity"] for row in sources.values()))
        self.assertEqual(sources["DOC-057"]["publication_status"], "FORA_DO_PERIODO_DE_PUBLICACAO_SOMENTE_ACOMPANHAMENTO")

    def test_personnel_gross_is_not_lrf_dtp(self) -> None:
        p = self.domains["PERSONNEL_LRF"]
        self.assertEqual(p["gross_personnel_last_12m_cents"], 87174952277)
        self.assertEqual(p["dtp_cents"], 66859452913)
        self.assertNotEqual(p["gross_personnel_last_12m_cents"], p["dtp_cents"])
        self.assertEqual(p["rcl_adjusted_personnel_cents"], 177088538889)
        self.assertEqual(p["dtp_pct_bp"], 3775)
        self.assertEqual(p["alert_limit_pct_bp"], 4860)
        self.assertEqual(p["prudential_limit_pct_bp"], 5130)
        self.assertEqual(p["maximum_limit_pct_bp"], 5400)
        self.assertEqual(p["semantic_guard"], "GROSS_PERSONNEL_EXPENSE_NE_LRF_DTP")

    def test_debt_internal_source_identities(self) -> None:
        d = self.domains["CONSOLIDATED_DEBT"]
        self.assertEqual(d["consolidated_debt_cents"], 35284117881)
        self.assertEqual(d["deductions_cents"], 34146807050)
        self.assertEqual(d["net_consolidated_debt_cents"], 1137310831)
        self.assertEqual(d["consolidated_debt_cents"] - d["deductions_cents"], d["net_consolidated_debt_cents"])
        self.assertEqual(
            d["gross_cash_availability_cents"]
            - d["processed_restos_a_pagar_cents"]
            - d["refundable_deposits_and_linked_values_cents"],
            d["cash_availability_after_obligations_cents"],
        )
        self.assertEqual(
            d["cash_availability_after_obligations_cents"] + d["other_financial_assets_cents"],
            d["deductions_cents"],
        )
        self.assertEqual(d["net_consolidated_debt_pct_bp"], 63)
        self.assertEqual(d["senate_limit_pct_bp"], 12000)

    def test_guarantees_and_credit_operations_preserve_zero_semantics(self) -> None:
        g = self.domains["GUARANTEES"]
        c = self.domains["CREDIT_OPERATIONS"]
        d = self.domains["CONSOLIDATED_DEBT"]
        self.assertEqual(g["guarantees_granted_cents"], 0)
        self.assertEqual(g["senate_limit_pct_bp"], 2200)
        self.assertEqual(c["credit_operations_reference_quadrimester_cents"], 0)
        self.assertEqual(c["credit_operations_year_to_date_cents"], 0)
        self.assertEqual(c["general_limit_pct_bp"], 1600)
        self.assertEqual(c["alert_limit_pct_bp"], 1440)
        self.assertEqual(c["revenue_anticipation_operations_cents"], 0)
        self.assertEqual(c["revenue_anticipation_limit_pct_bp"], 700)
        self.assertGreater(d["net_consolidated_debt_cents"], 0)
        self.assertEqual(c["semantic_guard"], "ZERO_CREDIT_OPERATIONS_NE_ZERO_DEBT")

    def test_annex5_rows_follow_actual_source_columns(self) -> None:
        cash = self.domains["CASH_AVAILABILITY_MONITORING"]
        self.assertEqual(cash["publication_status"], "FORA_DO_PERIODO_DE_PUBLICACAO_SOMENTE_ACOMPANHAMENTO")
        rows = {row["resource_group"]: row for row in cash["rows"]}
        self.assertEqual(set(rows), {"TOTAL_NON_LINKED", "TOTAL_LINKED_EXCEPT_RPPS", "LINKED_EDUCATION", "FUNDEB_TRANSFERS", "TOTAL"})
        for row in rows.values():
            reconstructed = (
                row["gross_cash_cents"]
                - row["prior_liquidated_unpaid_rp_cents"]
                - row["current_liquidated_unpaid_rp_cents"]
                - row["prior_committed_unliquidated_rp_cents"]
                - row["other_financial_obligations_cents"]
                - row["consortium_financial_insufficiency_cents"]
            )
            self.assertEqual(reconstructed, row["liquid_cash_before_current_nonprocessed_rp_cents"])
            self.assertEqual(
                row["liquid_cash_before_current_nonprocessed_rp_cents"] - row["current_committed_unliquidated_rp_cents"],
                row["liquid_cash_after_current_nonprocessed_rp_cents"],
            )
        edu = rows["LINKED_EDUCATION"]
        self.assertEqual(edu["gross_cash_cents"], 4664352024)
        self.assertEqual(edu["prior_liquidated_unpaid_rp_cents"], 61094313)
        self.assertEqual(edu["prior_committed_unliquidated_rp_cents"], 189995337)
        self.assertEqual(edu["other_financial_obligations_cents"], 0)
        self.assertEqual(edu["liquid_cash_after_current_nonprocessed_rp_cents"], 4413262374)
        fundeb = rows["FUNDEB_TRANSFERS"]
        self.assertEqual(fundeb["gross_cash_cents"], 2681179600)
        self.assertEqual(fundeb["liquid_cash_after_current_nonprocessed_rp_cents"], 2681179600)

    def test_detailed_annexes_reconcile_to_primary_summary(self) -> None:
        summary = self.domains["SIMPLIFIED_PRIMARY_SUMMARY"]
        p = self.domains["PERSONNEL_LRF"]
        d = self.domains["CONSOLIDATED_DEBT"]
        g = self.domains["GUARANTEES"]
        c = self.domains["CREDIT_OPERATIONS"]
        self.assertEqual(p["dtp_cents"], summary["dtp_cents"])
        self.assertEqual(p["rcl_adjusted_personnel_cents"], summary["rcl_adjusted_personnel_cents"])
        self.assertEqual(d["net_consolidated_debt_cents"], summary["net_consolidated_debt_cents"])
        self.assertEqual(d["rcl_adjusted_debt_cents"], summary["rcl_adjusted_debt_cents"])
        self.assertEqual(g["guarantees_granted_cents"], summary["guarantees_granted_cents"])
        self.assertEqual(c["credit_operations_year_to_date_cents"], summary["credit_operations_cents"])
        self.assertTrue(all(row["status"] == "EXACT_MATCH" for row in self.obj["cross_annex_reconciliation"]))

    def test_hard_guards_and_no_remote_effects(self) -> None:
        guards = set(self.obj["guards"])
        required = {
            "PRIMARY_SOURCE_UPGRADE_NE_NEW_FACT",
            "GROSS_PERSONNEL_EXPENSE_NE_LRF_DTP",
            "FORMAL_LRF_MARGIN_NE_FREE_CASH",
            "CASH_AVAILABILITY_NE_BUDGET_AUTHORIZATION",
            "LINKED_EDUCATION_CASH_NE_FREE_EDUCATION_MONEY",
            "FUNDEB_CASH_NE_FUNDEB_AVAILABLE_FOR_NEW_SPENDING",
            "RGF_ANEXO5_ACOMPANHAMENTO_NE_FINAL_PUBLISHED_PERIOD",
            "DEBT_HEADROOM_NE_SPENDING_AUTHORIZATION",
            "ZERO_CREDIT_OPERATIONS_NE_ZERO_DEBT",
            "PERCENT_LIMIT_NE_AVAILABLE_PERCENT_TO_SPEND",
            "NO_DOUBLE_COUNT_WITH_MD_01_2_DERIVED_LAYER",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(guards))
        self.assertTrue(all(value is False for value in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
