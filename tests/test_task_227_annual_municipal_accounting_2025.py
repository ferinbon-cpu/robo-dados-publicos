from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/annual_municipal_accounting_2025.v1.json"


class TestTask227AnnualMunicipalAccounting2025(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.domains = self.obj["semantic_domains"]

    def test_scope_sources_and_identity_boundary(self) -> None:
        self.assertEqual(self.obj["schema"], "ANNUAL_MUNICIPAL_ACCOUNTING_2025_V1")
        self.assertEqual(self.obj["task"], "TASK_227")
        self.assertEqual(self.obj["issue"], 767)
        self.assertEqual(self.obj["scope"]["money_representation"], "INTEGER_CENTS")
        self.assertTrue(self.obj["scope"]["selected_high_value_rows_only"])
        self.assertFalse(self.obj["scope"]["full_document_row_parse_claimed"])
        sources = {row["source_doc_id"]: row for row in self.obj["sources"]}
        self.assertEqual(set(sources), {"DOC-006", "DOC-010", "DOC-017"})
        self.assertEqual(sources["DOC-017"]["pages"], 28)
        self.assertEqual(sources["DOC-010"]["pages"], 2)
        self.assertEqual(sources["DOC-006"]["pages"], 5)
        self.assertTrue(all("BYTE_HASH_NOT_PROVEN" in row["identity"] for row in sources.values()))

    def test_three_semantic_domains_are_not_flattened(self) -> None:
        self.assertEqual(set(self.domains), {"PATRIMONIAL_POSITION", "FINANCIAL_FLOWS", "BUDGET_EXECUTION"})
        self.assertEqual(self.domains["PATRIMONIAL_POSITION"]["source_doc_id"], "DOC-017")
        self.assertEqual(self.domains["FINANCIAL_FLOWS"]["source_doc_id"], "DOC-010")
        self.assertEqual(self.domains["BUDGET_EXECUTION"]["source_doc_id"], "DOC-006")

    def test_patrimonial_source_values_and_safe_identities(self) -> None:
        rows = {r["metric_id"]: r["value_cents"] for r in self.domains["PATRIMONIAL_POSITION"]["rows"]}
        self.assertEqual(rows["TOTAL_ASSETS"], 303751023453)
        self.assertEqual(rows["CASH_AND_CASH_EQUIVALENTS"], 28687982427)
        self.assertEqual(rows["TOTAL_LIABILITIES"], 173772024309)
        self.assertEqual(rows["NET_EQUITY"], 129978999144)
        self.assertEqual(rows["RESULT_OF_YEAR"], -45338084748)
        self.assertEqual(rows["LONG_TERM_PROVISIONS"], 95775161955)
        self.assertEqual(rows["CURRENT_ASSETS"] + rows["NONCURRENT_ASSETS"], rows["TOTAL_ASSETS"])
        self.assertEqual(rows["CURRENT_LIABILITIES"] + rows["NONCURRENT_LIABILITIES"], rows["TOTAL_LIABILITIES"])
        self.assertEqual(rows["TOTAL_LIABILITIES"] + rows["NET_EQUITY"], rows["TOTAL_ASSETS"])
        self.assertNotEqual(rows["TOTAL_ASSETS"], rows["CASH_AND_CASH_EQUIVALENTS"])

    def test_financial_flow_source_values_preserve_education_label(self) -> None:
        rows = {r["metric_id"]: r for r in self.domains["FINANCIAL_FLOWS"]["rows"]}
        self.assertEqual(rows["EDUCATION_LINKED_BUDGET_REVENUE"]["value_cents"], 53033325975)
        self.assertEqual(rows["EDUCATION_LINKED_BUDGET_EXPENSE"]["value_cents"], 44571653248)
        self.assertEqual(rows["TOTAL_BUDGET_REVENUE"]["value_cents"], 122704460870)
        self.assertEqual(rows["TOTAL_BUDGET_EXPENSE"]["value_cents"], 139623117492)
        self.assertEqual(rows["PRIOR_YEAR_CASH_BALANCE"]["value_cents"], 107115280616)
        self.assertEqual(rows["NEXT_YEAR_CASH_BALANCE"]["value_cents"], 123661270045)
        self.assertIn("Educacao", rows["EDUCATION_LINKED_BUDGET_REVENUE"]["source_label"])
        self.assertIn("not silently redefined", self.domains["FINANCIAL_FLOWS"]["semantic_caution"])

    def test_budget_revenue_arithmetic_is_diagnostic_only(self) -> None:
        rows = {r["metric_id"]: r for r in self.domains["BUDGET_EXECUTION"]["revenue_rows"]}
        for row in rows.values():
            self.assertEqual(row["realized_cents"] - row["updated_forecast_cents"], row["balance_cents"])
        for field in ("initial_forecast_cents", "updated_forecast_cents", "realized_cents", "balance_cents"):
            self.assertEqual(rows["CURRENT_REVENUES"][field] + rows["CAPITAL_REVENUES"][field], rows["REVENUE_SUBTOTAL"][field])
        prior = self.domains["BUDGET_EXECUTION"]["other_revenue_rows"][0]
        self.assertEqual(prior["value_cents"], 5454214235)
        self.assertEqual(prior["page"], 2)

    def test_budget_expense_stages_and_identities(self) -> None:
        rows = {r["metric_id"]: r for r in self.domains["BUDGET_EXECUTION"]["expense_rows"]}
        self.assertEqual(rows["EXPENSE_TOTAL_WITH_REFINANCING"]["committed_cents"], 198881918058)
        self.assertEqual(rows["EXPENSE_TOTAL_WITH_REFINANCING"]["liquidated_cents"], 186945017286)
        self.assertEqual(rows["EXPENSE_TOTAL_WITH_REFINANCING"]["paid_cents"], 177693306563)
        for row in rows.values():
            self.assertEqual(row["committed_cents"] + row["appropriation_balance_cents"], row["updated_appropriation_cents"])
            self.assertLessEqual(row["paid_cents"], row["liquidated_cents"])
            self.assertLessEqual(row["liquidated_cents"], row["committed_cents"])
        for field in (
            "initial_appropriation_cents",
            "updated_appropriation_cents",
            "committed_cents",
            "liquidated_cents",
            "paid_cents",
            "appropriation_balance_cents",
        ):
            self.assertEqual(
                rows["EXPENSE_SUBTOTAL"][field] + rows["DEBT_AMORTIZATION_REFINANCING"][field],
                rows["EXPENSE_TOTAL_WITH_REFINANCING"][field],
            )

    def test_guards_block_cross_statement_overclaims(self) -> None:
        guards = set(self.obj["guards"])
        required = {
            "ASSET_NE_CASH",
            "LIABILITY_NE_EXPENDITURE",
            "NET_EQUITY_NE_AVAILABLE_CASH",
            "PATRIMONIAL_RESULT_NE_BUDGET_RESULT",
            "BUDGET_REVENUE_NE_CASH_RECEIPT",
            "BUDGET_EXPENSE_NE_PAID_EXPENSE",
            "COMMITTED_NE_LIQUIDATED_NE_PAID",
            "EDUCACAO_LABEL_IN_BALANCO_FINANCEIRO_NE_MDE_NE_FUNDEB_NE_EITI",
            "EDUCATION_REVENUE_MINUS_EXPENSE_NE_FREE_SURPLUS",
            "ANNUAL_CONSOLIDATED_MUNICIPAL_STATEMENT_NE_EDUCATION_ONLY_LEDGER",
            "NO_CROSS_STATEMENT_ARITHMETIC_WITHOUT_EXPLICIT_ACCOUNTING_IDENTITY",
        }
        self.assertTrue(required.issubset(guards))
        self.assertEqual(self.obj["scope"]["canonical_contextual_coverage"], "38/38_UNCHANGED")
        self.assertTrue(all(value is False for value in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
