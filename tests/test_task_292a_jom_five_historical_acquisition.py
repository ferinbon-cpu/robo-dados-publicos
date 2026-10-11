"""TASK292A offline transport simulations: five pinned originals and fail-closed."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from reportlab.pdfgen.canvas import Canvas
from scripts import task292a_jom_2026_five_historical_pdf_acquisition as target

ROOT = Path(__file__).resolve().parents[1]


def pdf_for(edition: int) -> bytes:
    b = io.BytesIO()
    # invariant=1 stabilizes CreationDate/document ID so two independent
    # renderings of the same synthetic PDF have identical bytes and SHA256.
    doc = Canvas(b, invariant=1)
    doc.drawString(20, 770, f"JORNAL OFICIAL MUNICIPIO LIMEIRA EDICAO {edition}")
    doc.showPage()
    doc.save()
    return b.getvalue()


class Response(io.BytesIO):
    def __init__(self, payload: bytes, url: str, *, final_url=None, mime="application/pdf"):
        super().__init__(payload)
        self.url = url
        self.final_url = final_url or url
        self.headers = {"Content-Type": mime, "Content-Length": str(len(payload))}

    def geturl(self):
        return self.final_url


class FakeTransport:
    def __init__(self, rows, failed=None, wrong_cover=None, redirect=None, mime_fail=None):
        self.rows = {x["document_url"]: x["edition"] for x in rows}
        self.failed = failed
        self.wrong_cover = wrong_cover
        self.redirect = redirect
        self.mime_fail = mime_fail
        self.calls = []

    def open(self, request, timeout=35):
        url = request.full_url
        edition = self.rows[url]
        self.calls.append(url)
        if edition == self.failed:
            raise HTTPError(url, 403, "Forbidden", None, None)
        return Response(
            pdf_for(9999 if edition == self.wrong_cover else edition), url,
            final_url="https://example.org/moved.pdf" if edition == self.redirect else None,
            mime="text/html" if edition == self.mime_fail else "application/pdf",
        )


def fake_sources():
    rows = target.exact_sources()
    prepared = []
    for r in rows:
        row = r.copy()
        if row["edition"] == 7151:
            payload = pdf_for(7151)
            row["historical_sha256"] = hashlib.sha256(payload).hexdigest()
            row["historical_bytes"] = len(payload)
            row["historical_pages"] = 1
        prepared.append(row)
    return prepared


class TestTask292A(unittest.TestCase):
    def test_pinned_sources_match_provenance_without_guessing(self):
        sources = target.exact_sources()
        self.assertEqual([x["edition"] for x in sources], list(target.EDITIONS))
        self.assertIsNone(sources[0]["source_id"])
        self.assertEqual(sources[0]["historical_sha256"], target.KNOWN_7151_SHA)
        self.assertEqual(sources[0]["historical_bytes"], target.KNOWN_7151_SIZE)
        self.assertEqual(sources[0]["historical_pages"], target.KNOWN_7151_PAGES)
        self.assertEqual([x["source_id"] for x in sources[1:]],
                         ["LIMEIRA_JO_07321", "LIMEIRA_JO_07322",
                          "LIMEIRA_JO_07323", "LIMEIRA_JO_07324"])
        self.assertEqual(len({x["document_url"] for x in sources}), 5)
        self.assertTrue(all(x["document_url"].startswith(
            "https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/")
            for x in sources))

    def test_manual_dispatch_main_first_attempt_only(self):
        env = {
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40,
            "JOM292A_OWNER_CONFIRM": "true",
        }
        target.validate_context(env)
        for change in [{"GITHUB_EVENT_NAME": "push"}, {"GITHUB_REF": "refs/heads/develop"},
                       {"GITHUB_RUN_ATTEMPT": "2"}, {"JOM292A_OWNER_CONFIRM": "false"}]:
            with self.assertRaisesRegex(target.PilotStop, "STOP_292A_MANUAL"):
                target.validate_context(env | change)

    def test_success_five_sources_exact_one_get_each_and_parts(self):
        rows = fake_sources()
        with tempfile.TemporaryDirectory() as td:
            with patch.object(target, "exact_sources", return_value=rows):
                transport = FakeTransport(rows)
                d = target.collect(Path(td) / "out", transport=transport)
            self.assertEqual(d["validated_count"], 5)
            self.assertEqual(d["failed_count"], 0)
            self.assertEqual(d["source_get_attempts"], 5)
            self.assertEqual((d["retry_count"], d["index_get_count"], d["drive_write_count"]),
                             (0, 0, 0))
            self.assertEqual(transport.calls, [x["document_url"] for x in rows])
            for row in d["documents"]:
                self.assertEqual(row["status"], "VALIDATED_ORIGINAL")
                self.assertEqual(row["pages"], 1)
                ed = row["edition"]
                self.assertEqual(len(row["parts"]), 1)
                loc = Path(td) / "out" / "pieces" / str(ed) / "part01"
                part = loc / f"JOM_{ed}_2026_ORIGINAL.pdf"
                self.assertEqual(hashlib.sha256(part.read_bytes()).hexdigest(), row["sha256"])
                self.assertEqual(json.loads((loc / "manifest_excerpt.json").read_text())["edition"], ed)
            self.assertFalse((Path(td)/"out"/"_working").exists())
            self.assertTrue((Path(td)/"out"/"manifest.json").exists())

    def test_7151_historical_sha_required(self):
        rows = fake_sources()
        rows[0]["historical_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as td:
            with patch.object(target, "exact_sources", return_value=rows):
                d = target.collect(Path(td)/"out", transport=FakeTransport(rows))
            self.assertEqual(d["validated_count"], 4)
            self.assertEqual(d["documents"][0]["code"],
                             "STOP_292A_HISTORICAL_7151_HASH_SIZE_PAGES")
            self.assertFalse((Path(td)/"out"/"pieces"/"7151").exists())

    def test_403_redirect_bad_cover_fail_only_document(self):
        rows = fake_sources()
        for key, item, code in [
            ("failed", 7321, "HTTPError"),
            ("redirect", 7322, "STOP_292A_FINAL_URL_DRIFT"),
            ("wrong_cover", 7323, "STOP_COVER_EDITION_NOT_VERIFIED"),
            ("mime_fail", 7324, "STOP_292A_MIME"),
        ]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                with patch.object(target, "exact_sources", return_value=rows):
                    d = target.collect(Path(td)/"out",
                                       transport=FakeTransport(rows, **{key: item}))
                self.assertEqual(d["validated_count"], 4)
                self.assertIn(code, next(x for x in d["documents"] if x["edition"] == item)["code"])
                self.assertFalse((Path(td)/"out"/"pieces"/str(item)).exists())

    def test_90mib_split_is_reversible_and_self_hashing(self):
        rows = fake_sources()
        fixture_size = len(pdf_for(7151))
        with tempfile.TemporaryDirectory() as td:
            with patch.object(target, "exact_sources", return_value=rows), \
                 patch.object(target, "SEGMENT_BYTES", (fixture_size + 1)//2):
                d = target.collect(Path(td)/"out", transport=FakeTransport(rows))
            self.assertEqual(d["validated_count"], 5)
            record = d["documents"][0]
            self.assertEqual(len(record["parts"]), 2)
            restored = b"".join(
                (Path(td)/"out"/"pieces"/"7151"/f"part{x['part_number']:02d}"/x["file_name"]).read_bytes()
                for x in record["parts"])
            self.assertEqual(hashlib.sha256(restored).hexdigest(), record["sha256"])
            self.assertEqual(len(restored), record["bytes"])

    def test_existing_output_stops_before_network(self):
        rows = fake_sources()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)/"out"
            out.mkdir()
            t = FakeTransport(rows)
            with patch.object(target, "exact_sources", return_value=rows):
                with self.assertRaisesRegex(target.PilotStop, "OUTPUT_EXISTS"):
                    target.collect(out, transport=t)
            self.assertFalse(t.calls)

    def test_workflow_policy_and_limits(self):
        policy = json.loads((ROOT/"config/automation_policy.v1.json").read_text())
        gate = next(x for x in policy["gates"]
                    if x["id"] == "JOM_2026_TASK292A_FIVE_HISTORICALLY_PROVEN_PDFS_MANUAL")
        self.assertFalse(gate["auto_allowed"])
        self.assertTrue(gate["human_confirmation_required"])
        self.assertEqual(gate["tier"], "T2_CREATE_ONLY")
        self.assertEqual(gate["effects"]["source_get_count_max"], 5)
        self.assertEqual(gate["effects"]["github_artifact_create_count_max"], 16)
        self.assertEqual(gate["effects"]["drive_writes"], 0)
        path = ROOT/".github/workflows/task292a-jom-2026-five-proven-originals-manual.yml"
        workflow = path.read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("confirmar_cinco_joms_292a", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("scripts/task292a_jom_2026_five_historical_pdf_acquisition.py", workflow)
        self.assertEqual(workflow.count("uses: actions/upload-artifact@"), 16)
        for banned in ["schedule:", "workflow_run:", "repository_dispatch:", "push:",
                       "secrets: inherit"]:
            self.assertNotIn(banned, workflow)

    def test_cli_direct_execution_rejects_unconfirmed_without_import_failure(self):
        env = os.environ.copy()
        env.update({
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REF": "refs/heads/main", "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_SHA": "a" * 40, "JOM292A_OWNER_CONFIRM": "false",
        })
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)/"uncreated"
            r = subprocess.run(
                [sys.executable, "scripts/task292a_jom_2026_five_historical_pdf_acquisition.py",
                 "--out", str(out)], cwd=ROOT, env=env, text=True,
                capture_output=True, timeout=15, check=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("STOP_292A_MANUAL_OWNER_MAIN_ONE_SHOT", r.stderr)
            self.assertNotIn("ModuleNotFoundError", r.stderr)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
