import unittest

from robo_dados_publicos.analytics.base_v05_network_series import (
    load_contract,
    materialize_series,
    read_fixture,
    to_product_rows,
    validate_series,
)


GENERATED_AT = "2026-09-06T03:02:00Z"
SOFTWARE_VERSION = "0.8.0"


class TestTask181BaseV05NetworkSeries(unittest.TestCase):
    def test_contract_pins_base_v05_source_and_period(self):
        c = load_contract()
        self.assertEqual(
            c["source"]["sha256"],
            "4d352dc55537240a4c1ffb3c37337e9c029577ab611f851f2ec925d0178b9eda",
        )
        self.assertEqual(c["source"]["sheet"], "Series Rede")
        self.assertEqual(c["source"]["period_start"], 2007)
        self.assertEqual(c["source"]["period_end"], 2025)
        self.assertFalse(c["quality"]["blank_is_zero"])
        self.assertTrue(c["quality"]["published_zero_is_observed_zero"])

    def test_fixture_has_complete_2007_2025_year_sequence(self):
        rows = read_fixture()
        self.assertEqual(len(rows), 19)
        self.assertEqual([int(x["Ano"]) for x in rows], list(range(2007, 2026)))

    def test_expected_non_null_and_missing_counts(self):
        got = validate_series()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["school_indicator_non_null"], 171)
        self.assertEqual(got["school_indicator_missing"], 133)
        self.assertEqual(got["fiscal_non_null"], 38)
        self.assertEqual(got["fiscal_missing"], 0)
        self.assertEqual(got["deferred_non_null"], 16)
        self.assertEqual(got["deferred_missing"], 22)
        self.assertGreaterEqual(got["published_zero_count"], 2)

    def test_product_rows_split_school_fiscal_and_deferred_roles(self):
        rows = to_product_rows()
        self.assertEqual(len(rows["school_rows"]), 171)
        self.assertEqual(len(rows["fiscal_rows"]), 38)
        self.assertEqual(len(rows["missing_ledger"]), 133)
        self.assertEqual(len(rows["deferred_source_role_review"]), 38)
        self.assertTrue(all(x["product_name"] == "SCHOOL_INDICATOR_SERIES" for x in rows["missing_ledger"]))

    def test_published_siope_zero_is_preserved_as_observation(self):
        rows = to_product_rows()["fiscal_rows"]
        y2007 = {x["metric_id"]: x["value"] for x in rows if x["period"] == "2007"}
        self.assertEqual(y2007["SIOPE_MDE_SHARE"], 0)
        self.assertEqual(y2007["SIOPE_FUNDEB_REMUNERATION_SHARE"], 0)

    def test_blank_ideb_year_does_not_become_zero(self):
        rows = to_product_rows()
        school = rows["school_rows"]
        self.assertFalse(any(x["period"] == "2008" and x["indicator_id"] == "IDEB" for x in school))
        self.assertTrue(
            any(
                x["period"] == "2008"
                and x["indicator_id"] == "IDEB"
                and x["status"] == "MISSING_SOURCE_CELL_NOT_ZERO"
                for x in rows["missing_ledger"]
            )
        )

    def test_official_and_simple_saresp_means_remain_distinct(self):
        school = to_product_rows()["school_rows"]
        y2025 = {
            x["indicator_id"]: x["value"]
            for x in school
            if x["period"] == "2025"
        }
        self.assertEqual(y2025["SARESP_OFFICIAL_LP_MEAN"], 219)
        self.assertEqual(y2025["SARESP_SIMPLE_SCHOOL_LP_MEAN"], 219.40499999999997)
        self.assertNotEqual(
            y2025["SARESP_OFFICIAL_LP_MEAN"],
            y2025["SARESP_SIMPLE_SCHOOL_LP_MEAN"],
        )
        self.assertEqual(y2025["SARESP_OFFICIAL_MATH_MEAN"], 240)
        self.assertEqual(y2025["SARESP_SIMPLE_SCHOOL_MATH_MEAN"], 240.60999999999996)

    def test_2025_network_values_are_preserved(self):
        school = to_product_rows()["school_rows"]
        y2025 = {x["indicator_id"]: x["value"] for x in school if x["period"] == "2025"}
        self.assertEqual(y2025["IDEB"], 7.1)
        self.assertEqual(y2025["IDEB_LP_PROFICIENCY"], 236.43)
        self.assertEqual(y2025["IDEB_MATH_PROFICIENCY"], 254.45)
        self.assertEqual(y2025["DSU"], 96.2)
        self.assertEqual(y2025["TNR"], 0.6)
        self.assertEqual(y2025["APPROVAL_RATE"], 99.9)
        self.assertEqual(y2025["FAILURE_RATE"], 0.1)
        self.assertEqual(y2025["DROPOUT_RATE"], 0)

    def test_remuneration_stays_deferred_not_materialized(self):
        rows = to_product_rows()
        deferred = rows["deferred_source_role_review"]
        observed = [x for x in deferred if x["status"] == "DEFERRED_SOURCE_ROLE_REVIEW"]
        self.assertEqual(len(observed), 16)
        self.assertTrue(all(x["unit"] == "BRL" for x in observed))
        self.assertFalse(
            any(
                x.get("indicator_id", "").startswith("REMUN")
                for x in rows["school_rows"]
            )
        )

    def test_materialization_produces_task176_products_deterministically(self):
        a = materialize_series(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        b = materialize_series(generated_at=GENERATED_AT, software_version=SOFTWARE_VERSION)
        self.assertEqual(a["school_indicator_product"]["row_count"], 171)
        self.assertEqual(a["fiscal_product"]["row_count"], 38)
        self.assertEqual(
            a["school_indicator_product"]["snapshot_id"],
            b["school_indicator_product"]["snapshot_id"],
        )
        self.assertEqual(
            a["fiscal_product"]["snapshot_id"],
            b["fiscal_product"]["snapshot_id"],
        )
        self.assertFalse(a["binary_import_complete"])
        self.assertFalse(a["source_layers_replaced"])


if __name__ == "__main__":
    unittest.main()
