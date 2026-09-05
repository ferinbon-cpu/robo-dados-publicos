from pathlib import Path
import json,unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_129_PNCP_LIMEIRA_CONTRACTS_PAGES2_5_0.8.0.json"
A=ROOT/"docs/evidence/TASK_129_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
W=ROOT/".github/workflows/task-129-pncp-pages2-5-once.yml"

class TestTask129Closure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))
        cls.a=json.loads(A.read_text(encoding="utf-8"))

    def test_page2_success_and_page3_transport_stop(self):
        x=self.e["live_execution"]
        self.assertEqual(2,x["request_attempts"])
        self.assertEqual(200,x["page2"]["http_status"])
        self.assertEqual(500,x["page2"]["rows_on_page"])
        self.assertEqual(0,x["page2"]["candidate_count"])
        self.assertEqual(0,x["page3"]["bytes_received"])
        self.assertIn("TimeoutError",x["page3"]["transport_error"])
        self.assertFalse(x["pages4_5_attempted"])

    def test_no_exhaustive_or_identity_promotion(self):
        c=self.e["combined_coverage"]
        self.assertFalse(c["exhaustive_within_query_scope"])
        self.assertEqual([1,2],c["pages_confirmed_scanned"])
        self.assertEqual([3,4,5],c["pages_remaining"])
        i=self.e["interpretation"]
        self.assertTrue(i["no_global_no_match_claim"])
        self.assertFalse(i["financial_identity_changed"])
        self.assertFalse(i["transaction_identity_changed"])

    def test_artifact_and_result_are_pinned(self):
        self.assertEqual(9961857923,self.e["artifact"]["id"])
        self.assertEqual(
            "b82fe218fa3756cd99669d0a73f36e7109e66c3a1db265da2d215e0fed5cbf40",
            self.e["artifact"]["zip_sha256"],
        )
        self.assertEqual(
            "ff0cb0a3af61884ec9aa585c2c37d76b053bf4bef0ad6bc120a6b0cd2651992f",
            self.e["live_execution"]["result_sha256"],
        )

    def test_authorization_consumed_and_workflow_removed(self):
        self.assertEqual("CONSUMED_PARTIAL_TRANSPORT_STOP_NO_RETRY",self.a["status"])
        self.assertFalse(self.a["future_execution_authorized"])
        self.assertTrue(self.a["consumed_by"]["workflow_single_use_consumed"])
        self.assertFalse(W.exists())

if __name__=="__main__": unittest.main()
