import unittest

from robo_dados_publicos.analytics.cnefe_limeira_ingestion import validate_cnefe_ingestion


class TestTask199BCnefeLimeiraIngestion(unittest.TestCase):
    def test_exact_binary_custody_and_scope(self):
        result = validate_cnefe_ingestion()
        self.assertEqual(
            result["status"],
            "PASS_CNEFE_RAW_AND_MEMBER_CUSTODY_PROVEN_CROSSWALK_PENDING",
        )
        self.assertEqual(
            result["archive_sha256"],
            "ab73250df889effcb01ddc2d060bddd3252e995468e97ef93b048564763626a7",
        )
        self.assertEqual(
            result["member_sha256"],
            "8adb17d18a8c0a4de9e6d48b31ed63f74e0bfde27f11f63154c17456d35218b3",
        )
        self.assertEqual(result["row_count"], 150450)
        self.assertEqual(result["sector_count"], 724)

    def test_school_text_candidates_do_not_promote_crosswalk(self):
        result = validate_cnefe_ingestion()
        self.assertEqual(result["school_candidate_rows"], 41)
        self.assertFalse(result["school_to_sector_crosswalk_materialized"])
        self.assertFalse(result["territory_profile_materialized"])
        self.assertFalse(result["canonical_answerability_change"])


if __name__ == "__main__":
    unittest.main()
