from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from robo_dados_publicos.manual_ingest.loa_extraction import (
    LoaExtractionStop,
    choose_extraction_route,
    load_loa_extraction_contract,
    validate_numeric_candidate,
    validate_ocr_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/loa_reproducible_extraction_readiness.v1.json"
FIXTURE = ROOT / "tests/fixtures/task_027_loa_reproducible_extraction_readiness.json"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def manifest_rows() -> list[dict]:
    config_hash = digest("tesseract-synthetic-config-v1")
    rows = []
    for page in range(1, 467):
        rows.append({
            "page_number": page,
            "page_image_sha256": digest(f"page-image-{page}"),
            "ocr_text_sha256": digest(f"ocr-text-{page}"),
            "ocr_text_chars": 100,
            "blank_page": False,
            "engine_name": "SYNTHETIC_TEST_ENGINE",
            "engine_version": "1.0.0",
            "engine_config_sha256": config_hash,
            "render_dpi": 300,
            "render_tool": "SYNTHETIC_RENDERER",
            "render_tool_version": "1.0.0",
            "critical_numeric_status": "REVIEW_REQUIRED" if page in {124, 127} else "NONE",
        })
    return rows


class TestTask027LoaReproducibleExtractionReadiness(unittest.TestCase):
    def setUp(self):
        self.contract = load_loa_extraction_contract(CONTRACT)
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_official_route_without_full_equivalence_fails_closed(self):
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_OFFICIAL_EQUIVALENCE_NOT_PROVEN"):
            choose_extraction_route(self.contract, self.fixture["official_unproven"])

    def test_fully_proven_official_route_only_reaches_review(self):
        result = choose_extraction_route(self.contract, self.fixture["official_proven_synthetic"])
        self.assertEqual(result["status"], "READY_FOR_SEPARATE_OFFICIAL_EQUIVALENCE_REVIEW")
        self.assertFalse(result["execution_authorized"])

    def test_ocr_design_only_reaches_separate_authorization_review(self):
        result = choose_extraction_route(self.contract, self.fixture["ocr_design"])
        self.assertEqual(result["status"], "READY_FOR_SEPARATE_DETERMINISTIC_OCR_AUTHORIZATION_REVIEW")
        self.assertFalse(result["execution_authorized"])

    def test_any_execute_true_is_blocked(self):
        proposal = deepcopy(self.fixture["ocr_design"])
        proposal["execute"] = True
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_EXTRACTION_EXECUTION_NOT_AUTHORIZED"):
            choose_extraction_route(self.contract, proposal)

    def test_ocr_input_hash_drift_fails_closed(self):
        proposal = deepcopy(self.fixture["ocr_design"])
        proposal["input_sha256"] = "0" * 64
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_OCR_INPUT_HASH_MISMATCH"):
            choose_extraction_route(self.contract, proposal)

    def test_complete_manifest_structure_passes_but_not_silver(self):
        result = validate_ocr_manifest(self.contract, manifest_rows())
        self.assertEqual(result["status"], "PASS_LOA_OCR_MANIFEST_STRUCTURE_ONLY")
        self.assertEqual(result["pages"], 466)
        self.assertEqual(result["critical_numeric_review_required_pages"], 2)
        self.assertFalse(result["silver_authorized"])

    def test_missing_page_fails_closed(self):
        rows = manifest_rows()[:-1]
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_OCR_MANIFEST_ROW_COUNT"):
            validate_ocr_manifest(self.contract, rows)

    def test_out_of_order_page_fails_closed(self):
        rows = manifest_rows()
        rows[0], rows[1] = rows[1], rows[0]
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_OCR_MANIFEST_PAGE_SEQUENCE"):
            validate_ocr_manifest(self.contract, rows)

    def test_mixed_engine_version_fails_closed(self):
        rows = manifest_rows()
        rows[200]["engine_version"] = "2.0.0"
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_OCR_MIXED_ENGINE_CONFIG"):
            validate_ocr_manifest(self.contract, rows)

    def test_empty_nonblank_page_fails_closed(self):
        rows = manifest_rows()
        rows[20]["ocr_text_chars"] = 0
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_OCR_EMPTY_NONBLANK_PAGE"):
            validate_ocr_manifest(self.contract, rows)

    def test_critical_numeric_value_without_independent_validation_stays_review_required(self):
        result = validate_numeric_candidate(self.contract, self.fixture["numeric_candidate_unreviewed"])
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertFalse(result["automatic_promotion"])

    def test_reviewed_numeric_candidate_still_does_not_auto_promote(self):
        result = validate_numeric_candidate(self.contract, self.fixture["numeric_candidate_reviewed"])
        self.assertEqual(result["status"], "VALIDATED_CANDIDATE_NOT_PROMOTED")
        self.assertFalse(result["automatic_promotion"])

    def test_numeric_candidate_requires_source_page(self):
        candidate = deepcopy(self.fixture["numeric_candidate_reviewed"])
        candidate["source_page"] = None
        with self.assertRaisesRegex(LoaExtractionStop, "STOP_LOA_NUMERIC_SOURCE_PAGE_REQUIRED"):
            validate_numeric_candidate(self.contract, candidate)


if __name__ == "__main__":
    unittest.main()
