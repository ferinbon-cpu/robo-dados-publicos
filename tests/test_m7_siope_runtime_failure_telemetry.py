from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_get_runtime_failure_telemetry import (
    _failure_diagnostics,
    _sanitize_dom_route,
)
from robo_dados_publicos.sources.siope_public_get_runtime_route_diagnostics import (
    load_public_get_runtime_route_diagnostics_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_get_runtime_route_diagnostics_gate.json"
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_public_get_runtime_failure_telemetry.py"
SCRIPT = ROOT / "scripts" / "github_siope_public_get_runtime_route_diagnostics_gate.py"


class TestM7SiopeRuntimeFailureTelemetry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_public_get_runtime_route_diagnostics_config(CONFIG)

    def test_failure_diagnostics_remove_query_values_and_keep_keys(self):
        blocked = [{
            "url": "https://www.fnde.gov.br/siope/buscarDados.do?token=TOPSECRET&acao=dados",
            "method": "GET",
            "resource_type": "XHR",
        }]
        page_state = {
            "ready": "complete",
            "loadingA": False,
            "loadingB": True,
            "challenge": False,
            "route": {
                "scheme": "https",
                "host": "www.fnde.gov.br",
                "path": "/siope/dadosInformadosMunicipio.do?should_not_survive=SECRET",
                "query_present": True,
                "query_keys": ["acao", "token"],
            },
        }
        diagnostics = _failure_diagnostics(
            page_state=page_state,
            navigate_result={},
            blocked=blocked,
            initial_document_continued=1,
            static_assets_continued=3,
            local_requests_continued=1,
            config=self.config,
        )
        serialized = json.dumps(diagnostics, sort_keys=True)
        self.assertNotIn("TOPSECRET", serialized)
        self.assertNotIn("should_not_survive", serialized)
        self.assertNotIn("SECRET", serialized)
        self.assertIn("token", serialized)
        self.assertTrue(diagnostics["initial_document_network_sent"])
        self.assertTrue(diagnostics["initial_document_contract_exactly_once"])
        self.assertEqual(diagnostics["candidate_shape_count"], 1)

    def test_dom_route_is_allowlisted_metadata_only(self):
        sanitized = _sanitize_dom_route({
            "scheme": "HTTPS",
            "host": "www.fnde.gov.br",
            "path": "/siope/x.do?secret=value#frag",
            "query_present": True,
            "query_keys": ["acao", "token", "bad key", "x" * 100],
        }, self.config)
        self.assertEqual(sanitized["scheme"], "https")
        self.assertEqual(sanitized["path"], "/siope/x.do")
        self.assertEqual(sanitized["query_keys"], ["acao", "token"])
        self.assertTrue(sanitized["official_host"])
        self.assertNotIn("value", json.dumps(sanitized))

    def test_network_policy_remains_fail_closed(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('_matches_exact_indexed_document(url, method, resource_type, config)', source)
        self.assertIn('_is_allowed_static_asset(url, method, resource_type, config)', source)
        self.assertIn('Fetch.failRequest', source)
        self.assertIn('"errorReason": "Aborted"', source)
        self.assertNotIn('Fetch.continueResponse', source)
        self.assertNotIn('Network.getResponseBody', source)
        self.assertNotIn('Fetch.getResponseBody', source)
        self.assertNotIn('request.get("postData"', source)

    def test_live_script_uses_failure_telemetry_runtime(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("SystemChromeCdpPublicGetRuntimeWithFailureTelemetry", script)
        self.assertIn("runtime=SystemChromeCdpPublicGetRuntimeWithFailureTelemetry()", script)
        self.assertIn('result["initial_document_network_sent"] = diagnostics["initial_document_network_sent"]', script)


if __name__ == "__main__":
    unittest.main()
