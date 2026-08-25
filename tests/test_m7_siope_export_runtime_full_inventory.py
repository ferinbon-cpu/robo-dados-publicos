from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_export_runtime_full_inventory import (
    diagnose_full_runtime_inventory,
    summarize_all_post_click_http_requests,
)
from robo_dados_publicos.sources.siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    load_runtime_route_probe_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_runtime_route_probe_gate.json"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-export-runtime-full-inventory-gate.yml"


def _base_raw(events):
    return {
        "browser_binary_name": "google-chrome",
        "browser_version": "Google Chrome TEST",
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "click_executed": True,
        "post_click_interception_active": True,
        "browser_download_denied": True,
        "candidate_route_network_sent": False,
        "cross_origin_initial_aborted_count": 12,
        "post_click_aborted_request_count": len(events),
        "intercepted_requests": events,
    }


class FakeRuntime:
    def __init__(self, raw):
        self.raw = raw

    def run_probe(self, config):
        return self.raw


class TestM7SiopeExportRuntimeFullInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_route_probe_config(CONFIG)

    def test_all_http_resource_types_are_inventoried(self):
        events = [
            {"url": "https://www.fnde.gov.br/a.js", "method": "GET", "resource_type": "Script"},
            {"url": "https://www.fnde.gov.br/a.png", "method": "GET", "resource_type": "Image"},
            {"url": "https://www.fnde.gov.br/a.woff2", "method": "GET", "resource_type": "Font"},
            {"url": "https://www.fnde.gov.br/api/data", "method": "GET", "resource_type": "Fetch"},
        ]
        summary = summarize_all_post_click_http_requests(events, self.config)
        self.assertEqual(summary["http_event_count"], 4)
        self.assertEqual(summary["resource_type_event_counts"], {"Fetch": 1, "Font": 1, "Image": 1, "Script": 1})
        self.assertEqual(summary["non_static_shape_count"], 1)

    def test_query_values_are_never_persisted(self):
        events = [{
            "url": "https://www.fnde.gov.br/api/export?id=20&token=TOPSECRET#frag",
            "method": "GET",
            "resource_type": "Other",
        }]
        summary = summarize_all_post_click_http_requests(events, self.config)
        payload = json.dumps(summary)
        self.assertNotIn("TOPSECRET", payload)
        self.assertEqual(summary["request_inventory"][0]["query_keys"], ["id", "token"])

    def test_marker_bound_shape_is_explicit(self):
        events = [{
            "url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/artifact/20/export",
            "method": "GET",
            "resource_type": "Other",
        }]
        summary = summarize_all_post_click_http_requests(events, self.config)
        self.assertEqual(summary["marker_shape_count"], 1)
        self.assertTrue(summary["request_inventory"][0]["marker_hits"])
        result = diagnose_full_runtime_inventory(self.config, runtime=FakeRuntime(_base_raw(events)))
        self.assertEqual(result["diagnostic_status"], "ONE_MARKER_BOUND_ROUTE_SHAPE_OBSERVED_NOT_SENT")
        self.assertEqual(result["next_gate"], "M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0")
        self.assertFalse(result["candidate_route_network_sent"])

    def test_only_static_shapes_route_to_control_diagnostics(self):
        events = [
            {"url": "https://www.fnde.gov.br/a.js", "method": "GET", "resource_type": "Script"},
            {"url": "https://www.fnde.gov.br/favicon.ico", "method": "GET", "resource_type": "Other"},
        ]
        result = diagnose_full_runtime_inventory(self.config, runtime=FakeRuntime(_base_raw(events)))
        self.assertEqual(result["diagnostic_status"], "ONLY_STATIC_POST_CLICK_HTTP_SHAPES_OBSERVED")
        self.assertEqual(result["next_gate"], "M7_SIOPE_RUNTIME_CONTROL_TARGET_DIAGNOSTICS_0_8_0")

    def test_network_sent_fails_closed(self):
        raw = _base_raw([{"url": "https://www.fnde.gov.br/a.js", "method": "GET", "resource_type": "Script"}])
        raw["candidate_route_network_sent"] = True
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "NETWORK_SENT"):
            diagnose_full_runtime_inventory(self.config, runtime=FakeRuntime(raw))

    def test_inventory_truncation_fails_closed(self):
        events = [
            {"url": f"https://www.fnde.gov.br/assets/{i}.js", "method": "GET", "resource_type": "Script"}
            for i in range(129)
        ]
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "TRUNCATION_REQUIRED"):
            summarize_all_post_click_http_requests(events, self.config)

    def test_workflow_is_manual_read_only_and_requires_confirmation(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_export_runtime_full_inventory", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("persist-credentials: false", text)

    def test_workflow_preserves_fail_closed_runtime_and_sanitized_artifact(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github_siope_export_runtime_route_probe_design_gate.py", text)
        self.assertIn("github_siope_export_runtime_full_inventory_gate.py --dry-run", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("siope-export-runtime-full-inventory-evidence/result.json", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)
        self.assertNotIn("gcloud ", text)
        self.assertNotIn("drive", text.lower())
        self.assertNotIn("--head", text.lower())


if __name__ == "__main__":
    unittest.main()
