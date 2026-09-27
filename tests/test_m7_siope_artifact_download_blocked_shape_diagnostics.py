from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.sources.siope_artifact_download_blocked_shape_diagnostics import diagnose_blocked_shape
from robo_dados_publicos.sources.siope_artifact_download_runtime_route_probe import load_artifact_download_runtime_route_probe_config
from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_artifact_download_runtime_route_probe_gate.json"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-artifact-download-blocked-shape-diagnostics-gate.yml"
SCRIPT = ROOT / "scripts" / "github_siope_artifact_download_blocked_shape_diagnostics_gate.py"


class FakeRuntime:
    def __init__(self, blocked):
        self.blocked = blocked

    def run_probe(self, config):
        return {
            "page_verified": True,
            "artifact_declared": True,
            "export_control_found": True,
            "click_executed": True,
            "post_click_interception_active": True,
            "browser_download_denied": True,
            "candidate_route_network_sent": False,
            "verified_metadata_network_sent": True,
            "verified_metadata_request_count": 1,
            "blocked_requests": self.blocked,
        }


class TestM7SiopeArtifactDownloadBlockedShapeDiagnostics(unittest.TestCase):
    def setUp(self):
        self.config = load_artifact_download_runtime_route_probe_config(CONFIG)

    def test_favicon_is_explicitly_classified(self):
        got = diagnose_blocked_shape(self.config, runtime=FakeRuntime([
            {"url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros/favicon.ico", "method": "GET", "resource_type": "Other"}
        ]))
        shape = got["blocked_request_shapes"][0]
        self.assertEqual(shape["classification_reason"], "FAVICON")
        self.assertFalse(shape["network_sent"])

    def test_disallowed_method_is_visible_without_query_values(self):
        got = diagnose_blocked_shape(self.config, runtime=FakeRuntime([
            {"url": "https://www.fnde.gov.br/api/download?token=SECRET&id=20", "method": "OPTIONS", "resource_type": "XHR"}
        ]))
        shape = got["blocked_request_shapes"][0]
        self.assertEqual(shape["classification_reason"], "METHOD_NOT_CANDIDATE")
        self.assertEqual(shape["query_keys"], ["id", "token"])
        self.assertNotIn("SECRET", json.dumps(got))

    def test_local_scheme_does_not_persist_opaque_value(self):
        got = diagnose_blocked_shape(self.config, runtime=FakeRuntime([
            {"url": "blob:https://www.fnde.gov.br/opaque-secret", "method": "GET", "resource_type": "Other"}
        ]))
        shape = got["blocked_request_shapes"][0]
        self.assertEqual(shape["scheme"], "blob")
        self.assertIsNone(shape["route_without_query"])
        self.assertNotIn("opaque-secret", json.dumps(got))

    def test_candidate_network_send_fails_closed(self):
        class BadRuntime(FakeRuntime):
            def run_probe(self, config):
                out = super().run_probe(config)
                out["candidate_route_network_sent"] = True
                return out
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            diagnose_blocked_shape(self.config, runtime=BadRuntime([{"url": "https://www.fnde.gov.br/x", "method": "GET", "resource_type": "XHR"}]))

    def test_no_blocked_request_fails_closed(self):
        with self.assertRaises(SiopeRuntimeRouteProbeError):
            diagnose_blocked_shape(self.config, runtime=FakeRuntime([]))

    def test_direct_dry_run_bootstraps_without_network(self):
        cp = subprocess.run([sys.executable, str(SCRIPT), "--dry-run"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        got = json.loads(cp.stdout)
        self.assertFalse(got["candidate_route_network_sent"])
        self.assertFalse(got["artifact_downloaded"])

    def test_workflow_manual_read_only_full_qa(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("contents: read", text)
        self.assertIn("confirm_artifact_download_blocked_shape_diagnostics", text)
        live = text.index("Diagnóstico ao vivo da forma bloqueada")
        self.assertLess(text.index("python -m unittest discover -s tests -v"), live)
        self.assertLess(text.index("python main.py selftest"), live)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)


if __name__ == "__main__":
    unittest.main()
