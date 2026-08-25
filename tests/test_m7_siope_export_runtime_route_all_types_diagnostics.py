from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_export_runtime_route_all_types_diagnostics import (
    diagnose_export_runtime_route_all_types,
    summarize_all_http_post_click_requests,
)
from robo_dados_publicos.sources.siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    load_runtime_route_probe_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_runtime_route_probe_gate.json"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-export-runtime-route-all-types-diagnostics-gate.yml"
SCRIPT = ROOT / "scripts" / "github_siope_export_runtime_route_all_types_diagnostics_gate.py"


def _base_raw(events):
    return {
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


class TestM7SiopeRuntimeRouteAllTypesDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_route_probe_config(CONFIG)

    def test_non_candidate_resource_types_are_inventoried(self):
        events = [
            {
                "url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/export/20",
                "method": "GET",
                "resource_type": "Image",
                "initiator_functions": [],
            },
            {
                "url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/file/20?token=SECRET&id=20",
                "method": "POST",
                "resource_type": "Preflight",
                "initiator_functions": [],
            },
        ]
        summary = summarize_all_http_post_click_requests(events, self.config)
        self.assertEqual(summary["eligible_event_count"], 2)
        self.assertEqual(summary["unique_route_shape_count"], 2)
        self.assertEqual(summary["resource_type_shape_counts"], {"Image": 1, "Preflight": 1})
        dumped = json.dumps(summary, sort_keys=True)
        self.assertNotIn("SECRET", dumped)
        self.assertIn('"token"', dumped)

    def test_non_http_and_disallowed_methods_stay_excluded(self):
        events = [
            {"url": "data:text/plain,x", "method": "GET", "resource_type": "Other"},
            {"url": "https://www.fnde.gov.br/api/x", "method": "PUT", "resource_type": "XHR"},
        ]
        summary = summarize_all_http_post_click_requests(events, self.config)
        self.assertEqual(summary["eligible_event_count"], 0)
        self.assertEqual(summary["excluded_non_http_count"], 1)
        self.assertEqual(summary["excluded_method_count"], 1)

    def test_live_style_result_keeps_every_route_unsent(self):
        events = [
            {
                "url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/export/20?key=SECRET",
                "method": "GET",
                "resource_type": "Media",
                "initiator_functions": [],
            }
        ]
        result = diagnose_export_runtime_route_all_types(
            self.config, runtime=FakeRuntime(_base_raw(events))
        )
        self.assertEqual(
            result["diagnostic_status"],
            "ALL_HTTP_GET_POST_ROUTE_SHAPES_OBSERVED_NOT_SENT",
        )
        self.assertFalse(result["candidate_route_network_sent"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["head_request_performed"])
        self.assertNotIn("SECRET", json.dumps(result, sort_keys=True))

    def test_network_sent_flag_fails_closed(self):
        raw = _base_raw([])
        raw["candidate_route_network_sent"] = True
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "NETWORK_SENT"):
            diagnose_export_runtime_route_all_types(self.config, runtime=FakeRuntime(raw))

    def test_workflow_is_manual_full_qa_and_sanitized(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", text)
        self.assertIn("confirm_export_runtime_route_all_types_diagnostics", text)
        self.assertIn("github_preflight.py", text)
        self.assertIn("github_siope_export_runtime_route_probe_design_gate.py", text)
        self.assertIn("--dry-run", text)
        self.assertIn("unittest discover", text)
        self.assertIn("main.py selftest", text)
        self.assertIn("result.json", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("drive", text.lower())

    def test_script_and_workflow_do_not_add_download_head_or_body_capture(self):
        text = SCRIPT.read_text(encoding="utf-8") + "\n" + WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("getResponseBody", text)
        self.assertNotIn("getRequestPostData", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)
        self.assertNotIn("requests.head", text)
        self.assertIn('"artifact_downloaded": False', SCRIPT.read_text(encoding="utf-8"))
        self.assertIn('"head_request_performed": False', SCRIPT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
