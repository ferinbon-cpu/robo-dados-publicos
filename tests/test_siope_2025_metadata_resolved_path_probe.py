from __future__ import annotations

import copy
from datetime import datetime, timezone
from email.message import Message
import json
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

from robo_dados_publicos.sources.siope_2025_metadata_resolved_path_probe import (
    AUTH_PATH,
    RESOLVED_URL,
    MetadataResolvedPathProbe,
    MetadataResolvedPathProbeError,
    validate_authorization_document,
    validate_preparation_contract,
)

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "config" / "siope_2025_metadata_resolved_path_probe_preparation.v1.json"
TEMPLATE = ROOT / "config" / "siope_2025_metadata_resolved_path_probe_authorization.template.v1.json"
POLICY = ROOT / "config" / "automation_policy.v1.json"
RUNNER = ROOT / "scripts" / "run_siope_2025_metadata_resolved_path_probe.py"
GATE = ROOT / "scripts" / "github_siope_2025_metadata_resolved_path_probe_preparation_gate.py"


class FakeResponse:
    def __init__(self, *, body: bytes, status: int = 206, headers: dict[str, str] | None = None, url: str = RESOLVED_URL):
        self._body = body
        self.status = status
        self.headers = headers or {}
        self.url = url

    def read(self, size: int = -1) -> bytes:
        return self._body if size < 0 else self._body[:size]

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class Task009CResolvedPathProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prep = json.loads(PREP.read_text(encoding="utf-8"))
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.policy = json.loads(POLICY.read_text(encoding="utf-8"))

    def test_preparation_contract_passes_offline(self) -> None:
        validate_preparation_contract(self.prep, self.template, self.policy)
        self.assertFalse(self.prep["live_execution_authorized_by_task_009c"])
        self.assertFalse(self.template["authorized"])
        self.assertEqual(self.prep["effects_task_009c"]["source_get_count"], 0)

    def test_preparation_gate_cli_passes_without_remote_effects(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(GATE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["status"], "PASS_TASK009C_RESOLVED_PATH_PREPARATION_OFFLINE")
        self.assertEqual(payload["source_get_count"], 0)
        self.assertFalse(payload["live_execution_authorized"])

    def test_cli_dry_run_matches_workflow_execution_shape(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(RUNNER), "--mode", "dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["status"], "PASS_TASK009C_RESOLVED_PATH_PROBE_DRY_RUN_NO_NETWORK")
        self.assertEqual(payload["source_get_count"], 0)
        self.assertFalse(payload["live_execution_authorized"])

    def test_missing_authorization_fails_closed(self) -> None:
        with self.assertRaises(MetadataResolvedPathProbeError):
            validate_authorization_document(
                None,
                requested_authorization_id="SIOPE2025-METADATA-DIRECT-PROBE-TEST01",
                current_head_sha="1" * 40,
                current_parent_sha="2" * 40,
                changed_paths_since_base=[AUTH_PATH],
                current_workflow_run_number=1,
                current_workflow_run_attempt=1,
                current_workflow_ref="refs/heads/main",
                now_utc=datetime(2026, 8, 28, 12, 30, tzinfo=timezone.utc),
            )

    def test_direct_partial_zip_probe_is_sanitized(self) -> None:
        body = b"PK\x03\x04" + b"x" * 100
        response = FakeResponse(
            body=body,
            headers={
                "Content-Type": "application/zip",
                "Content-Length": str(len(body)),
                "Content-Range": "bytes 0-103/54321",
            },
        )
        result = MetadataResolvedPathProbe(opener=lambda req, timeout: response).run().sanitized()
        self.assertEqual(result["source_get_count"], 1)
        self.assertEqual(result["http_status"], 206)
        self.assertEqual(result["content_range_total"], 54321)
        self.assertTrue(result["zip_magic_present"])
        self.assertNotIn("raw_body", result)
        self.assertFalse(result["archive_persisted"])

    def test_further_redirect_is_sanitized_and_not_followed(self) -> None:
        headers = Message()
        headers["Location"] = "https://fnde.sharepoint.com/next/package.zip?token=never-persist"

        def opener(req, timeout):
            raise HTTPError(req.full_url, 302, "Found", headers, None)

        result = MetadataResolvedPathProbe(opener=opener).run().sanitized()
        self.assertEqual(result["result_kind"], "REDIRECT_STOP_REQUIRES_NEW_AUTHORIZATION")
        self.assertEqual(result["source_get_count"], 1)
        self.assertEqual(result["redirect_host"], "fnde.sharepoint.com")
        self.assertEqual(result["redirect_path"], "/next/package.zip")
        self.assertNotIn("token", json.dumps(result))

    def test_url_drift_stops_before_transport(self) -> None:
        called = False

        def opener(req, timeout):
            nonlocal called
            called = True
            raise AssertionError("must not be called")

        with self.assertRaises(MetadataResolvedPathProbeError):
            MetadataResolvedPathProbe(opener=opener).run(url="https://example.com/file.zip")
        self.assertFalse(called)

    def test_html_interstitial_fails_closed(self) -> None:
        response = FakeResponse(body=b"<html>login</html>", headers={"Content-Type": "text/html"})
        with self.assertRaises(MetadataResolvedPathProbeError) as ctx:
            MetadataResolvedPathProbe(opener=lambda req, timeout: response).run()
        self.assertEqual(ctx.exception.request_count, 1)

    def test_range_ignored_large_200_fails_closed(self) -> None:
        response = FakeResponse(
            body=b"PK\x03\x04" + b"x" * 5000,
            status=200,
            headers={"Content-Type": "application/zip", "Content-Length": "5004"},
        )
        with self.assertRaises(MetadataResolvedPathProbeError) as ctx:
            MetadataResolvedPathProbe(opener=lambda req, timeout: response).run()
        self.assertEqual(ctx.exception.request_count, 1)

    def _authorized(self) -> dict:
        value = copy.deepcopy(self.template)
        value.update({
            "authorized": True,
            "authorization_id": "SIOPE2025-METADATA-DIRECT-PROBE-TEST01",
            "approved_by": "ferinbon-cpu",
            "approved_at_utc": "2026-08-28T12:00:00Z",
            "expires_at_utc": "2026-08-28T13:00:00Z",
            "authorized_base_sha": "a" * 40,
            "authorized_workflow_run_number": 7,
        })
        return value

    def test_exact_one_shot_authorization_passes(self) -> None:
        validate_authorization_document(
            self._authorized(),
            requested_authorization_id="SIOPE2025-METADATA-DIRECT-PROBE-TEST01",
            current_head_sha="b" * 40,
            current_parent_sha="a" * 40,
            changed_paths_since_base=[AUTH_PATH],
            current_workflow_run_number=7,
            current_workflow_run_attempt=1,
            current_workflow_ref="refs/heads/main",
            now_utc=datetime(2026, 8, 28, 12, 30, tzinfo=timezone.utc),
        )

    def test_extra_changed_path_and_rerun_are_blocked(self) -> None:
        for paths, attempt in [([AUTH_PATH, "unexpected.txt"], 1), ([AUTH_PATH], 2)]:
            with self.assertRaises(MetadataResolvedPathProbeError):
                validate_authorization_document(
                    self._authorized(),
                    requested_authorization_id="SIOPE2025-METADATA-DIRECT-PROBE-TEST01",
                    current_head_sha="b" * 40,
                    current_parent_sha="a" * 40,
                    changed_paths_since_base=paths,
                    current_workflow_run_number=7,
                    current_workflow_run_attempt=attempt,
                    current_workflow_ref="refs/heads/main",
                    now_utc=datetime(2026, 8, 28, 12, 30, tzinfo=timezone.utc),
                )


if __name__ == "__main__":
    unittest.main()
