from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
AUTH=ROOT/"docs/evidence/TASK_134_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
E=ROOT/"docs/evidence/TASK_136_PNCP_CURL_DNS_STOP_0.8.0.json"

class TestTask136(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=json.loads(AUTH.read_text(encoding="utf-8"))
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_dns_stop_is_pre_http(self):
        self.assertEqual("STOP_PRE_HTTP_DNS_RESOLUTION_FAILED", self.e["result"])
        x=self.e["execution"]
        self.assertEqual(6,x["curl_exit_code"])
        self.assertEqual(0,x["http_status"])
        self.assertFalse(x["http_get_emitted"])
        self.assertEqual(0,x["bytes_received"])
        self.assertFalse(x["raw_file_created"])
        self.assertFalse(x["retry_performed"])

    def test_no_data_conclusion_created(self):
        s=self.e["epistemic_state"]
        self.assertFalse(s["pncp_data_observed"])
        self.assertFalse(s["administrative_identifier_found"])
        self.assertFalse(s["no_match_conclusion_created"])
        self.assertFalse(s["financial_identity_created"])
        self.assertFalse(s["transaction_identity_created"])

    def test_source_authorization_remains_unconsumed(self):
        self.assertTrue(self.a["task134_execution_attempt_consumed"])
        self.assertFalse(self.a["source_read_scope_consumed"])
        self.assertFalse(self.a["authorization_consumed"])
        self.assertEqual(0,self.a["source_http_requests_emitted"])
        self.assertEqual(0,self.a["source_bytes_read"])
        self.assertFalse(self.a["future_retry_authorized"])
        self.assertFalse(self.a["future_rerun_authorized"])

if __name__=="__main__":
    unittest.main()
