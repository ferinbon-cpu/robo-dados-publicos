from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError
from robo_dados_publicos.sources.siope_public_get_runtime_cdp_direct import (
    _AttachedCdpSession,
    _browser_ws_url_from_active_port,
    _create_attached_page_session,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_public_get_runtime_cdp_direct.py"
SCRIPT = ROOT / "scripts" / "github_siope_public_get_runtime_route_diagnostics_gate.py"
CONFIG = ROOT / "config" / "source_expansion.siope_public_get_runtime_route_diagnostics_gate.json"


class FakeBrowserSession:
    def __init__(self):
        self.event_handler = None
        self.calls = []
        self.next_id = 0
        self.command_timeout_s = 1.0

    def command(self, method, params=None, **kwargs):
        self.calls.append((method, params or {}))
        if method == "Target.createTarget":
            return {"targetId": "TARGET-1"}
        if method == "Target.attachToTarget":
            return {"sessionId": "SESSION-1"}
        return {}


class TestSiopePublicGetRuntimeCdpDirect(unittest.TestCase):
    def test_active_port_browser_websocket_is_local_and_exact(self):
        url = _browser_ws_url_from_active_port(43210, "/devtools/browser/abc-123")
        self.assertEqual(url, "ws://127.0.0.1:43210/devtools/browser/abc-123")
        for bad in ["/json/version", "/devtools/page/x", "/devtools/browser/x?secret=1", "/devtools/browser/x#frag"]:
            with self.assertRaises(SiopeRuntimeRouteProbeError):
                _browser_ws_url_from_active_port(43210, bad)

    def test_target_is_created_and_attached_via_browser_cdp(self):
        browser = FakeBrowserSession()
        attached = _create_attached_page_session(browser)
        self.assertIsInstance(attached, _AttachedCdpSession)
        self.assertEqual(attached.session_id, "SESSION-1")
        self.assertEqual(
            browser.calls,
            [
                ("Target.createTarget", {"url": "about:blank"}),
                ("Target.attachToTarget", {"targetId": "TARGET-1", "flatten": True}),
            ],
        )

    def test_runtime_source_does_not_use_local_json_version_or_new_endpoints(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("_wait_browser_debug_version", source)
        self.assertNotIn("_create_page_target", source)
        self.assertNotIn("/json/version", source)
        self.assertNotIn("/json/new", source)
        self.assertIn("Target.createTarget", source)
        self.assertIn("Target.attachToTarget", source)
        self.assertIn("Browser.setDownloadBehavior", source)
        self.assertIn('"behavior": "deny"', source)

    def test_gate_script_uses_direct_runtime(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("SystemChromeCdpPublicGetRuntimeDirect", script)
        self.assertNotIn("SystemChromeCdpPublicGetRuntimeWithFailureTelemetry", script)

    def test_safety_contract_remains_closed(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        serialized = json.dumps(config, sort_keys=True)
        self.assertNotIn("352690", config["public_indexed_example_url"])
        self.assertEqual(config["pilot_limeira_values_send"], "PROHIBITED")
        self.assertEqual(config["dynamic_candidate_network_send"], "PROHIBITED")
        self.assertEqual(config["form_submission"], "PROHIBITED")
        self.assertEqual(config["captcha_bypass"], "PROHIBITED")
        self.assertEqual(config["authentication"], "PROHIBITED")
        self.assertEqual(config["request_body_capture"], "PROHIBITED")
        self.assertEqual(config["response_body_capture"], "PROHIBITED")
        self.assertEqual(config["artifact_download"], "PROHIBITED")
        self.assertNotIn('"schedule": "ENABLED"', serialized)


if __name__ == "__main__":
    unittest.main()
