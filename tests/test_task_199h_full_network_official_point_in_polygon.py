from __future__ import annotations

import unittest

from robo_dados_publicos.analytics.task199h_full_network_official_point_in_polygon import (
    build_task199h_territory_profile,
    load_contract,
    territory_rows,
    validate_contract,
)


class Task199HFullNetworkTests(unittest.TestCase):
    def test_contract_closes_exactly_five_held_schools(self):
        obj = load_contract()
        self.assertEqual(obj["scope"]["before_strong_links"], 64)
        self.assertEqual(obj["scope"]["after_strong_links"], 69)
        self.assertTrue(obj["scope"]["full_network"])
        self.assertEqual(len(obj["promotions"]), 5)
        self.assertEqual(
            {x["sector_id"] for x in obj["promotions"]},
            {
                "352690205000447",
                "352690205000913",
                "352690205000850",
                "352690205000593",
                "352690205000232",
            },
        )

    def test_official_geometry_identity_is_pinned(self):
        obj = load_contract()
        src = obj["sources"]["ibge_sector_geometry"]
        self.assertEqual(src["bytes"], 182128640)
        self.assertEqual(src["limeira_sector_rows"], 735)
        self.assertEqual(
            src["sha256"],
            "07affc966f82292d6f9a359adccc49e69ed55d2075936ef6d1e9c346b29a04bc",
        )
        self.assertFalse(src["raw_persisted"])
        self.assertTrue(obj["point_in_polygon"]["all_unique"])
        self.assertTrue(obj["point_in_polygon"]["all_interior_not_boundary"])

    def test_theresa_main_unit_and_neusa_conflict_are_preserved(self):
        obj = load_contract()
        theresa = next(x for x in obj["promotions"] if x["codigo_inep"] == "35241885")
        self.assertEqual(theresa["geoportal_gid"], 80)
        self.assertEqual(theresa["extension_excluded"]["geoportal_gid"], 38)
        neusa = next(x for x in obj["promotions"] if x["codigo_inep"] == "35099569")
        self.assertIn("MARIO_ALVES_FERRAZ_185", neusa["address_conflict_preserved"])

    def test_full_network_rows_do_not_turn_source_x_into_zero(self):
        rows = territory_rows()
        self.assertEqual(len(rows), 284)
        linked = {
            r["school_code"]
            for r in rows
            if r.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"
        }
        self.assertEqual(len(linked), 69)
        mauricio = [r for r in rows if r.get("school_code") == "35286229"]
        self.assertEqual(len(mauricio), 1)
        self.assertEqual(mauricio[0]["metric_id"], "SECTOR_POPULATION")
        self.assertEqual(mauricio[0]["value"], 4.0)
        self.assertFalse(any("INCOME" in str(r["metric_id"]) for r in mauricio))

    def test_four_numeric_new_income_percentiles_are_pinned(self):
        obj = load_contract()
        observed = {
            x["codigo_inep"]: x.get("V06004_sector_percentile_unweighted")
            for x in obj["promotions"]
            if x.get("income_status") != "SOURCE_EXPLICIT_X"
        }
        self.assertEqual(
            observed,
            {
                "35208437": 45.5,
                "35004773": 0.6,
                "35099569": 15.3,
                "35241885": 47.2,
            },
        )

    def test_product_exposes_full_network_but_explicit_income_missingness(self):
        product = build_task199h_territory_profile(
            generated_at="2026-09-11T23:30:00+00:00",
            software_version="0.8.0",
        )
        self.assertEqual(product["row_count"], 284)
        self.assertIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", product["capabilities"])
        self.assertIn("SCHOOL_TO_SECTOR_LINK_COVERAGE_69_OF_69", product["capabilities"])
        self.assertIn("SECTOR_INCOME_MISSINGNESS_EXPLICIT", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_PARTIAL", product["capabilities"])

    def test_validation_is_terminal_full_network(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["strong_school_links"], 69)
        self.assertEqual(got["held_school_links"], 0)
        self.assertEqual(got["coverage_rate"], 1.0)
        self.assertTrue(got["full_network_school_link"])
        self.assertEqual(got["schools_with_numeric_income_context"], 68)
        self.assertEqual(got["schools_with_explicit_sector_income_missingness"], 1)


if __name__ == "__main__":
    unittest.main()
