from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_128_PNCP_LIMEIRA_CONTRACTS_PAGE1_SCAN_0.8.0.json"
A=ROOT/"docs/evidence/TASK_128_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
W=ROOT/"docs/evidence/TASK_128_EXECUTED_WORKFLOW_SOURCE_0.8.0.txt"

class TestTask128Closure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))
        cls.a=json.loads(A.read_text(encoding="utf-8"))

    def test_page1_live_identity(self):
        x=self.e["live_execution"]
        self.assertEqual(33936732563,x["run_id"])
        self.assertEqual(101226011211,x["job_id"])
        self.assertEqual("ef902e52c5eeef1d10f32c3c126a4baadee36abf",x["execution_head_sha"])
        self.assertEqual(1,x["get_attempts"])
        self.assertEqual(200,x["http_status"])
        self.assertEqual(767611,x["bytes_received"])
        self.assertEqual("8935e589bbbf4cfaba6c49eea7b675ab30e160c168f374c3a87857969bb11990",x["source_sha256"])

    def test_page1_is_partial_not_no_match(self):
        c=self.e["coverage"]
        self.assertEqual(2023,c["total_registros"])
        self.assertEqual(5,c["total_paginas"])
        self.assertEqual(500,c["rows_on_page"])
        self.assertFalse(c["exhaustive_within_query_scope"])
        self.assertTrue(c["fresh_paging_gate_required"])
        self.assertEqual(0,self.e["candidate_count"])
        self.assertEqual("PARTIAL_PAGE1_REQUIRES_FRESH_PAGING_GATE",self.e["status"])

    def test_authorization_consumed_without_retry(self):
        self.assertEqual("CONSUMED_SINGLE_USE_PAGE1",self.a["status"])
        self.assertEqual(1,self.a["consumed_by"]["get_attempts"])
        self.assertFalse(self.a["consumed_by"]["retry_performed"])
        self.assertFalse(self.a["future_paging_authorized"])
        self.assertFalse(self.a["future_retry_authorized"])

    def test_raw_payload_not_persisted_and_workflow_source_preserved(self):
        self.assertFalse(self.e["raw_payload_persisted"])
        self.assertTrue(W.exists())
        self.assertIn("TASK128_RESULT_BEGIN",W.read_text(encoding="utf-8"))

if __name__=="__main__":
    unittest.main()
