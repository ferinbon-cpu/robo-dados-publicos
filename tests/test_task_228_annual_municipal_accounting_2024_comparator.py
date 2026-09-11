from __future__ import annotations

import json
import unittest
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_2024 = ROOT / "config/annual_municipal_accounting_2024.v1.json"
CONFIG_2025 = ROOT / "config/annual_municipal_accounting_2025.v1.json"
COMPARISON = ROOT / "config/annual_municipal_accounting_2024_2025_comparison.v1.json"


class TestTask228AnnualMunicipalAccounting2024Comparator(unittest.TestCase):
    def setUp(self) -> None:
        self.y24 = json.loads(CONFIG_2024.read_text(encoding="utf-8"))
        self.y25 = json.loads(CONFIG_2025.read_text(encoding="utf-8"))
        self.cmp = json.loads(COMPARISON.read_text(encoding="utf-8"))

    def test_scope_sources_and_semantic_domains(self) -> None:
        self.assertEqual(self.y24["schema"], "ANNUAL_MUNICIPAL_ACCOUNTING_2024_V1")
        self.assertEqual(self.y24["task"], "TASK_228")
        self.assertEqual(self.y24["issue"], 769)
        self.assertEqual(self.y24["scope"]["price_basis"], "NOMINAL_NOT_DEFLATED")
        self.assertEqual({s["source_doc_id"] for s in self.y24["sources"]}, {"DOC-005", "DOC-009", "DOC-013", "DOC-016"})
        self.assertEqual(set(self.y24["semantic_domains"]), {"PATRIMONIAL_POSITION", "FINANCIAL_FLOWS", "BUDGET_EXECUTION", "PATRIMONIAL_VARIATIONS"})

    def test_2024_patrimonial_safe_identities_and_preserved_mismatch(self) -> None:
        domain = self.y24["semantic_domains"]["PATRIMONIAL_POSITION"]
        rows = {r["metric_id"]: r["value_cents"] for r in domain["rows"]}
        self.assertEqual(rows["CURRENT_ASSETS"] + rows["NONCURRENT_ASSETS"], rows["TOTAL_ASSETS"])
        self.assertEqual(rows["CURRENT_LIABILITIES"] + rows["NONCURRENT_LIABILITIES"], rows["TOTAL_LIABILITIES"])
        self.assertNotEqual(rows["TOTAL_LIABILITIES"] + rows["NET_EQUITY"], rows["TOTAL_ASSETS"])
        self.assertEqual(rows["PASSIVE_PLUS_NET_EQUITY_SIDE_PRINTED_TOTAL"] - rows["TOTAL_ASSETS"], 5282370525)
        self.assertEqual(domain["display_total_discrepancy_cents"], 5282370525)
        self.assertEqual(domain["explicitly_unavailable_qa_identity"], "TOTAL_LIABILITIES + NET_EQUITY = TOTAL_ASSETS")

    def test_dvp_identity_and_result_is_not_forced_to_bp(self) -> None:
        dvp = self.y24["semantic_domains"]["PATRIMONIAL_VARIATIONS"]
        rows = {r["metric_id"]: r["value_cents"] for r in dvp["rows"]}
        self.assertEqual(
            rows["TOTAL_AUGMENTATIVE_PATRIMONIAL_VARIATIONS"] - rows["TOTAL_DIMINUTIVE_PATRIMONIAL_VARIATIONS"],
            rows["DVP_PATRIMONIAL_RESULT"],
        )
        bp = {r["metric_id"]: r["value_cents"] for r in self.y24["semantic_domains"]["PATRIMONIAL_POSITION"]["rows"]}
        self.assertNotEqual(rows["DVP_PATRIMONIAL_RESULT"], bp["RESULT_OF_YEAR_BP_ROW"])
        self.assertEqual(bp["RESULT_OF_YEAR_BP_ROW"] - rows["DVP_PATRIMONIAL_RESULT"], 197126041)

    def test_financial_source_values_and_printed_totals_are_separate(self) -> None:
        rows = {r["metric_id"]: r["value_cents"] for r in self.y24["semantic_domains"]["FINANCIAL_FLOWS"]["rows"]}
        self.assertEqual(rows["EDUCATION_LINKED_BUDGET_REVENUE"], 49368786227)
        self.assertEqual(rows["EDUCATION_LINKED_BUDGET_EXPENSE"], 44614787066)
        self.assertEqual(rows["NEXT_YEAR_CASH_BALANCE"], 111074598490)
        self.assertNotEqual(rows["INGRESS_SIDE_PRINTED_TOTAL"], rows["OUTFLOW_SIDE_PRINTED_TOTAL"])

    def test_2024_budget_internal_identities_and_stages(self) -> None:
        budget = self.y24["semantic_domains"]["BUDGET_EXECUTION"]
        revenue = {r["metric_id"]: r for r in budget["revenue_rows"]}
        for row in revenue.values():
            self.assertEqual(row["realized_cents"] - row["updated_forecast_cents"], row["balance_cents"])
        for field in ("initial_forecast_cents", "updated_forecast_cents", "realized_cents", "balance_cents"):
            self.assertEqual(revenue["CURRENT_REVENUES"][field] + revenue["CAPITAL_REVENUES"][field], revenue["REVENUE_SUBTOTAL"][field])
        expense = {r["metric_id"]: r for r in budget["expense_rows"]}
        for row in expense.values():
            self.assertEqual(row["committed_cents"] + row["appropriation_balance_cents"], row["updated_appropriation_cents"])
            self.assertLessEqual(row["paid_cents"], row["liquidated_cents"])
            self.assertLessEqual(row["liquidated_cents"], row["committed_cents"])
        for field in ("initial_appropriation_cents", "updated_appropriation_cents", "committed_cents", "liquidated_cents", "paid_cents", "appropriation_balance_cents"):
            self.assertEqual(expense["EXPENSE_SUBTOTAL"][field] + expense["DEBT_AMORTIZATION_REFINANCING"][field], expense["EXPENSE_TOTAL_WITH_REFINANCING"][field])

    def test_comparison_rows_reconcile_to_2024_and_2025_sources(self) -> None:
        y24_simple = {}
        y25_simple = {}
        for domain_name in ("PATRIMONIAL_POSITION", "FINANCIAL_FLOWS"):
            y24_simple[domain_name] = {r["metric_id"]: r["value_cents"] for r in self.y24["semantic_domains"][domain_name]["rows"]}
            y25_simple[domain_name] = {r["metric_id"]: r["value_cents"] for r in self.y25["semantic_domains"][domain_name]["rows"]}
        b24 = self.y24["semantic_domains"]["BUDGET_EXECUTION"]
        b25 = self.y25["semantic_domains"]["BUDGET_EXECUTION"]
        b24_rev = {r["metric_id"]: r for r in b24["revenue_rows"]}
        b25_rev = {r["metric_id"]: r for r in b25["revenue_rows"]}
        b24_exp = {r["metric_id"]: r for r in b24["expense_rows"]}
        b25_exp = {r["metric_id"]: r for r in b25["expense_rows"]}
        b24_other = {r["metric_id"]: r for r in b24["other_revenue_rows"]}
        b25_other = {r["metric_id"]: r for r in b25["other_revenue_rows"]}

        for row in self.cmp["rows"]:
            domain = row["semantic_domain"]
            metric = row["metric_id"]
            if domain in y24_simple:
                source24, source25 = y24_simple[domain][metric], y25_simple[domain][metric]
            elif metric == "REVENUE_SUBTOTAL":
                source24, source25 = b24_rev[metric][row["stage"]], b25_rev[metric][row["stage"]]
            elif metric == "EXPENSE_TOTAL_WITH_REFINANCING":
                source24, source25 = b24_exp[metric][row["stage"]], b25_exp[metric][row["stage"]]
            else:
                source24, source25 = b24_other[metric][row["stage"]], b25_other[metric][row["stage"]]
            self.assertEqual(row["value_2024_cents"], source24)
            self.assertEqual(row["value_2025_cents"], source25)
            self.assertEqual(row["nominal_delta_cents"], source25 - source24)
            expected_pct = (Decimal(source25 - source24) / Decimal(source24) * Decimal(100)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            self.assertEqual(Decimal(row["nominal_change_pct_2024_base"]), expected_pct)

    def test_comparison_withholds_unsafe_rows_and_has_strong_guards(self) -> None:
        withheld = {row["metric"] for row in self.cmp["non_comparable_or_withheld"]}
        self.assertTrue({"PATRIMONIAL_RESULT", "NET_EQUITY", "PATRIMONIAL_VARIATIONS", "FINANCIAL_STATEMENT_TOTAL"}.issubset(withheld))
        guards = set(self.y24["guards"]) | set(self.cmp["guards"])
        required = {
            "TOTAL_LIABILITIES_PLUS_NET_EQUITY_NE_ASSERTED_AS_TOTAL_ASSETS_2024",
            "DVP_PATRIMONIAL_RESULT_NE_BALANCO_PATRIMONIAL_RESULT_ROW_WITHOUT_RECONCILIATION",
            "FINANCIAL_INGRESS_TOTAL_NE_FORCED_EQUAL_OUTFLOW_TOTAL",
            "NOMINAL_DELTA_NE_REAL_CHANGE_WITHOUT_DEFLATOR",
            "EDUCACAO_SOURCE_LABEL_NE_MDE_FUNDEB_EITI",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(guards))
        self.assertEqual(self.cmp["price_basis"], "NOMINAL_NOT_DEFLATED")
        self.assertEqual(self.y24["scope"]["canonical_contextual_coverage"], "38/38_UNCHANGED")
        self.assertTrue(all(value is False for value in self.y24["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
