from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/education_trial_balance_2025_09.v1.json"


class TestTask224EducationTrialBalance202509(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(CONFIG.read_text(encoding="utf-8"))

    def _assert_stage_identities(self, row: dict) -> None:
        self.assertEqual(row["liquidated_ytd"] + row["to_liquidate"], row["committed_ytd"])
        self.assertEqual(row["committed_ytd"] + row["balance"], row["appropriation"])

    def test_source_identity_and_scope_are_bounded(self) -> None:
        src = self.obj["source"]
        self.assertEqual(src["md_01_3_id"], "DOC-066")
        self.assertEqual(src["logical_id"], "BALANCETE-EDUC-2025-09")
        self.assertEqual(src["reference_month"], "2025-09")
        self.assertEqual(src["pages"], 3)
        self.assertEqual(src["value_pages"], [1, 2])
        self.assertIn("BYTE_HASH_NOT_PROVEN", src["source_identity"])
        self.assertEqual(self.obj["scope"], "SCOPED_EXACT_TOTALS_AND_SELECTED_ELEMENTS_NOT_COMPLETE_LEDGER")

    def test_general_totals_match_source_cents(self) -> None:
        row = self.obj["totals"]["GENERAL_BUDGET_EXPENSE"]
        self.assertEqual(row["liquidated_month"], 3870191633)
        self.assertEqual(row["liquidated_ytd"], 31672643962)
        self.assertEqual(row["committed_ytd"], 35095692920)
        self.assertEqual(row["to_liquidate"], 3423048958)
        self.assertEqual(row["appropriation"], 51988592378)
        self.assertEqual(row["balance"], 16892899458)
        self.assertEqual(row["source_page"], 2)
        self._assert_stage_identities(row)

    def test_all_total_groups_pass_accounting_diagnostics(self) -> None:
        for row in self.obj["totals"].values():
            self._assert_stage_identities(row)

        current = self.obj["totals"]["CURRENT_EXPENSES"]
        capital = self.obj["totals"]["CAPITAL_EXPENSES"]
        general = self.obj["totals"]["GENERAL_BUDGET_EXPENSE"]
        for field in self.obj["column_semantics"]:
            self.assertEqual(current[field] + capital[field], general[field])

    def test_personnel_total_is_exact_and_not_recast_as_free_resource(self) -> None:
        row = self.obj["totals"]["PERSONNEL_AND_SOCIAL_CHARGES"]
        self.assertEqual(row["liquidated_ytd"], 24002178322)
        self.assertEqual(row["committed_ytd"], 24778884684)
        self.assertEqual(row["appropriation"], 36806464821)
        self.assertEqual(row["balance"], 12027580137)
        self.assertIn("BALANCE_NE_SAVINGS_OR_FREE_RESOURCE", self.obj["guards"])
        self.assertIn("NO_WAGE_RAISE_AFFORDABILITY_INFERENCE", self.obj["guards"])

    def test_selected_elements_are_exact_stage_records(self) -> None:
        rows = {r["economic_code"]: r for r in self.obj["selected_elements"]}
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows["3.1.90.04.00"]["liquidated_ytd"], 3160269455)
        self.assertEqual(rows["3.1.90.11.00"]["liquidated_ytd"], 15487737938)
        self.assertEqual(rows["3.3.90.30.00"]["committed_ytd"], 2493394526)
        self.assertEqual(rows["3.3.90.39.00"]["to_liquidate"], 1687932091)
        self.assertEqual(rows["4.4.90.51.00"]["appropriation"], 539497916)
        for row in rows.values():
            self._assert_stage_identities(row)

    def test_semantic_guards_prevent_overclaiming(self) -> None:
        guards = set(self.obj["guards"])
        self.assertIn("PARTIAL_MONTHLY_POSITION_NE_ANNUAL_CLOSING", guards)
        self.assertIn("APPROPRIATION_NE_FREE_CASH", guards)
        self.assertIn("COMMITTED_NE_LIQUIDATED_NE_PAID", guards)
        self.assertIn("NO_EITI_ATTRIBUTION_FROM_EDUCATION_TOTAL", guards)
        self.assertIn("PRIMARY_SOURCE_PRECEDES_MD_01_2_OR_DERIVED_NOTE", guards)

    def test_no_coverage_or_remote_effect_inflation(self) -> None:
        cov = self.obj["canonical_contextual_coverage"]
        self.assertEqual((cov["answerable"], cov["total"]), (38, 38))
        self.assertFalse(cov["changed_by_this_task"])
        self.assertTrue(all(value is False for value in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
