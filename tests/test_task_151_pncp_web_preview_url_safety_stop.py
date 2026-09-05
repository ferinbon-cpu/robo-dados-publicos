from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/evidence/TASK_151_PNCP_WEB_PREVIEW_URL_SAFETY_STOP_0.8.0.json"


class TestTask151(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e = json.loads(E.read_text(encoding="utf-8"))

    def test_single_web_open_consumed_without_followup(self):
        x = self.e["execution"]
        self.assertEqual(1, x["web_open_invocations"])
        self.assertFalse(x["retry_performed"])
        self.assertEqual(0, x["search_queries"])
        self.assertEqual(0, x["clicks"])
        self.assertEqual(0, x["followup_opens"])
        self.assertEqual(0, x["direct_download_invocations"])

    def test_stop_is_pre_source_not_pncp_response(self):
        self.assertEqual("STOP_WEB_URL_SAFETY_PRECONDITION_PRE_SOURCE", self.e["result"])
        x = self.e["execution"]
        self.assertEqual("URL_SAFETY_PRECONDITION_NON_RETRYABLE", x["tool_failure_class"])
        self.assertFalse(x["pncp_source_reach_established"])
        self.assertFalse(x["pncp_http_status_established"])
        self.assertFalse(x["source_data_observed"])
        self.assertFalse(x["raw_payload_persisted"])

    def test_query_normalization_is_recorded(self):
        self.assertNotEqual(self.e["requested_exact_url"], self.e["tool_reported_normalized_url"])
        self.assertIn("tamanhoPagina=50", self.e["requested_exact_url"])
        self.assertIn("tamanhoPagina=50", self.e["tool_reported_normalized_url"])

    def test_no_epistemic_promotion(self):
        s = self.e["epistemic_state"]
        self.assertFalse(any(s.values()))

    def test_new_authorization_required(self):
        a = self.e["authorization_state"]
        self.assertTrue(a["task150_single_web_open_authorization_consumed"])
        self.assertFalse(a["second_open_authorized"])
        self.assertFalse(a["retry_authorized"])
        self.assertFalse(a["direct_download_authorized"])


if __name__ == "__main__":
    unittest.main()
