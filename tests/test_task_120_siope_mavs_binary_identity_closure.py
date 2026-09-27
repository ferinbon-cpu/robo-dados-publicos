from __future__ import annotations
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"docs/evidence/TASK_120_SIOPE_MAVS_BINARY_IDENTITY_0.8.0.json"
AUTH=ROOT/"docs/evidence/TASK_120_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"

class TestTask120BinaryIdentityClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads(RESULT.read_text(encoding="utf-8"))
        cls.auth=json.loads(AUTH.read_text(encoding="utf-8"))

    def test_exact_binary_identity_is_pinned(self):
        self.assertEqual("PASS_TASK120_EXACT_SOURCE_BINARY_IDENTITY",self.result["status"])
        source=self.result["source"]
        self.assertEqual(360070,source["metadata_size_bytes"])
        self.assertEqual(360070,source["raw_media_size_bytes"])
        self.assertEqual(
            "d2b7f7638222bc9788f6d42df11126d2e3aa57cb4204450914c98d9400bf0bbe",
            source["sha256"],
        )
        self.assertTrue(source["pdf_magic_verified"])

    def test_exact_request_budget_was_consumed(self):
        counts=self.result["request_counts"]
        self.assertEqual(1,counts["drive_metadata_reads"])
        self.assertEqual(1,counts["drive_raw_media_reads"])
        self.assertEqual(0,counts["drive_searches"])
        self.assertEqual(0,counts["drive_lists"])
        self.assertEqual(0,counts["drive_writes"])

    def test_no_semantic_reinterpretation_or_persistence(self):
        self.assertTrue(self.result["semantic_boundary"]["task056_remains_semantic_authority"])
        self.assertTrue(all(
            self.result["semantic_boundary"][key] is False
            for key in (
                "text_extraction_performed","ocr_performed",
                "ontology_scan_performed","semantic_reinterpretation_performed"
            )
        ))
        self.assertTrue(all(value is False for value in self.result["persistence"].values()))

    def test_only_source_binary_identity_is_promoted(self):
        p=self.result["promotions"]
        self.assertTrue(p["source_binary_identity_proven"])
        self.assertFalse(p["financial_identity"])
        self.assertFalse(p["transaction_identity"])
        self.assertFalse(p["implementation"])
        self.assertFalse(p["causal_effect"])

    def test_authorization_is_consumed_and_not_reusable(self):
        self.assertEqual("CONSUMED_SINGLE_USE_NO_RETRY",self.auth["status"])
        self.assertEqual(1,self.auth["consumed_by"]["metadata_read_count"])
        self.assertEqual(1,self.auth["consumed_by"]["raw_media_read_count"])
        self.assertFalse(self.auth["consumed_by"]["content_interpretation_performed"])
        self.assertFalse(self.auth["consumed_by"]["raw_pdf_persisted_to_repository"])
        self.assertFalse(self.auth["future_execution_authorized"])

if __name__=="__main__": unittest.main()
