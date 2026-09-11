import copy
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.task199h_public_geopixel_point_in_polygon import (
    Task199HStop,
    build_task199h_territory_profile,
    held_after_task199h,
    load_contract,
    territory_rows,
    validate_contract,
)
from robo_dados_publicos.analytics.task202_equity_missingness_aware_gate import (
    current_question_answerability_v4,
)
from tests.test_task_201b_inep_workforce_materialization import (
    GENERATED_AT,
    SOFTWARE_VERSION,
    full_products,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task199h_public_geopixel_point_in_polygon.v1.json"


class TestTask199HPublicGeopixelPointInPolygon(unittest.TestCase):
    def test_contract_closes_69_of_69_with_zero_held(self):
        report = validate_contract()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["strong_school_links"], 69)
        self.assertEqual(report["held_school_links"], 0)
        self.assertEqual(report["coverage_rate"], 1.0)
        self.assertTrue(report["full_network_school_link"])
        self.assertEqual(held_after_task199h(), [])
        self.assertEqual(
            set(report["promotion_codes"]),
            {"35208437", "35286229", "35004773", "35099569", "35241885"},
        )

    def test_product_has_284_rows_69_schools_and_full_network_capability(self):
        product = build_task199h_territory_profile(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 284)
        self.assertIn("SCHOOL_TO_SECTOR_LINK_FULL_NETWORK", product["capabilities"])
        self.assertIn("SCHOOL_TO_SECTOR_LINK_COVERAGE_69_OF_69", product["capabilities"])
        self.assertIn("SECTOR_INCOME_MISSINGNESS_EXPLICIT", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_PARTIAL", product["capabilities"])
        self.assertNotIn("SCHOOL_TO_SECTOR_LINK_COVERAGE_64_OF_69", product["capabilities"])
        codes = {
            row["school_code"]
            for row in product["rows"]
            if row.get("geo_level") == "SCHOOL_LOCATION_CENSUS_SECTOR"
        }
        self.assertEqual(len(codes), 69)

    def test_exact_final_five_sector_links_are_pinned(self):
        rows = territory_rows()
        expected = {
            "35208437": "352690205000447",
            "35286229": "352690205000913",
            "35004773": "352690205000850",
            "35099569": "352690205000593",
            "35241885": "352690205000232",
        }
        for code, sector in expected.items():
            found = {
                row["sector_id"]
                for row in rows
                if row.get("school_code") == code
            }
            self.assertEqual(found, {sector}, code)

    def test_exact_new_numeric_metrics_and_percentiles(self):
        rows = territory_rows()
        by_key = {
            (row.get("school_code"), row.get("metric_id")): row.get("value")
            for row in rows
            if row.get("school_code") in {"35208437", "35004773", "35099569", "35241885"}
        }
        expected = {
            ("35208437", "SECTOR_POPULATION"): 481.0,
            ("35208437", "SECTOR_RESPONSIBLE_INCOME_MEAN"): 2701.31,
            ("35208437", "SECTOR_RESPONSIBLE_INCOME_MEDIAN"): 2000.0,
            ("35208437", "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE"): 45.5,
            ("35004773", "SECTOR_POPULATION"): 569.0,
            ("35004773", "SECTOR_RESPONSIBLE_INCOME_MEAN"): 1292.38,
            ("35004773", "SECTOR_RESPONSIBLE_INCOME_MEDIAN"): 1280.0,
            ("35004773", "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE"): 0.6,
            ("35099569", "SECTOR_POPULATION"): 559.0,
            ("35099569", "SECTOR_RESPONSIBLE_INCOME_MEAN"): 2058.32,
            ("35099569", "SECTOR_RESPONSIBLE_INCOME_MEDIAN"): 1500.0,
            ("35099569", "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE"): 15.3,
            ("35241885", "SECTOR_POPULATION"): 565.0,
            ("35241885", "SECTOR_RESPONSIBLE_INCOME_MEAN"): 2743.13,
            ("35241885", "SECTOR_RESPONSIBLE_INCOME_MEDIAN"): 2450.0,
            ("35241885", "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE"): 47.2,
        }
        self.assertEqual(by_key, expected)

    def test_mauricio_official_x_is_missing_not_zero(self):
        rows = [row for row in territory_rows() if row.get("school_code") == "35286229"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["metric_id"], "SECTOR_POPULATION")
        self.assertEqual(rows[0]["value"], 4.0)
        self.assertIn("OFFICIAL_SECTOR_INCOME_X_MISSING_NE_ZERO", rows[0]["caution"])
        contract = load_contract()
        mauricio = next(row for row in contract["promotions"] if row["codigo_inep"] == "35286229")
        self.assertEqual(mauricio["income"]["status"], "OFFICIAL_X_MISSING")
        self.assertTrue(all(mauricio["income"][f"V0600{i}"] == "X" for i in range(1, 7)))

    def test_neusa_conflict_and_theresa_extension_remain_explicit(self):
        contract = load_contract()
        neusa = next(row for row in contract["promotions"] if row["codigo_inep"] == "35099569")
        self.assertIn("MARIO_ALVES_FERRAZ_185", neusa["conflict_preserved"])
        self.assertIn("OLIVIA_SACCO_IAQUINTA_SN", neusa["conflict_preserved"])
        theresa = next(row for row in contract["promotions"] if row["codigo_inep"] == "35241885")
        self.assertEqual(theresa["geoportal"]["gid"], 80)
        self.assertEqual(theresa["extension_excluded"]["gid"], 38)
        self.assertIn("Extensão", theresa["extension_excluded"]["returned_name"])
        self.assertEqual(theresa["extension_excluded"]["reason"], "EXPLICIT_EXTENSION_NOT_MAIN_UNIT")

    def test_full_network_product_preserves_38_of_38_answerability(self):
        products = full_products(with_task201b=True)
        products["TERRITORY_PROFILE"] = build_task199h_territory_profile(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        report = current_question_answerability_v4(products)
        self.assertEqual(report["status_counts"], {"MATERIALIZED_ANSWERABLE": 38})
        equity = {row["question_id"]: row for row in report["questions"]}["EQUITY_Q1"]
        self.assertEqual(equity["status"], "MATERIALIZED_ANSWERABLE")

    def test_contract_fails_closed_on_geography_identity_or_missingness_drift(self):
        original = json.loads(CONFIG.read_text(encoding="utf-8"))
        mutations = []

        bad_hash = copy.deepcopy(original)
        bad_hash["sources"]["ibge_sector_geometry"]["sha256"] = "0" * 64
        mutations.append(bad_hash)

        multiple = copy.deepcopy(original)
        multiple["promotions"][0]["point_in_polygon"]["match_count"] = 2
        mutations.append(multiple)

        boundary = copy.deepcopy(original)
        boundary["promotions"][0]["point_in_polygon"]["on_boundary"] = True
        mutations.append(boundary)

        neusa = copy.deepcopy(original)
        next(x for x in neusa["promotions"] if x["codigo_inep"] == "35099569")["conflict_preserved"] = ""
        mutations.append(neusa)

        theresa = copy.deepcopy(original)
        next(x for x in theresa["promotions"] if x["codigo_inep"] == "35241885")["extension_excluded"]["reason"] = "USE_EXTENSION"
        mutations.append(theresa)

        fake_zero = copy.deepcopy(original)
        mauricio = next(x for x in fake_zero["promotions"] if x["codigo_inep"] == "35286229")
        mauricio["income"]["V06004"] = 0
        mutations.append(fake_zero)

        for mutated in mutations:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as handle:
                json.dump(mutated, handle, ensure_ascii=False)
                handle.flush()
                with self.assertRaises(Task199HStop):
                    load_contract(handle.name)


if __name__ == "__main__":
    unittest.main()
