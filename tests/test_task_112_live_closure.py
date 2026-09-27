from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/evidence/TASK_112_REAL_PPA_OCR_RESULT_0.8.0.json"
ARTIFACT = ROOT / "docs/evidence/TASK_112_REAL_PPA_OCR_ARTIFACT_0.8.0.json"
AUTH = ROOT / "docs/evidence/TASK_112_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
WORKFLOW = ROOT / ".github/workflows/task-112-real-ppa-ocr-once.yml"


class TestTask112LiveClosure(unittest.TestCase):
    def setUp(self):
        self.result = json.loads(RESULT.read_text(encoding="utf-8"))

    def test_exact_source_and_document_identity_are_proven(self):
        self.assertEqual(
            "NO_MATCH_TASK112_EXPECTED_PLANNING_SIGNAL_NOT_FOUND",
            self.result["status"],
        )
        self.assertEqual(1, self.result["source"]["request_count"])
        self.assertEqual(
            "685a621a2f5fa8859e4b7f8518627c1523a2fbc5f3402ff48d4aa7573300113d",
            self.result["source"]["source_sha256"],
        )
        self.assertEqual(3252087, self.result["source"]["source_bytes"])
        self.assertEqual(80, self.result["document"]["page_count"])
        self.assertEqual(80, self.result["document"]["pages_ocr_scanned"])
        self.assertEqual(1, self.result["law_identity"]["page"])
        self.assertGreater(self.result["law_identity"]["confidence_mean"], 90.0)

    def test_no_match_is_only_for_declared_alias(self):
        self.assertIsNone(self.result["planning_signal"])
        self.assertFalse(self.result["retry_performed"])
        self.assertFalse(self.result["future_execution_authorized"])
        self.assertTrue(all(v == 0 for v in self.result["hard_boundaries"].values()))

    def test_artifact_and_auth_are_consumed_and_pinned(self):
        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        auth = json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertEqual(9954834931, artifact["artifact"]["id"])
        self.assertEqual(
            "039b7cea3e763734f790ec006ed1c4bbf85b4d72f914aeec5878e398fd5cc792",
            artifact["artifact"]["zip_sha256"],
        )
        self.assertEqual(
            "WORKFLOW_AND_EXACT_SOURCE_READ_CONSUMED_NO_MATCH_FOR_DECLARED_ALIAS",
            auth["status"],
        )
        self.assertEqual(1, auth["consumed_by"]["source_request_count"])
        self.assertTrue(auth["consumed_by"]["source_read_scope_consumed"])
        self.assertTrue(auth["consumed_by"]["workflow_single_use_consumed"])
        self.assertFalse(auth["future_execution_authorized"])

    def test_live_workflow_is_removed_before_merge(self):
        self.assertFalse(WORKFLOW.exists())


if __name__ == "__main__":
    unittest.main()
