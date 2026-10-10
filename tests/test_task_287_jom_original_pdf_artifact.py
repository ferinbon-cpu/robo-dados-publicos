"""T0 tests for single-click JOM-original GitHub artifact workflow."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reportlab.pdfgen.canvas import Canvas

from scripts import download_jom_loa2027_pilot as task

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/jom-loa2027-five-original-pdfs-manual.yml"


def pdf_with_cover(edition: int) -> bytes:
    out = io.BytesIO()
    page = Canvas(out, pagesize=(595, 842))
    page.drawString(50, 780, f"JORNAL OFICIAL DO MUNICIPIO DE LIMEIRA — EDICAO {edition}")
    page.drawString(50, 750, f"EDICAO N. {edition} — 2026")
    page.showPage()
    page.save()
    return out.getvalue()


class FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes, url: str, mime: str = "application/pdf"):
        super().__init__(payload)
        self._url = url
        self.headers = {"Content-Type": mime, "Content-Length": str(len(payload))}

    def geturl(self):
        return self._url


class FakeTransport:
    def __init__(self, corrupted=None, cover_wrong=None, redirect=None):
        self.by_url = {row["document_url"]: int(row["edition"]) for row in task.exact_sources()}
        self.corrupted = corrupted
        self.cover_wrong = cover_wrong
        self.redirect = redirect
        self.calls = []

    def open(self, request, timeout):
        url = request.full_url
        self.calls.append(url)
        edition = self.by_url[url]
        payload = b"notpdf!" if edition == self.corrupted else pdf_with_cover(
            7777 if edition == self.cover_wrong else edition
        )
        return FakeResponse(payload, "https://evil.example/anything" if edition == self.redirect else url)


class TestManualJomArtifacts(unittest.TestCase):
    def test_exact_known_pinned_urls(self):
        x = task.exact_sources()
        self.assertEqual([int(i["edition"]) for i in x], [7211, 7208, 7209, 7210, 7212])
        self.assertTrue(all(i["document_url"].startswith(
            "https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/"
        ) for i in x))

    def test_context_fails_closed_without_manual_owner_confirmation(self):
        with self.assertRaisesRegex(task.PilotStop, "STOP_MANUAL"):
            task.validate_manual_context({})
        task.validate_manual_context({
            "JOM_OWNER_CONFIRM": "true", "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REF": "refs/heads/main", "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": "a"*40,
        })

    def test_fake_five_pdfs_validated_without_any_network(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = FakeTransport()
            result = task.collect_pilot(Path(temp), transport=fake)
            self.assertEqual(result["validated_count"], 5)
            self.assertEqual(result["failed_count"], 0)
            self.assertEqual(len(fake.calls), 5)
            self.assertEqual(len(list((Path(temp) / "originals").glob("*.pdf"))), 5)
            self.assertTrue(all(row["pages"] == 1 for row in result["documents"]))
            self.assertEqual(result["drive_write_count"], 0)
            self.assertEqual(result["retry_count"], 0)
            self.assertTrue((Path(temp) / "manifest.json").exists())

    def test_corrupt_pdf_is_not_stored_and_is_recorded_as_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            result = task.collect_pilot(Path(temp), transport=FakeTransport(corrupted=7211))
            self.assertEqual(result["validated_count"], 4)
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["documents"][0]["code"], "STOP_NOT_PDF")
            self.assertEqual(len(list((Path(temp) / "originals").glob("*.pdf"))), 4)

    def test_wrong_cover_edition_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            result = task.collect_pilot(Path(temp), transport=FakeTransport(cover_wrong=7208))
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["documents"][1]["code"], "STOP_COVER_EDITION_NOT_VERIFIED")

    def test_redirect_to_other_host_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            result = task.collect_pilot(Path(temp), transport=FakeTransport(redirect=7209))
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["documents"][2]["code"], "STOP_FINAL_URL_DRIFT")

    def test_tiny_bound_fails_before_persisting(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(task, "MAX_PER_PDF", 90):
                result = task.collect_pilot(Path(temp), transport=FakeTransport())
            self.assertEqual(result["validated_count"], 0)
            self.assertTrue(all(x["code"] == "STOP_CONTENT_LENGTH_LIMIT" for x in result["documents"]))
            self.assertEqual(list((Path(temp) / "originals").glob("*.pdf")), [])

    def test_manual_workflow_contract(self):
        src = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", src)
        self.assertIn("permissions:\n  contents: read", src)
        self.assertIn("autorizar_5_arquivos:", src)
        self.assertIn("retention-days: 7", src)
        self.assertIn("if-no-files-found: warn", src)
        self.assertIn("python scripts/download_jom_loa2027_pilot.py --out artifacts_jom", src)
        for forbidden in ("schedule:", "workflow_run:", "pull_request:", "repository_dispatch:", "secrets: inherit"):
            self.assertNotIn(forbidden, src)


if __name__ == "__main__":
    unittest.main()
