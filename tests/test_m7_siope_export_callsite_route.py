import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_download_route_discovery import ReadOnlyDeclaredResourceClient
from robo_dados_publicos.sources.siope_export_callsite_route import (
    SiopeExportCallsiteRouteError,
    analyze_callsites,
    discover_export_callsite_routes,
    load_export_callsite_route_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_callsite_route_gate.json"


class _Headers(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class _Response:
    def __init__(self, url: str, body: str, content_type: str, status: int = 200):
        self.url = url
        self._body = body.encode("utf-8")
        self.headers = _Headers({"Content-Type": content_type})
        self.status = status

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def read(self, _limit):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _FakeOpener:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def __call__(self, request, timeout=0):
        self.calls.append((request.full_url, request.get_method(), timeout))
        return self.mapping[request.full_url]


class TestM7SiopeExportCallsiteRoute(unittest.TestCase):
    def setUp(self):
        self.config = load_export_callsite_route_config(CONFIG)
        self.page_url = self.config["page_url"]
        self.script_url = "https://www.fnde.gov.br/assets/app.js"
        self.page_html = """
        <html><body>
          <h1>Dados Gerais - SIOPE</h1>
          <div>exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz</div>
          <script src="/assets/app.js"></script>
        </body></html>
        """

    def test_config_remains_read_only_and_candidate_route_request_is_prohibited(self):
        self.assertEqual("PASSIVE_EXPORT_CALLSITE_ROUTE_DISCOVERY_ONLY", self.config["mode"])
        self.assertEqual("PROHIBITED", self.config["candidate_route_request"])
        self.assertEqual("PROHIBITED", self.config["artifact_download"])
        self.assertEqual("PROHIBITED", self.config["browser_automation"])
        self.assertEqual("PROHIBITED", self.config["click_execution"])
        self.assertEqual("NONE" if False else "PROHIBITED", self.config["remote_writes"])
        self.assertEqual("DISABLED", self.config["schedule"])

    def test_route_literal_near_target_identifier_is_candidate(self):
        text = "function getArtifactByDataProductId(id){ return fetch(`/api/artifacts/${id}/download?token=x`); }"
        observations = analyze_callsites(
            text,
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            identifiers=tuple(self.config["target_identifiers"]),
            window_chars=2400,
            max_per_identifier=8,
            max_total=24,
        )
        routes = observations[0]["route_candidates"]
        self.assertEqual(1, len(routes))
        self.assertTrue(routes[0]["dynamic"])
        self.assertTrue(routes[0]["query_present"])
        self.assertNotIn("token", routes[0]["route_without_query"])
        self.assertIn("{VAR}", routes[0]["route_without_query"])

    def test_unrelated_route_outside_callsite_window_is_not_candidate(self):
        text = "getArtifactByDataProductId(id);" + ("x" * 6000) + "const u='/api/unrelated/export';"
        observations = analyze_callsites(
            text,
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            identifiers=("getArtifactByDataProductId",),
            window_chars=2400,
            max_per_identifier=8,
            max_total=24,
        )
        self.assertEqual([], observations[0]["route_candidates"])

    def test_cross_origin_route_near_callsite_is_rejected(self):
        text = "function downloadFile(){ return fetch('https://evil.example/download'); }"
        observations = analyze_callsites(
            text,
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            identifiers=("downloadFile",),
            window_chars=2400,
            max_per_identifier=8,
            max_total=24,
        )
        self.assertEqual([], observations[0]["route_candidates"])

    def test_discovery_fetches_only_page_and_declared_script_never_candidate_route(self):
        external = "function getArtifactByDataProductId(id){return fetch(`/api/artifacts/${id}/download`)}"
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            self.script_url: _Response(self.script_url, external, "application/javascript"),
        })
        result = discover_export_callsite_routes(
            self.config,
            client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
        )
        self.assertEqual("PASS_M7_SIOPE_EXPORT_CALLSITE_ROUTE_DISCOVERY_GATE", result["status"])
        self.assertEqual("CALLSITE_ROUTE_CANDIDATE_OBSERVED_NOT_CALLED", result["callsite_route_status"])
        self.assertGreater(result["route_candidate_count"], 0)
        self.assertEqual([self.page_url, self.script_url], [call[0] for call in opener.calls])
        self.assertFalse(result["candidate_route_requested"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["browser_automation_performed"])
        self.assertFalse(result["collection_authorized"])
        self.assertEqual("NONE", result["remote_writes"])

    def test_target_identifier_without_route_is_success_but_route_remains_unproven(self):
        external = "function getArtifactMetadataByDataProductId(id){return cache[id]}"
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            self.script_url: _Response(self.script_url, external, "application/javascript"),
        })
        result = discover_export_callsite_routes(
            self.config,
            client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
        )
        self.assertEqual("EXPORT_CALLSITE_OBSERVED_ROUTE_UNPROVEN", result["callsite_route_status"])
        self.assertEqual(0, result["route_candidate_count"])
        self.assertEqual("M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_0_8_0", result["next_gate"])
        self.assertFalse(result["candidate_route_requested"])

    def test_no_target_identifier_fails_closed(self):
        external = "const ordinary = '/api/status';"
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            self.script_url: _Response(self.script_url, external, "application/javascript"),
        })
        with self.assertRaisesRegex(SiopeExportCallsiteRouteError, "TARGET_IDENTIFIERS_NOT_OBSERVED"):
            discover_export_callsite_routes(
                self.config,
                client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
            )

    def test_dry_run_authorizes_nothing(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "github_siope_export_callsite_route_gate.py"), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("PASS_M7_SIOPE_EXPORT_CALLSITE_ROUTE_DISCOVERY_DRY_RUN", payload["status"])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["candidate_route_requested"])
        self.assertFalse(payload["artifact_downloaded"])
        self.assertFalse(payload["browser_automation_performed"])
        self.assertFalse(payload["collection_authorized"])
        self.assertEqual("NONE", payload["remote_writes"])


if __name__ == "__main__":
    unittest.main()
