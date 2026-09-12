from copy import deepcopy
import unittest

from robo_dados_publicos.analytics.current_observatory_bundle import build_current_bundle
from robo_dados_publicos.analytics.current_territory import (
    build_current_territory_profile, coverage_context, coverage_fact, income_missingness_facts,
)
from robo_dados_publicos.analytics.task202_equity_missingness_aware_gate import build_task202_territory_profile
from robo_dados_publicos.analytics.observatory_query_serving import validate_product_snapshot
from robo_dados_publicos.productization.safe_local_mixed_execution import execute_contextual_query_v4

KW = dict(generated_at="2026-09-12T03:00:00+00:00", software_version="0.8.0")


class CurrentTerritoryIntegrationTests(unittest.TestCase):
    def test_current_bundle_catalog_and_answerability_share_latest_territory(self):
        bundle = build_current_bundle(**KW)
        territory = bundle["products"]["TERRITORY_PROFILE"]
        self.assertEqual(territory["row_count"], 284)
        self.assertEqual(coverage_context(territory)["strong_links"], 69)
        self.assertEqual(bundle["answerability"]["status_counts"], {"MATERIALIZED_ANSWERABLE": 38})
        catalog = next(r for r in bundle["products"]["QUERY_PRODUCT_CATALOG"]["rows"] if r["product_name"] == "TERRITORY_PROFILE")
        self.assertEqual(catalog["row_count"], 284)
        self.assertEqual(validate_product_snapshot(territory)["status"], "PASS")

    def test_historical_partial_snapshot_keeps_its_own_coverage(self):
        old = build_task202_territory_profile(**KW)
        self.assertEqual(old["row_count"], 267)
        self.assertIn("64/69", coverage_fact(old)["text"])
        self.assertEqual(coverage_context(old)["held"], 5)
        self.assertFalse(coverage_context(old)["full_network"])

    def test_corrupted_rows_and_false_full_capability_fail_closed(self):
        product = build_current_territory_profile(**KW)
        altered = deepcopy(product)
        altered["rows"].pop()
        with self.assertRaises(RuntimeError):
            coverage_context(altered)
        old = build_task202_territory_profile(**KW)
        old["capabilities"].append("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK")
        with self.assertRaisesRegex(ValueError, "FULL_CAPABILITY_WITH_PARTIAL_ROWS"):
            coverage_context(old)

    def test_explicit_x_preserves_geography_without_numeric_income(self):
        product = build_current_territory_profile(**KW)
        coverage = coverage_context(product)
        self.assertEqual(coverage["numeric_income_schools"], 68)
        self.assertEqual(coverage["explicit_income_missingness_codes"], ["35286229"])
        missing = income_missingness_facts(product, "35286229")
        self.assertEqual(missing[0]["status"], "SOURCE_EXPLICIT_X")
        self.assertIsNone(missing[0]["value"])
        rows = [r for r in product["rows"] if r.get("school_code") == "35286229"]
        self.assertEqual([r["metric_id"] for r in rows], ["SECTOR_POPULATION"])

    def test_contextual_network_answer_uses_current_coverage(self):
        answer = execute_contextual_query_v4("contexto socioeconomico do territorio de Limeira", **KW)
        self.assertEqual(answer["state"], "ANSWERED_CONTEXTUALLY")
        coverage = next(r for r in answer["NUMBER_OR_FACT"] if r["kind"] == "TERRITORY_LINK_COVERAGE")
        self.assertEqual(coverage["strong_school_links"], 69)
        self.assertEqual(coverage["held"], 0)
        self.assertTrue(coverage["full_network_link"])
        self.assertIn("69/69", coverage["text"])
        self.assertNotIn("PARTIAL_64_OF_69_SCHOOL_LINK_COVERAGE", answer["CAUTION_OR_LIMIT"])

    def test_previously_held_school_now_uses_approved_exact_sector(self):
        answer = execute_contextual_query_v4("contexto socioeconomico do territorio do Ismael Pereira Lago", **KW)
        self.assertEqual(answer["state"], "ANSWERED_CONTEXTUALLY")
        rows = [r for r in answer["NUMBER_OR_FACT"] if r["kind"] == "TERRITORY_METRIC"]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r["school_code"] == "35208437" for r in rows))
        self.assertEqual(answer["TIME_REFERENCE"], ["2022"])


if __name__ == "__main__":
    unittest.main()
