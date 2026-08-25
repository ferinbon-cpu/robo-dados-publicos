from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.sources.siope_artifact_download_event_diagnostics import (
    _sanitize_download_event,
    diagnose_artifact_download_event,
)
from robo_dados_publicos.sources.siope_artifact_download_runtime_route_probe import load_artifact_download_runtime_route_probe_config
from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_artifact_download_runtime_route_probe_gate.json"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-artifact-download-event-diagnostics-gate.yml"
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_artifact_download_event_diagnostics.py"
SCRIPT = ROOT / "scripts" / "github_siope_artifact_download_event_diagnostics_gate.py"


class FakeRuntime:
    def __init__(self, raw: dict):
        self.raw = raw

    def run_probe(self, config: dict) -> dict:
        return dict(self.raw)


def base_raw(events: list[dict] | None = None) -> dict:
    return {
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "click_executed": True,
        "browser_download_denied": True,
        "download_events_enabled": True,
        "verified_metadata_network_sent": True,
        "verified_metadata_request_count": 1,
        "post_click_static_assets_continued_count": 0,
        "blocked_requests": [],
        "download_events": list(events or []),
        "candidate_route_network_sent": False,
        "artifact_downloaded": False,
    }


class TestM7SiopeArtifactDownloadEventDiagnostics(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_artifact_download_runtime_route_probe_config(CONFIG)

    def test_http_event_is_sanitized_without_query_values(self) -> None:
        shape = _sanitize_download_event(
            "https://www.fnde.gov.br/download/file.gz?token=SECRET&key=VALUE",
            "SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            self.config,
        )
        text = json.dumps(shape, sort_keys=True)
        self.assertEqual(shape["route_without_query"], "https://www.fnde.gov.br/download/file.gz")
        self.assertEqual(shape["query_keys"], ["key", "token"])
        self.assertTrue(shape["suggested_filename_matches_declared"])
        self.assertNotIn("SECRET", text)
        self.assertNotIn("VALUE", text)

    def test_blob_event_keeps_only_scheme_and_declared_filename_match(self) -> None:
        shape = _sanitize_download_event(
            "blob:https://www.fnde.gov.br/opaque-secret-value",
            "SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            self.config,
        )
        text = json.dumps(shape, sort_keys=True)
        self.assertEqual(shape["scheme"], "blob")
        self.assertIsNone(shape["route_without_query"])
        self.assertNotIn("opaque-secret-value", text)

    def test_observed_event_passes_with_download_denied(self) -> None:
        event = _sanitize_download_event(
            "blob:https://www.fnde.gov.br/opaque",
            "SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            self.config,
        )
        result = diagnose_artifact_download_event(self.config, runtime=FakeRuntime(base_raw([event])))
        self.assertEqual(result["download_event_count"], 1)
        self.assertEqual(result["diagnostic_status"], "BROWSER_DOWNLOAD_EVENT_OBSERVED_DENIED")
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["candidate_route_network_sent"])
        self.assertFalse(result["collection_authorized"])

    def test_zero_event_routes_to_dom_intent_diagnostics(self) -> None:
        result = diagnose_artifact_download_event(self.config, runtime=FakeRuntime(base_raw([])))
        self.assertEqual(result["download_event_count"], 0)
        self.assertEqual(result["diagnostic_status"], "NO_BROWSER_DOWNLOAD_EVENT_OBSERVED")
        self.assertEqual(result["next_gate"], "M7_SIOPE_ARTIFACT_DOWNLOAD_DOM_INTENT_DIAGNOSTICS_0_8_0")

    def test_network_send_or_download_fails_closed(self) -> None:
        raw = base_raw([])
        raw["candidate_route_network_sent"] = True
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            diagnose_artifact_download_event(self.config, runtime=FakeRuntime(raw))
        raw = base_raw([])
        raw["artifact_downloaded"] = True
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            diagnose_artifact_download_event(self.config, runtime=FakeRuntime(raw))

    def test_source_enables_download_events_but_denies_download(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('"behavior": "deny"', source)
        self.assertIn('"eventsEnabled": True', source)
        self.assertIn('Browser.downloadWillBegin', source)
        self.assertNotIn('"behavior": "allow"', source)
        self.assertNotIn('Browser.getDownload', source)

    def test_direct_dry_run_bootstraps_without_network(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["candidate_route_network_sent"])
        self.assertFalse(result["collection_authorized"])

    def test_workflow_manual_read_only_and_full_qa(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("confirm_artifact_download_event_diagnostics", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("python main.py selftest", workflow)
        self.assertIn("--dry-run", workflow)
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("wget ", workflow)


if __name__ == "__main__":
    unittest.main()
