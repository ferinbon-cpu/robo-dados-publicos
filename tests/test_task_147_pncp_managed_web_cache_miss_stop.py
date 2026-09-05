from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_147_PNCP_MANAGED_WEB_CACHE_MISS_STOP_0.8.0.json"

class TestTask147(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_exact_corrected_url_is_pinned(self):
        self.assertTrue(cls_url := self.e["exact_url"])
        self.assertTrue(cls_url.endswith("pagina=1&tamanhoPagina=50"))
        self.assertNotIn("tamanhoPagina=500", cls_url)

    def test_single_open_consumed_without_retry(self):
        x=self.e["execution"]
        self.assertEqual(1,x["managed_web_open_invocations"])
        self.assertFalse(x["retry_performed"])
        self.assertEqual(0,x["search_queries"])
        self.assertEqual(0,x["clicks"])
        self.assertEqual(0,x["followup_opens"])
        a=self.e["authorization_state"]
        self.assertTrue(a["fresh_task146_exact_url_authorization_consumed"])
        self.assertFalse(a["second_open_authorized"])
        self.assertFalse(a["retry_authorized"])

    def test_cache_miss_is_not_pncp_response(self):
        self.assertEqual("STOP_MANAGED_WEB_CACHE_MISS_NO_PNCP_CONTENT",self.e["result"])
        x=self.e["execution"]
        self.assertEqual("FETCH_CACHE_MISS",x["tool_failure_class"])
        self.assertFalse(x["pncp_content_returned"])
        self.assertFalse(x["pncp_http_status_established"])
        self.assertFalse(x["source_data_observed"])
        self.assertFalse(x["raw_payload_persisted"])

    def test_no_negative_or_identity_conclusion(self):
        s=self.e["epistemic_state"]
        self.assertFalse(s["administrative_identifier_candidate_found"])
        self.assertFalse(s["pncp_no_match_conclusion_created"])
        self.assertFalse(s["negative_exhaustive_conclusion_created"])
        self.assertFalse(s["financial_identity_created"])
        self.assertFalse(s["transaction_identity_created"])
        self.assertFalse(s["supplier_linkage_created"])
        self.assertFalse(self.e["followup_endpoints_executed"])

if __name__=="__main__":
    unittest.main()
