import unittest

from robo_dados_publicos.analytics.ibge_territory_foundation import (
    binary_acquisition_plan,
    validate_foundation,
)


class TestTask199AIbgeTerritorialFoundation(unittest.TestCase):
    def test_foundation_passes_fail_closed_validation(self):
        result = validate_foundation()
        self.assertEqual(
            result["status"],
            "PASS_SOURCE_FOUNDATION_READY_BINARY_INGESTION_PENDING",
        )
        self.assertEqual(result["source_count"], 5)
        self.assertEqual(result["first_binary_target"], "IBGE_CNEFE_LIMEIRA_2022")
        self.assertFalse(result["territory_profile_materialized"])
        self.assertFalse(result["canonical_answerability_change"])

    def test_binary_plan_is_exact_and_bounded(self):
        plan = binary_acquisition_plan()
        self.assertEqual(len(plan), 4)
        self.assertEqual(plan[0]["source_id"], "IBGE_CNEFE_LIMEIRA_2022")
        self.assertIn("3526902_LIMEIRA.zip", plan[0]["url"])
        self.assertEqual(
            plan[1]["source_id"],
            "IBGE_CENSO2022_SECTOR_BASIC_BR_20260520",
        )
        self.assertEqual(
            plan[2]["source_id"],
            "IBGE_CENSO2022_SECTOR_INCOME_RESP_BR_20260508",
        )
        self.assertEqual(plan[3]["source_id"], "IBGE_CENSO2022_SP_SECTOR_GPKG")

    def test_discovery_does_not_fake_materialization(self):
        result = validate_foundation()
        self.assertFalse(result["territory_profile_materialized"])
        self.assertFalse(result["canonical_answerability_change"])


if __name__ == "__main__":
    unittest.main()
