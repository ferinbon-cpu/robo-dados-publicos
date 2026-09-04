from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"docs/evidence/TASK_114_ONTOLOGY_OCR_RESULT_0.8.0.json"
ARTIFACT=ROOT/"docs/evidence/TASK_114_ONTOLOGY_OCR_ARTIFACT_0.8.0.json"
AUTH=ROOT/"docs/evidence/TASK_114_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
WORKFLOW=ROOT/".github/workflows/task-114-ontology-ppa-ocr-once.yml"

class TestTask114LiveClosure(unittest.TestCase):
    def setUp(self):
        self.result=json.loads(RESULT.read_text(encoding="utf-8"))

    def test_complete_ontology_scan_is_pinned(self):
        self.assertEqual("NO_CANDIDATES_FOUND",self.result["status"])
        self.assertEqual(0,self.result["candidate_count"])
        self.assertEqual(0,self.result["candidate_page_count"])
        self.assertEqual([],self.result["candidate_pages"])
        self.assertEqual(1,self.result["source"]["request_count"])
        self.assertEqual(80,self.result["document"]["page_count"])
        self.assertEqual(
            "685a621a2f5fa8859e4b7f8518627c1523a2fbc5f3402ff48d4aa7573300113d",
            self.result["source"]["source_sha256"],
        )

    def test_no_promotion_occurred(self):
        self.assertTrue(all(value is False for value in self.result["promotion"].values()))
        self.assertFalse(self.result["retry_performed"])
        self.assertFalse(self.result["future_execution_authorized"])

    def test_artifact_and_auth_are_pinned(self):
        artifact=json.loads(ARTIFACT.read_text(encoding="utf-8"))
        auth=json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertEqual(9955229109,artifact["artifact"]["id"])
        self.assertEqual(
            "a288dd65298ee8475b266b6c7761e19d69913d58549d8572fd4ddccf51727ac7",
            artifact["artifact"]["zip_sha256"],
        )
        self.assertEqual(
            "WORKFLOW_AND_EXACT_SOURCE_ONTOLOGY_SCAN_CONSUMED_NO_CANDIDATES",
            auth["status"],
        )
        self.assertEqual(29,auth["consumed_by"]["ontology_term_count"])
        self.assertEqual(3,auth["consumed_by"]["ontology_family_count"])
        self.assertEqual(0,auth["consumed_by"]["candidate_count"])
        self.assertTrue(auth["consumed_by"]["source_read_scope_consumed"])
        self.assertTrue(auth["consumed_by"]["workflow_single_use_consumed"])

    def test_live_workflow_is_removed_before_merge(self):
        self.assertFalse(WORKFLOW.exists())

if __name__=="__main__":
    unittest.main()
