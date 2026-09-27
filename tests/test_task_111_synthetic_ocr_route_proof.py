from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_111_SYNTHETIC_OCR_ROUTE_PROOF_0.8.0.json"
WORKFLOW = ROOT / ".github/workflows/task-111-synthetic-ocr-proof-once.yml"


class TestTask111SyntheticOcrRouteProof(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_successful_synthetic_proof_is_pinned(self):
        self.assertEqual("PASS_SYNTHETIC_OCR_ROUTE_PROVEN", self.data["decision"])
        proof = self.data["successful_attempt"]
        self.assertEqual(33919583422, proof["run_id"])
        self.assertEqual(101174577341, proof["job_id"])
        self.assertEqual("success", proof["conclusion"])
        self.assertTrue(proof["pdf_text_empty"])
        self.assertEqual(1, proof["pdf_page_count"])
        self.assertTrue(proof["marker_recovered"])
        self.assertTrue(proof["portuguese_phrase_recovered"])
        self.assertEqual(
            "TASK111 MARCADOR OCR 73159 EDUCACAO INTEGRAL LIMEIRA",
            proof["normalized_ocr_text"],
        )
        self.assertGreaterEqual(proof["word_confidence_min"], 90.0)
        self.assertGreaterEqual(proof["word_confidence_max"], proof["word_confidence_min"])

    def test_exact_dependency_versions_are_pinned(self):
        self.assertEqual(
            {
                "poppler-utils": "24.02.0-1ubuntu9.9",
                "tesseract-ocr": "5.3.4-1build5",
                "tesseract-ocr-por": "1:4.1.0-2",
                "pypdf": "6.10.0",
            },
            self.data["successful_attempt"]["installed_packages"],
        )

    def test_hashes_are_exact_sha256_strings(self):
        hashes = self.data["successful_attempt"]["sha256"]
        self.assertEqual(
            {
                "synthetic_pdf": "c3b8a549e64b6a933a4e762a70e26ffd2d2633e3c9f140dbc709954905485272",
                "rendered_page_1": "28c86fe1035e100f1a3049375cc14ec78382c4567e7bf0dfdad8b8e97451c7fd",
                "ocr_tsv": "ce34e5ad0e8e7f53ed0a550e12765b97613b21c8a5a41c907e205f7a15ae25d3",
            },
            hashes,
        )
        for value in hashes.values():
            self.assertEqual(64, len(value))
            int(value, 16)

    def test_real_source_remains_unread_and_unauthorized(self):
        proof = self.data["successful_attempt"]
        self.assertEqual(0, proof["official_source_http_requests"])
        self.assertEqual(0, proof["real_ppa_reads"])
        self.assertFalse(proof["real_ppa_ocr"])
        self.assertFalse(self.data["real_source_read_authorized"])
        self.assertFalse(self.data["real_source_ocr_authorized"])
        self.assertEqual(
            "SEPARATE_REAL_SOURCE_OCR_GATE_REQUIRED",
            self.data["next_boundary"],
        )

    def test_single_use_workflow_is_removed_before_merge(self):
        self.assertFalse(WORKFLOW.exists())


if __name__ == "__main__":
    unittest.main()
