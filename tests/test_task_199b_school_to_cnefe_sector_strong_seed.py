import unittest

from robo_dados_publicos.analytics.school_to_cnefe_sector_seed import validate_strong_seed


class TestTask199BSchoolToCnefeSectorStrongSeed(unittest.TestCase):
    def test_strong_seed_is_exact_partial_and_fail_closed(self):
        result = validate_strong_seed()
        self.assertEqual(result["status"], "PASS_PARTIAL_STRONG_SEED_14_OF_40")
        self.assertEqual(result["row_count"], 14)
        self.assertEqual(result["unique_sector_count"], 14)
        self.assertFalse(result["full_69_school_crosswalk_materialized"])
        self.assertFalse(result["territory_profile_materialized"])
        self.assertFalse(result["canonical_answerability_change"])


if __name__ == "__main__":
    unittest.main()
