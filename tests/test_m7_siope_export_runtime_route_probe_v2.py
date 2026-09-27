from __future__ import annotations

from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError
from robo_dados_publicos.sources.siope_export_runtime_route_probe_v2 import (
    _is_allowed_static_asset,
    load_runtime_route_probe_v2_config,
    probe_export_runtime_route_v2,
    summarize_blocked_candidates,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_runtime_route_probe_v2_gate.json"


class FakeRuntime:
    def __init__(self, raw):
        self.raw = raw
    def run_probe(self, config):
        return self.raw


def _raw(events):
    return {
        "browser_binary_name": "google-chrome",
        "browser_version": "TEST",
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "click_executed": True,
        "post_click_interception_active": True,
        "browser_download_denied": True,
        "candidate_route_network_sent": False,
        "cross_origin_initial_aborted_count": 3,
        "post_click_static_assets_continued_count": 7,
        "post_click_nonstatic_aborted_count": len(events),
        "blocked_requests": events,
    }


class TestRuntimeRouteProbeV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_route_probe_v2_config(CONFIG)

    def test_only_exact_static_script_and_stylesheet_are_allowlisted(self):
        base = "https://www.fnde.gov.br/plataforma-antonieta-de-barros/assets/"
        self.assertTrue(_is_allowed_static_asset(base + "chunk.js", "GET", "Script", self.config))
        self.assertTrue(_is_allowed_static_asset(base + "chunk.css", "GET", "Stylesheet", self.config))
        self.assertFalse(_is_allowed_static_asset(base + "data", "GET", "Fetch", self.config))
        self.assertFalse(_is_allowed_static_asset("https://evil.example/assets/x.js", "GET", "Script", self.config))
        self.assertFalse(_is_allowed_static_asset(base + "chunk.js", "POST", "Script", self.config))

    def test_unique_nonstatic_request_passes_without_send(self):
        events = [{
            "url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/artifacts/20/export?key=SECRET",
            "method": "GET",
            "resource_type": "Fetch",
        }]
        result = probe_export_runtime_route_v2(self.config, runtime=FakeRuntime(_raw(events)))
        self.assertEqual(result["runtime_probe_status"], "UNIQUE_NONSTATIC_REQUEST_OBSERVED_NOT_SENT")
        self.assertFalse(result["candidate_route_network_sent"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertEqual(result["candidate"]["query_keys"], ["key"])
        self.assertNotIn("SECRET", str(result))

    def test_favicon_is_ignored(self):
        events = [{"url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros/favicon.ico", "method": "GET", "resource_type": "Other"}]
        self.assertEqual(summarize_blocked_candidates(events, self.config), [])

    def test_multiple_nonstatic_requests_fail_closed(self):
        events = [
            {"url": "https://www.fnde.gov.br/api/a", "method": "GET", "resource_type": "Fetch"},
            {"url": "https://www.fnde.gov.br/api/b", "method": "GET", "resource_type": "XHR"},
        ]
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "MULTIPLE_CANDIDATES"):
            probe_export_runtime_route_v2(self.config, runtime=FakeRuntime(_raw(events)))

    def test_zero_candidates_fail_closed(self):
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "ZERO_CANDIDATES"):
            probe_export_runtime_route_v2(self.config, runtime=FakeRuntime(_raw([])))

    def test_network_sent_flag_fails_closed(self):
        raw = _raw([{"url": "https://www.fnde.gov.br/api/a", "method": "GET", "resource_type": "Fetch"}])
        raw["candidate_route_network_sent"] = True
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "NETWORK_SENT"):
            probe_export_runtime_route_v2(self.config, runtime=FakeRuntime(raw))


if __name__ == "__main__":
    unittest.main()
