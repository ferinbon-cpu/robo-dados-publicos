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

    def test_historical_dns_claim_is_preserved_but_not_admissible(self):
        self.assertEqual(
            "UNVERIFIED_EXECUTION_CLAIM_NOT_ADMISSIBLE_AS_SOURCE_EFFECT",
            self.e["canonical_result"],
        )
        p=self.e["provenance_adjudication"]
        self.assertFalse(p["executor_run_id_present"])
        self.assertFalse(p["executor_job_id_present"])
        self.assertFalse(p["executor_log_present"])
        self.assertFalse(p["executor_artifact_present"])
        self.assertFalse(p["source_effect_claim_admissible"])
        self.assertTrue(p["historical_record_preserved"])
        self.assertEqual(6,self.e["historical_claim"]["curl_exit_code"])

    def test_no_data_conclusion_created(self):
        s=self.e["epistemic_state"]
        self.assertFalse(s["pncp_data_observed"])
        self.assertFalse(s["administrative_identifier_found"])
        self.assertFalse(s["no_match_conclusion_created"])
        self.assertFalse(s["financial_identity_created"])
        self.assertFalse(s["transaction_identity_created"])

    def test_source_authorization_is_restored_to_unconsumed(self):
        self.assertEqual("AUTHORIZED_UNCONSUMED_NO_PROVEN_SOURCE_ATTEMPT",self.a["status"])
        self.assertFalse(self.a["task134_execution_attempt_consumed"])
        self.assertFalse(self.a["source_read_scope_consumed"])
        self.assertFalse(self.a["authorization_consumed"])
        self.assertEqual(0,self.a["source_http_requests_emitted"])
        self.assertEqual(0,self.a["source_bytes_read"])
        self.assertFalse(self.a["future_retry_authorized"])
        self.assertFalse(self.a["future_rerun_authorized"])

if __name__=="__main__":
    unittest.main()
