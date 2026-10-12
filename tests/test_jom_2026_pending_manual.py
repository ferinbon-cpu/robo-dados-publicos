"""TASK296 offline contract and fake-transport tests; never perform network GETs."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import download_jom_2026_pending_manual as mod


class FakeResponse(io.BytesIO):
    def __init__(self, body, url, mime="application/pdf", declared=None):
        super().__init__(body)
        self.final_url = url
        self.headers = {"Content-Type": mime}
        if declared is not None:
            self.headers["Content-Length"] = str(declared)

    def geturl(self):
        return self.final_url


class FakeTransport:
    def __init__(self, *, bad_at=-1, mime_bad=False, redirect_bad=False, http_status=None):
        self.calls = []
        self.bad_at = bad_at
        self.mime_bad = mime_bad
        self.redirect_bad = redirect_bad
        self.http_status = http_status
        self.data = b"%PDF-" + b"x" * 200

    def open(self, request, timeout):
        self.calls.append(request.full_url)
        idx = len(self.calls) - 1
        if idx == self.bad_at and self.http_status is not None:
            raise HTTPError(request.full_url, self.http_status, "TEST_SIMULATED", {}, None)
        return FakeResponse(
            self.data,
            request.full_url + "/redirect" if idx == self.bad_at and self.redirect_bad else request.full_url,
            mime="text/html" if idx == self.bad_at and self.mime_bad else "application/pdf",
            declared=len(self.data),
        )


class TestTask296(unittest.TestCase):
    def test_fixture_complete_and_exact_batches(self):
        sources = mod.load_sources()
        self.assertEqual(len(sources), 88)
        self.assertEqual([r["edition"] for r in sources], list(mod.EXPECTED_EDITIONS))
        batches = mod.batch_map()
        self.assertEqual(list(batches), list(mod.BATCH_IDS))
        self.assertEqual([len(x) for x in batches.values()], [9] * 9 + [7])
        self.assertEqual([r["edition"] for r in batches["P01"]], list(range(7152, 7161)))
        self.assertTrue(all(r["expected_date"] for r in batches["P01"]))
        self.assertEqual(len({r["url"] for r in sources}), 88)

    def test_manual_context_rejects_missing_or_wrong_authorization(self):
        base = {
            "JOM296_BATCH": "P01", "JOM296_OWNER_CONFIRM": "true",
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
            "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40,
        }
        mod.require_manual_owner_context(base, "P01")
        for key, value in (
            ("JOM296_OWNER_CONFIRM", "false"),
            ("GITHUB_EVENT_NAME", "push"),
            ("GITHUB_REF", "refs/heads/other"),
            ("GITHUB_RUN_ATTEMPT", "2"),
            ("GITHUB_SHA", "not_sha"),
            ("JOM296_BATCH", "P02"),
        ):
            changed = dict(base)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(mod.PilotStop):
                mod.require_manual_owner_context(changed, "P01")

    def _mutated_fixture(self, update):
        src = json.loads(mod.FIXTURE.read_text(encoding="utf-8"))
        update(src)
        root = tempfile.TemporaryDirectory()
        path = Path(root.name) / "bad.json"
        path.write_text(json.dumps(src), encoding="utf-8")
        return root, path

    def test_duplicate_url_is_stopped_before_network(self):
        def mutate(src):
            src["sources"][2]["url"] = src["sources"][1]["url"]
        tmp, path = self._mutated_fixture(mutate)
        with tmp, self.assertRaisesRegex(mod.PilotStop, "STOP_FIXTURE_DUPLICATE_URL"):
            mod.load_sources(path)

    def test_wrong_host_stops(self):
        def mutate(src):
            src["sources"][2]["url"] = "https://evil.invalid/" + src["sources"][2]["url"].split("/")[-1]
        tmp, path = self._mutated_fixture(mutate)
        with tmp, self.assertRaisesRegex(mod.PilotStop, "STOP_SOURCE_URL_DRIFT"):
            mod.load_sources(path)

    def test_missing_edition_stops(self):
        def mutate(src):
            src["sources"][2]["edition"] = 98765
        tmp, path = self._mutated_fixture(mutate)
        with tmp, self.assertRaisesRegex(mod.PilotStop, "STOP_FIXTURE_EDITION_SET_OR_ORDER"):
            mod.load_sources(path)

    @patch.object(mod, "inspect_pdf", return_value=2)
    def test_fake_transport_success_7_downloads_no_drive(self, _inspect):
        fake = FakeTransport()
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.collect_batch(Path(tmp) / "result", "P10", transport=fake)
            self.assertEqual(result["requested_count"], 7)
            self.assertEqual(result["validated_count"], 7)
            self.assertEqual(result["failed_count"], 0)
            self.assertEqual(result["get_attempts"], 7)
            self.assertEqual(result["retry_count"], 0)
            self.assertEqual(result["drive_write_count"], 0)
            self.assertEqual(len(fake.calls), 7)
            self.assertEqual(result["documents"][0]["sha256"], hashlib.sha256(fake.data).hexdigest())
            self.assertEqual(len(list((Path(tmp) / "result/originals").glob("*.pdf"))), 7)
            self.assertTrue((Path(tmp) / "result/manifest.json").exists())
            self.assertTrue(result["artifact_expiring_not_bronze_custody"])

    @patch.object(mod, "inspect_pdf", return_value=2)
    def test_bad_mime_partial_manifest_no_retry(self, _inspect):
        fake = FakeTransport(bad_at=2, mime_bad=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.collect_batch(Path(tmp) / "result", "P10", transport=fake)
            self.assertEqual(result["validated_count"], 6)
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["get_attempts"], 7)
            self.assertEqual(len(fake.calls), 7)
            self.assertEqual(result["documents"][2]["code"], "STOP_RESPONSE_MIME")
            self.assertEqual(len(list((Path(tmp) / "result/originals").glob("*.part"))), 0)

    @patch.object(mod, "inspect_pdf", return_value=2)
    def test_redirect_drift_no_silent_follow(self, _inspect):
        fake = FakeTransport(bad_at=0, redirect_bad=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.collect_batch(Path(tmp) / "result", "P10", transport=fake)
            self.assertEqual(result["validated_count"], 6)
            self.assertEqual(result["documents"][0]["code"], "STOP_FINAL_URL_DRIFT")


    @patch.object(mod, "inspect_pdf", return_value=2)
    def test_http_403_stops_after_one_get_without_retry(self, _inspect):
        fake = FakeTransport(bad_at=0, http_status=403)
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.collect_batch(Path(tmp) / "result", "P03", transport=fake)
            self.assertEqual(result["requested_count"], 9)
            self.assertEqual(result["validated_count"], 0)
            self.assertEqual(result["failed_count"], 9)
            self.assertEqual(result["get_attempts"], 1)
            self.assertEqual(result["retry_count"], 0)
            self.assertEqual(result["source_http_circuit_breaker_status"], 403)
            self.assertEqual(result["not_attempted_due_to_http_circuit_breaker"], 8)
            self.assertEqual(result["documents"][0]["code"], "HTTP_403")
            self.assertEqual(result["documents"][0]["http_status"], 403)
            self.assertTrue(all(
                r["request_attempts"] == 0 and
                r["status"] == "NOT_ATTEMPTED_SOURCE_HTTP_CIRCUIT_BREAKER"
                for r in result["documents"][1:]
            ))
            self.assertEqual(fake.calls, [mod.batch_map()["P03"][0]["url"]])

    @patch.object(mod, "inspect_pdf", return_value=2)
    def test_http_429_and_502_activate_circuit_breaker(self, _inspect):
        for code in (429, 502):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as tmp:
                fake = FakeTransport(bad_at=0, http_status=code)
                result = mod.collect_batch(Path(tmp) / "result", "P10", transport=fake)
                self.assertEqual(len(fake.calls), 1)
                self.assertEqual(result["source_http_circuit_breaker_status"], code)
                self.assertEqual(result["not_attempted_due_to_http_circuit_breaker"], 6)
                self.assertEqual(result["documents"][0]["code"], f"HTTP_{code}")

    @patch.object(mod, "inspect_pdf", return_value=2)
    def test_http_404_does_not_infer_global_blockage(self, _inspect):
        fake = FakeTransport(bad_at=0, http_status=404)
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.collect_batch(Path(tmp) / "result", "P10", transport=fake)
            self.assertEqual(result["validated_count"], 6)
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["get_attempts"], 7)
            self.assertEqual(result["not_attempted_due_to_http_circuit_breaker"], 0)
            self.assertIsNone(result["source_http_circuit_breaker_status"])
            self.assertEqual(result["documents"][0]["code"], "HTTP_404")
            self.assertEqual(len(fake.calls), 7)

    def test_no_network_for_invalid_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(mod.PilotStop):
                mod.collect_batch(Path(tmp) / "result", "INVALID", transport=FakeTransport())


if __name__ == "__main__":
    unittest.main()
