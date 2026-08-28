import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY_RUN_2_0.8.0.json"


class TestM8ReadonlyLiveEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_run_job_head_and_artifact_are_exact(self):
        run = self.data["run"]
        artifact = self.data["artifact"]
        self.assertEqual(33136736495, run["id"])
        self.assertEqual(98738273929, run["job_id"])
        self.assertEqual("8f80edcae45a373f85b84c03880842363661d870", run["head_sha"])
        self.assertEqual("success", run["conclusion"])
        self.assertEqual(9672319372, artifact["id"])
        self.assertEqual(28788, artifact["zip_size_bytes"])
        self.assertEqual("sha256:a3afeed9c1449ab4806127024d044d177e76e8097894786b0e68bbbfffc60b51", artifact["digest"])
        self.assertEqual("1000c052f05e25073650466034969770deaeb4dabc0fb49e0991931e599409a2", artifact["result_json"]["sha256"])

    def test_runtime_scope_and_effects_are_readonly(self):
        oauth = self.data["oauth_capability"]
        effects = self.data["bounded_effects"]
        self.assertEqual("PASS_M8_READONLY_CREDENTIAL_CAPABILITY", oauth["status"])
        self.assertEqual("https://www.googleapis.com/auth/drive.readonly", oauth["scope"])
        self.assertEqual("oauth_refresh_and_tokeninfo_exact", oauth["scope_proof"])
        self.assertTrue(oauth["proof_occurs_before_first_drive_lookup"])
        self.assertEqual(0, oauth["drive_api_request_count_during_capability_proof"])
        self.assertEqual(0, effects["source_get_count"])
        self.assertEqual(9, effects["drive_lookup_count"])
        self.assertEqual(9, effects["drive_download_count"])
        self.assertEqual(0, effects["drive_write_count"])
        self.assertFalse(effects["publication_authorized"])
        self.assertFalse(effects["remote_file_id_persisted"])
        self.assertFalse(effects["retry_authorized"])
        self.assertFalse(effects["pagination_authorized"])
        self.assertFalse(effects["recurrence_authorized"])
        self.assertFalse(effects["schedule_enabled"])
        self.assertFalse(effects["future_batch_execution_authorized"])
        self.assertFalse(effects["imputation_performed"])
        self.assertFalse(effects["compliance_claims_authorized"])

    def test_product_scope_is_exactly_2016_through_2024(self):
        product = self.data["product"]
        self.assertEqual(list(range(2016, 2025)), product["years"])
        self.assertEqual(9, product["year_count"])
        self.assertEqual(9, product["gold_count"])
        self.assertEqual(8, product["metric_row_count"])
        self.assertEqual(72, product["gold_metric_observations"])
        self.assertEqual(1, product["period_by_year"]["2016"])
        for year in range(2017, 2025):
            self.assertEqual(6, product["period_by_year"][str(year)])
        self.assertTrue(product["publication_not_authorized_by_this_evidence"])

    def test_product_file_hashes_and_sizes_are_pinned(self):
        expected = {
            "product/report.json": (25586, "bf9f7d9d1c5b1cb046cb4721e41e24b46b90070d50386060f02166d0fac9a946"),
            "product/report_card.json": (778, "09a55ba600ac99e6cf18f2ddec310aedd5e800bdce7586eaf606b7c5190a451a"),
            "product/table.csv": (23115, "749b8dd8f56b4ced755f634e08c9b4f8d7cd6f75c448e4c55bbfe77f6d7f8a8e"),
            "product/report.md": (24602, "3d89f69c012f71294ccc001542fb4eade0c9d4d5d4de2882c35e4745f9e6938c"),
            "product/report.html": (25974, "d5c124538c02ef25968a89e74069632a2cc23f63822d93d24ee3b8119f9ab4ee"),
            "product/report.pdf": (21854, "31aadfd44448061aefcbc76903e3f910f14b7f8b6e46ae60dbfdc683143225d9"),
            "product/manifest.json": (1214, "382dfa0965a547a09b68ec0d284d8fcc4a16e121dd8295d5ac12b27248aa09c7"),
        }
        observed = {row["path"]: (row["bytes"], row["sha256"]) for row in self.data["artifact"]["product_files"]}
        self.assertEqual(expected, observed)

    def test_gold_inputs_are_exact_and_no_2015_is_present(self):
        expected = {
            2016: (1, 1615, "7f84500f5915b21210fda36c638a6d1fecdf1fb1ef0a5a4f9431c5273659d2bd"),
            2017: (6, 1616, "d9a62de4345c42a8c02a8b97e7c5ccb129b203b1c75f3b4074f09ddf96783d0e"),
            2018: (6, 1619, "b479a4801a83f3d1f3086ea57b10f25ff393b69714b3a00ea7e6b0256e03ce02"),
            2019: (6, 1620, "d843f61c37f84d978de8488243492cd8fe09c3a9ad3856c856e314e5063ab19c"),
            2020: (6, 1621, "073e5e823ad9d37431ef4e89876236ff545c2211a4e9167000c01cef96eab7fa"),
            2021: (6, 1620, "e8b4888b243aee21af0ba4654a481d502150a45bbbecebfcb5239f5d338d5ef5"),
            2022: (6, 1623, "4057aac2b18dc7184db992ee989d64c8732c4ad858cc6e8b7520cd50c4d37f68"),
            2023: (6, 1623, "a4da994fd2a04ef0b3133d9a20855e6809922f19366075d48aab3296ca488272"),
            2024: (6, 1612, "d6a35db7c42129569c73f19de789d871d0d285929d8eb3fe2a04d5ef03fdd6e0"),
        }
        observed = {row["year"]: (row["period"], row["bytes"], row["sha256"]) for row in self.data["gold_inputs"]}
        self.assertEqual(expected, observed)
        self.assertNotIn(2015, observed)
        self.assertFalse(self.data["governance"]["m8_no_click_authorized"])
        self.assertFalse(self.data["governance"]["publication_authorized"])
        self.assertFalse(self.data["governance"]["future_batch_execution_authorized"])

    def test_live_qa_counts_are_pinned(self):
        qa = self.data["qa"]
        self.assertEqual({"passed": 1229, "total": 1229}, qa["unit_tests"])
        self.assertEqual({"passed": 109, "total": 109}, qa["historical_regression"])
        self.assertEqual("PASS", qa["compileall"])


if __name__ == "__main__":
    unittest.main()
