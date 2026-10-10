"""TASK288 offline regression: exact partition, bounds, provenance and owner gates."""
from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reportlab.pdfgen.canvas import Canvas
from scripts import download_jom_2026_archive_batch as target

ROOT = Path(__file__).resolve().parents[1]


def pdf_for(edition):
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=(595, 842))
    c.drawString(50, 780, f"JORNAL OFICIAL DO MUNICIPIO DE LIMEIRA EDICAO {edition}")
    c.showPage()
    c.save()
    return buf.getvalue()


class Response(io.BytesIO):
    def __init__(self, payload, url, mime="application/pdf", declared=None):
        super().__init__(payload)
        self._url = url
        self.headers = {"Content-Type": mime, "Content-Length": str(declared or len(payload))}
    def geturl(self):
        return self._url


class Transport:
    def __init__(self, invalid=None, redirect=None, wrong_cover=None, bad_mime=None):
        self.editions = {r["document_url"]: int(r["edition"])
                         for rs in target.batch_map().values() for r in rs}
        self.invalid, self.redirect = invalid, redirect
        self.wrong_cover, self.bad_mime = wrong_cover, bad_mime
        self.calls = []
    def open(self, request, timeout):
        url = request.full_url
        self.calls.append(url)
        edition = self.editions[url]
        payload = (
            b"not a real pdf body" * 20 if edition == self.invalid
            else pdf_for(9999 if edition == self.wrong_cover else edition)
        )
        return Response(payload,
                        "https://evil.invalid/new.pdf" if edition == self.redirect else url,
                        "text/html" if edition == self.bad_mime else "application/pdf")


class Task288Tests(unittest.TestCase):
    def test_81_unique_targets_in_9_explicit_batches(self):
        batches = target.batch_map()
        self.assertEqual(tuple(batches), target.BATCH_IDS)
        self.assertEqual(len(batches), 9)
        ids = [int(r["edition"]) for rows in batches.values() for r in rows]
        self.assertEqual(len(ids), 81)
        self.assertEqual(len(set(ids)), 81)
        self.assertTrue(set(ids).isdisjoint(target.ALREADY_PRESERVED))
        self.assertTrue(all(len(x) == 9 for x in batches.values()))
        self.assertTrue(all(r["document_url"].startswith(
            "https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/"
        ) for rs in batches.values() for r in rs))

    def test_owner_main_dispatch_validation(self):
        ok = {
            "JOM_2026_OWNER_CONFIRM": "true", "JOM_2026_BATCH": "B01",
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40,
        }
        target.validate_manual_context(ok, "B01")
        for bad in (
            {"JOM_2026_OWNER_CONFIRM": "false"},
            {"GITHUB_EVENT_NAME": "push"},
            {"GITHUB_REF": "refs/heads/feature"},
            {"GITHUB_RUN_ATTEMPT": "2"},
            {"JOM_2026_BATCH": "B09"},
        ):
            e = ok | bad
            with self.assertRaisesRegex(target.PilotStop, "STOP_MANUAL"):
                target.validate_manual_context(e, "B01")

    def test_success_9_pdfs_manifest_no_drive(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Transport()
            result = target.collect_batch(Path(td)/"out", "B01", transport=fake)
            self.assertEqual((result["validated_count"], result["failed_count"]), (9, 0))
            self.assertEqual(result["source_get_attempts"], 9)
            self.assertEqual(len(fake.calls), 9)
            self.assertEqual(result["drive_write_count"], 0)
            self.assertEqual(result["retry_count"], 0)
            self.assertEqual(len(list((Path(td)/"out"/"originals").glob("*.pdf"))), 9)
            self.assertTrue((Path(td)/"out"/"manifest.json").exists())
            self.assertTrue(all(x["sha256"] and x["pages"] == 1 for x in result["documents"]))

    def test_corrupt_pdf_no_persistence(self):
        edition = int(target.batch_map()["B01"][0]["edition"])
        with tempfile.TemporaryDirectory() as td:
            result = target.collect_batch(Path(td)/"out", "B01",
                                          transport=Transport(invalid=edition))
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["documents"][0]["code"], "STOP_NOT_PDF")
            self.assertEqual(len(list((Path(td)/"out"/"originals").glob("*.pdf"))), 8)

    def test_cover_mismatch_is_not_persisted(self):
        edition = int(target.batch_map()["B01"][2]["edition"])
        with tempfile.TemporaryDirectory() as td:
            result = target.collect_batch(Path(td)/"out", "B01",
                                          transport=Transport(wrong_cover=edition))
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["documents"][2]["code"], "STOP_COVER_EDITION_NOT_VERIFIED")

    def test_redirect_fails_closed(self):
        edition = int(target.batch_map()["B01"][3]["edition"])
        with tempfile.TemporaryDirectory() as td:
            result = target.collect_batch(Path(td)/"out", "B01",
                                          transport=Transport(redirect=edition))
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["documents"][3]["code"], "STOP_FINAL_URL_DRIFT")

    def test_bad_mime_fails_closed(self):
        edition = int(target.batch_map()["B01"][5]["edition"])
        with tempfile.TemporaryDirectory() as td:
            result = target.collect_batch(Path(td)/"out", "B01",
                                          transport=Transport(bad_mime=edition))
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["documents"][5]["code"], "STOP_MIME")

    def test_byte_budget_blocks_before_persisting(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Transport()
            with patch.object(target, "MAX_TOTAL", 10):
                result = target.collect_batch(Path(td)/"out", "B01", transport=fake)
            self.assertEqual(result["validated_count"], 0)
            self.assertEqual(len(list((Path(td)/"out"/"originals").glob("*.pdf"))), 0)
            self.assertLessEqual(result["source_get_attempts"], 9)

    def test_invalid_batch_has_no_effect(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(target.PilotStop, "STOP_INVALID_BATCH"):
                target.collect_batch(Path(td)/"out", "B00", transport=Transport())
            self.assertFalse((Path(td)/"out").exists())

    def test_new_workflow_is_manual_and_artifact_only(self):
        path = ROOT / ".github/workflows/jom-2026-81-originals-manual-batches.yml"
        txt = path.read_text(encoding="utf-8")
        for required in (
            "workflow_dispatch:", "autorizar_lote:", "contents: read",
            "persist-credentials: false", "retention-days: 7",
            "download_jom_2026_archive_batch.py", "Exigir completude 9 de 9",
            "if-no-files-found: warn",
        ):
            self.assertIn(required, txt)
        for forbidden in ("schedule:", "workflow_run:", "pull_request:",
                          "repository_dispatch:", "secrets: inherit", "push:"):
            self.assertNotIn(forbidden, txt)


if __name__ == "__main__":
    unittest.main()
