import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.product import (
    PRODUCT_FIELDS,
    ReportCard,
    build_product_report,
    render_csv,
    render_html,
    write_product_bundle,
)


GENERATED_AT = "2026-08-24T22:30:00+00:00"


class TestProductOutput(unittest.TestCase):
    def answer(self, **overrides):
        data = dict(
            status="ANSWERED",
            dado="Valor observado: 10",
            calculo="5 + 5 = 10",
            correspondencia="Correspondência documental candidata.",
            interpretacao="O valor observado é dez.",
            cautela="",
            fontes=("https://example.test/data?id=10",),
        )
        data.update(overrides)
        return AnswerContract(**data)

    def report(self, answers=None, **overrides):
        kwargs = dict(
            report_id="REL_TESTE_001",
            title="Relatório mínimo",
            scope="Teste unitário",
            generated_at=GENERATED_AT,
        )
        kwargs.update(overrides)
        return build_product_report(
            [self.answer()] if answers is None else answers,
            **kwargs,
        )

    def test_report_card_requires_timezone(self):
        with self.assertRaisesRegex(ValueError, "TIMEZONE"):
            ReportCard(
                report_id="R",
                title="T",
                scope="S",
                software_version="0.7.0",
                generated_at="2026-08-24T22:30:00",
                status="READY",
                row_count=1,
                formats=("application/json",),
            )

    def test_no_data_is_explicit(self):
        report = self.report(answers=[])
        self.assertEqual("NO_DATA", report["report_card"]["status"])
        self.assertEqual(0, report["report_card"]["row_count"])
        self.assertEqual([], report["rows"])

    def test_all_insufficient_evidence_is_explicit(self):
        report = self.report(
            answers=[self.answer(status="EVIDENCIA_INSUFICIENTE", dado="", cautela="Fonte insuficiente")]
        )
        self.assertEqual("EVIDENCIA_INSUFICIENTE", report["report_card"]["status"])

    def test_caution_prevents_clean_ready_status(self):
        report = self.report(answers=[self.answer(cautela="Comparação ainda não confirmada")])
        self.assertEqual("READY_WITH_CAUTION", report["report_card"]["status"])

    def test_clean_answer_is_ready(self):
        self.assertEqual("READY", self.report()["report_card"]["status"])

    def test_unknown_answer_status_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "ANSWER_STATUS_UNSUPPORTED"):
            self.report(answers=[self.answer(status="MAGIC_MATCH")])

    def test_sensitive_source_query_values_are_redacted(self):
        report = self.report(
            answers=[
                self.answer(
                    fontes=(
                        "https://example.test/data?id=10&access_token=supersecret&sig=abc123",
                    )
                )
            ]
        )
        source = report["rows"][0]["FONTES"]
        self.assertIn("id=10", source)
        self.assertIn("access_token=REDACTED", source)
        self.assertIn("sig=REDACTED", source)
        self.assertNotIn("supersecret", source)
        self.assertNotIn("abc123", source)

    def test_csv_preserves_answer_contract_columns(self):
        text = render_csv(self.report())
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(list(PRODUCT_FIELDS), rows[0])
        self.assertEqual("ANSWERED", rows[1][0])
        self.assertEqual("Valor observado: 10", rows[1][1])

    def test_html_escapes_user_facing_text(self):
        report = self.report(answers=[self.answer(interpretacao="<script>alert(1)</script>")])
        output = render_html(report)
        self.assertNotIn("<script>alert(1)</script>", output)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", output)

    def test_bundle_contains_expected_files_and_valid_pdf_signature(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "bundle"
            manifest = write_product_bundle(self.report(), out)
            expected = {
                "report.json",
                "report_card.json",
                "table.csv",
                "report.md",
                "report.html",
                "report.pdf",
                "manifest.json",
            }
            self.assertEqual(expected, {p.name for p in out.iterdir()})
            self.assertTrue((out / "report.pdf").read_bytes().startswith(b"%PDF-"))
            self.assertEqual("LOCAL_ONLY_NOT_PUBLISHED", manifest["publication_status"])
            self.assertEqual("08_OUTPUTS", manifest["drive_target"])
            self.assertEqual("table.csv", manifest["google_sheets_import_source"])

    def test_manifest_hashes_match_every_payload_file(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "bundle"
            manifest = write_product_bundle(self.report(), out)
            self.assertEqual(6, len(manifest["files"]))
            for item in manifest["files"]:
                path = out / item["name"]
                self.assertEqual(path.stat().st_size, item["bytes"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])

    def test_presentation_semantics_do_not_claim_truth(self):
        report = self.report()
        self.assertFalse(report["semantics"]["presentation_is_evidence"])
        self.assertTrue(report["semantics"]["zero_is_not_missing"])
        self.assertTrue(report["semantics"]["evidence_insufficient_is_explicit"])

    def test_report_json_keeps_utf8_semantics(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "bundle"
            write_product_bundle(self.report(), out)
            payload = json.loads((out / "report.json").read_text(encoding="utf-8"))
            self.assertIn("CÁLCULO", payload["columns"])
            self.assertIn("INTERPRETAÇÃO", payload["columns"])


if __name__ == "__main__":
    unittest.main()
