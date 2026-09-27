from __future__ import annotations

from io import BytesIO
from pathlib import Path
import hashlib
import json
import unittest

from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from robo_dados_publicos.manual_ingest.planning_budget import (
    ManualIngestStop,
    ManualSourceContract,
    extract_ppa_eiti_program,
    inspect_pdf_text_layer,
    load_manual_ingest_contract,
    parse_ldo_structural_markers,
    validate_financial_identity,
    validate_source_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "task_025_manual_supervised_ingest_f01.json"
CONTRACT = ROOT / "config" / "manual_supervised_ingest_f01.v1.json"


class TestTask025ManualSupervisedIngestF01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_contract_pins_exact_three_sources(self):
        sources = load_manual_ingest_contract(CONTRACT)
        self.assertEqual([s.family for s in sources], ["PPA", "LDO", "LOA"])
        self.assertEqual(
            [s.expected_pages for s in sources],
            [105, 37, 466],
        )
        self.assertEqual(
            [s.expected_bytes for s in sources],
            [4856211, 11534048, 24203962],
        )

    def test_contract_rejects_non_source_authority(self):
        raw = {
            "source_id": "BAD",
            "family": "PPA",
            "legal_number": "X",
            "reference_period": "2026",
            "expected_sha256": "a" * 64,
            "expected_bytes": 1,
            "expected_pages": 1,
            "source_type": "DERIVED",
        }
        with self.assertRaisesRegex(ManualIngestStop, "STOP_MANUAL_SOURCE_MUST_BE_SOURCE"):
            ManualSourceContract.from_mapping(raw)

    def test_validate_source_bytes_exact(self):
        buf = BytesIO()
        pdf = canvas.Canvas(buf)
        pdf.drawString(72, 720, "synthetic public planning fixture")
        pdf.save()
        payload = buf.getvalue()
        contract = ManualSourceContract(
            source_id="SYNTHETIC",
            family="PPA",
            legal_number="SYNTHETIC",
            reference_period="2026",
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            expected_bytes=len(payload),
            expected_pages=1,
        )
        result = validate_source_bytes(contract, payload)
        self.assertEqual(result.status, "PASS_SOURCE_BYTES_VERIFIED")
        self.assertEqual(result.pages, 1)

    def test_validate_source_bytes_fails_closed_on_hash(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        buf = BytesIO()
        writer.write(buf)
        payload = buf.getvalue()
        contract = ManualSourceContract(
            source_id="SYNTHETIC",
            family="LOA",
            legal_number="SYNTHETIC",
            reference_period="2026",
            expected_sha256="0" * 64,
            expected_bytes=len(payload),
            expected_pages=1,
        )
        with self.assertRaisesRegex(ManualIngestStop, "STOP_MANUAL_SOURCE_IMMUTABLE_MISMATCH"):
            validate_source_bytes(contract, payload)

    def test_image_only_pdf_is_detected_without_ocr_guessing(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        buf = BytesIO()
        writer.write(buf)
        probe = inspect_pdf_text_layer(buf.getvalue())
        self.assertEqual(probe["pages"], 1)
        self.assertEqual(probe["text_pages"], 0)
        self.assertFalse(probe["has_text_layer"])

    def test_ppa_program_and_eiti_indicator(self):
        parsed = extract_ppa_eiti_program(self.fixture["ppa_text"])
        self.assertEqual(parsed["program_code"], "2001")
        self.assertEqual(parsed["responsible_unit_code"], "10.00.00")
        self.assertEqual(
            [
                parsed["indicator"]["recent"],
                parsed["indicator"]["2026"],
                parsed["indicator"]["2027"],
                parsed["indicator"]["2028"],
                parsed["indicator"]["2029"],
                parsed["indicator"]["final_ppa"],
            ],
            [52, 53, 55, 57, 59, 59],
        )
        self.assertEqual(
            parsed["known_text_extraction_review"],
            "PARSER_REVIEW_REQUIRED_TRANSPORTE_ENSINO_MEDIO",
        )

    def test_ppa_target_drift_stops(self):
        with self.assertRaisesRegex(ManualIngestStop, "STOP_PPA_EITI_TARGET_DRIFT"):
            extract_ppa_eiti_program(self.fixture["ppa_target_drift_text"])

    def test_ldo_required_structure(self):
        parsed = parse_ldo_structural_markers(self.fixture["ldo_text"])
        self.assertEqual(parsed["status"], "PASS_LDO_REQUIRED_STRUCTURE")
        self.assertTrue(all(parsed["markers"].values()))

    def test_ldo_missing_structure_stops(self):
        with self.assertRaisesRegex(ManualIngestStop, "STOP_LDO_REQUIRED_STRUCTURE_MISSING"):
            parse_ldo_structural_markers("LEI 7.141/2025. DAS METAS FISCAIS.")

    def test_program_level_bridge_is_not_financial_identity(self):
        result = validate_financial_identity(self.fixture["financial_program_only"])
        self.assertEqual(result["status"], "EVIDENCIA_INSUFICIENTE")
        self.assertFalse(result["program_level_bridge_is_financial_identity"])
        self.assertIn("explicit_action_or_subaction", result["missing"])
        self.assertIn("paid", result["missing"])

    def test_full_chain_can_only_prove_when_all_fields_are_present(self):
        result = validate_financial_identity(self.fixture["financial_full_chain"])
        self.assertEqual(result["status"], "FINANCIAL_IDENTITY_PROVEN")
        self.assertEqual(result["missing"], [])


if __name__ == "__main__":
    unittest.main()
