from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_149_PNCP_DIRECT_DOWNLOAD_PREVIEW_GUARD_STOP_0.8.0.json"


class TestTask149(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_exact_corrected_url_is_pinned(self):
        self.assertTrue(self.e["exact_url"].endswith("pagina=1&tamanhoPagina=50"))

    def test_single_invocation_stopped_before_source(self):
        x=self.e["execution"]
        self.assertEqual(1,x["direct_download_invocations"])
        self.assertFalse(x["retry_performed"])
        self.assertEqual("URL_NOT_VIEWED_IN_CONVERSATION_PRECONDITION",x["tool_failure_class"])
        self.assertFalse(x["pncp_source_reach_established"])
        self.assertFalse(x["pncp_http_status_established"])
        self.assertFalse(x["source_data_observed"])
        self.assertFalse(x["temporary_payload_created"])
        self.assertEqual("NO_FILE_CREATED",x["local_postcheck"])

    def test_authorization_is_consumed_without_preview_or_retry(self):
        a=self.e["authorization_state"]
        self.assertTrue(a["task148_single_direct_download_authorization_consumed"])
        self.assertFalse(a["second_direct_download_authorized"])
        self.assertFalse(a["web_preview_authorized"])
        self.assertFalse(a["retry_authorized"])

    def test_no_data_conclusion_created(self):
        s=self.e["epistemic_state"]
        self.assertFalse(s["administrative_identifier_candidate_found"])
        self.assertFalse(s["pncp_no_match_conclusion_created"])
        self.assertFalse(s["negative_exhaustive_conclusion_created"])
        self.assertFalse(s["financial_identity_created"])
        self.assertFalse(s["transaction_identity_created"])
        self.assertFalse(s["supplier_linkage_created"])


if __name__=="__main__":
    unittest.main()
