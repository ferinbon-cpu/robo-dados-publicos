from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_artifact_download_runtime_route_probe import (
    _is_allowed_verified_metadata,
    load_artifact_download_runtime_route_probe_config,
    probe_artifact_download_runtime_route,
    summarize_download_candidates,
)
from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "source_expansion.siope_artifact_download_runtime_route_probe_gate.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "siope-artifact-download-runtime-route-probe-gate.yml"


class FakeRuntime:
    def __init__(self, blocked, metadata_count=1, candidate_sent=False):
        self.blocked = blocked
        self.metadata_count = metadata_count
        self.candidate_sent = candidate_sent

    def run_probe(self, config):
        return {
            "page_verified": True,
            "artifact_declared": True,
            "export_control_found": True,
            "click_executed": True,
            "post_click_interception_active": True,
            "browser_download_denied": True,
            "candidate_route_network_sent": self.candidate_sent,
            "verified_metadata_network_sent": self.metadata_count > 0,
            "verified_metadata_request_count": self.metadata_count,
            "cross_origin_initial_aborted_count": 0,
            "post_click_static_assets_continued_count": 3,
            "post_click_nonstatic_aborted_count": len(self.blocked),
            "blocked_requests": self.blocked,
        }


class TestM7SiopeArtifactDownloadRuntimeRouteProbe(unittest.TestCase):
    def setUp(self):
        self.config = load_artifact_download_runtime_route_probe_config(CONFIG_PATH)

    def test_config_keeps_collection_closed_and_metadata_exact(self):
        self.assertEqual(self.config["verified_metadata_method"], "GET")
        self.assertEqual(self.config["max_verified_metadata_requests"], 2)
        self.assertEqual(self.config["artifact_download"], "PROHIBITED")
        self.assertEqual(self.config["source_collection"], "PROHIBITED")
        self.assertEqual(self.config["schedule"], "DISABLED")

    def test_only_exact_verified_metadata_is_allowed(self):
        url = self.config["verified_metadata_url"]
        self.assertTrue(_is_allowed_verified_metadata(url, "GET", "XHR", self.config))
        self.assertFalse(_is_allowed_verified_metadata(url + "?x=1", "GET", "XHR", self.config))
        self.assertFalse(_is_allowed_verified_metadata(url, "POST", "XHR", self.config))
        self.assertFalse(_is_allowed_verified_metadata(url, "GET", "Document", self.config))

    def test_candidate_sanitizer_removes_query_values(self):
        events = [{"url": "https://www.fnde.gov.br/download/file?token=SECRET&id=20", "method": "GET", "resource_type": "XHR"}]
        got = summarize_download_candidates(events, self.config)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["route_without_query"], "https://www.fnde.gov.br/download/file")
        self.assertEqual(got[0]["query_keys"], ["id", "token"])
        self.assertNotIn("SECRET", json.dumps(got))

    def test_unique_candidate_passes_without_candidate_network_send(self):
        runtime = FakeRuntime([{"url": "https://www.fnde.gov.br/download/file?id=20", "method": "GET", "resource_type": "XHR"}], metadata_count=2)
        got = probe_artifact_download_runtime_route(self.config, runtime=runtime)
        self.assertEqual(got["candidate_count"], 1)
        self.assertFalse(got["candidate_route_network_sent"])
        self.assertTrue(got["verified_metadata_network_sent"])
        self.assertFalse(got["artifact_downloaded"])

    def test_zero_candidate_fails_closed(self):
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            probe_artifact_download_runtime_route(self.config, runtime=FakeRuntime([], metadata_count=1))

    def test_multiple_candidates_fail_closed(self):
        events = [
            {"url": "https://www.fnde.gov.br/a", "method": "GET", "resource_type": "XHR"},
            {"url": "https://www.fnde.gov.br/b", "method": "GET", "resource_type": "XHR"},
        ]
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            probe_artifact_download_runtime_route(self.config, runtime=FakeRuntime(events, metadata_count=1))

    def test_missing_verified_metadata_fails_closed(self):
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            probe_artifact_download_runtime_route(self.config, runtime=FakeRuntime([], metadata_count=0))

    def test_candidate_network_send_fails_closed(self):
        events = [{"url": "https://www.fnde.gov.br/a", "method": "GET", "resource_type": "XHR"}]
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            probe_artifact_download_runtime_route(self.config, runtime=FakeRuntime(events, metadata_count=1, candidate_sent=True))

    def test_workflow_is_manual_read_only_and_full_qa_precedes_live(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("contents: read", text)
        self.assertIn("confirm_artifact_download_runtime_route_probe", text)
        live = text.index("Probe ao vivo da rota final")
        self.assertLess(text.index("python -m unittest discover -s tests -v"), live)
        self.assertLess(text.index("python main.py selftest"), live)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("drive", text.lower())
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)


if __name__ == "__main__":
    unittest.main()
