import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_download_route_discovery import (
    ReadOnlyDeclaredResourceClient,
    SiopeDownloadRouteDiscoveryError,
    discover_download_route,
    extract_declared_script_urls,
    extract_explicit_download_route_candidates,
    load_download_route_discovery_config,
    summarize_public_page_markers,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_download_route_discovery_gate.json"


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
        value = self.mapping[request.full_url]
        if isinstance(value, Exception):
            raise value
        return value


class TestM7SiopeDownloadRouteDiscovery(unittest.TestCase):
    def setUp(self):
        self.config = load_download_route_discovery_config(CONFIG)
        self.page_url = self.config["page_url"]
        self.page_html = """
        <html><body>
          <h1>Dados Gerais - SIOPE</h1>
          <div>exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz</div>
          <button data-label="Exportar artefato">Exportar artefato</button>
          <script src="/assets/app.js"></script>
          <script src="https://evil.example/app.js"></script>
        </body></html>
        """

    def test_config_is_read_only_and_does_not_authorize_artifact_request(self):
        self.assertEqual("PASSIVE_DOWNLOAD_ROUTE_DISCOVERY_ONLY", self.config["mode"])
        self.assertEqual("PROHIBITED", self.config["artifact_download"])
        self.assertEqual("PROHIBITED", self.config["head_request"])
        self.assertEqual("PROHIBITED", self.config["remote_writes"])
        self.assertEqual("PROHIBITED", self.config["source_collection"])
        self.assertEqual("DISABLED", self.config["schedule"])

    def test_only_explicit_same_origin_scripts_are_selected(self):
        scripts = extract_declared_script_urls(
            self.page_html,
            page_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            max_scripts=8,
        )
        self.assertEqual(("https://www.fnde.gov.br/assets/app.js",), scripts)

    def test_page_markers_are_counts_and_booleans_only(self):
        html = """
        <button onclick="exportArtifact(20)" data-action="export">Exportar artefato</button>
        <a href="/dados/listar">Lista</a>
        <script>const label = 'export';</script>
        """
        markers = summarize_public_page_markers(html)
        self.assertTrue(markers["export_label_present"])
        self.assertEqual(1, markers["inline_script_count"])
        self.assertEqual(1, markers["inline_script_export_marker_count"])
        self.assertEqual(1, markers["inline_event_export_marker_count"])
        self.assertEqual(1, markers["data_attribute_export_marker_count"])
        self.assertEqual(0, markers["href_action_export_marker_count"])
        self.assertNotIn("exportArtifact", json.dumps(markers))

    def test_storage_path_alone_is_not_promoted_to_download_url(self):
        candidates = extract_explicit_download_route_candidates(
            '"exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz"',
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            artifact_basename="SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            keywords=("download", "export", "artefato", "artifact"),
        )
        self.assertEqual((), candidates)

    def test_explicit_relative_download_route_is_resolved_and_query_values_are_not_exposed(self):
        candidates = extract_explicit_download_route_candidates(
            'const x="/plataforma/api/artefato/download?token=SECRET&produto=20";',
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            artifact_basename="SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            keywords=("download", "export", "artefato", "artifact"),
        )
        self.assertEqual(1, len(candidates))
        self.assertEqual("https://www.fnde.gov.br/plataforma/api/artefato/download", candidates[0]["url_without_query"])
        self.assertTrue(candidates[0]["query_present"])
        self.assertNotIn("SECRET", json.dumps(candidates[0]))

    def test_discovery_reads_page_and_declared_script_but_never_candidate_route(self):
        script_url = "https://www.fnde.gov.br/assets/app.js"
        candidate_url = "https://www.fnde.gov.br/plataforma/api/artefato/download"
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            script_url: _Response(script_url, f'const route="{candidate_url}";', "application/javascript"),
        })
        result = discover_download_route(
            self.config,
            client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
        )
        self.assertEqual("PASS_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_GATE", result["status"])
        self.assertEqual(2, len(opener.calls))
        self.assertEqual([self.page_url, script_url], [url for url, _, _ in opener.calls])
        self.assertNotIn(candidate_url, [url for url, _, _ in opener.calls])
        self.assertEqual(1, result["declared_script_count"])
        self.assertEqual(1, result["fetched_script_count"])
        self.assertEqual(0, result["script_failure_count"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["head_request_performed"])
        self.assertFalse(result["collection_authorized"])
        self.assertEqual("NONE", result["remote_writes"])

    def test_no_explicit_route_fails_closed_with_sanitized_diagnostics(self):
        script_url = "https://www.fnde.gov.br/assets/app.js"
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            script_url: _Response(script_url, "const label='Exportar artefato';", "application/javascript"),
        })
        with self.assertRaises(SiopeDownloadRouteDiscoveryError) as caught:
            discover_download_route(
                self.config,
                client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
            )
        exc = caught.exception
        self.assertIn("NOT_EXPLICITLY_DISCOVERED", str(exc))
        self.assertEqual(1, exc.diagnostics["declared_script_count"])
        self.assertEqual(1, exc.diagnostics["fetched_script_count"])
        self.assertEqual(0, exc.diagnostics["script_failure_count"])
        self.assertEqual(0, exc.diagnostics["route_candidate_count"])
        self.assertTrue(exc.diagnostics["page_markers"]["export_label_present"])
        serialized = json.dumps(exc.diagnostics)
        self.assertNotIn("const label", serialized)
        self.assertNotIn(script_url, serialized)

    def test_script_fetch_failure_is_diagnostic_not_raw_content(self):
        script_url = "https://www.fnde.gov.br/assets/app.js"
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            script_url: _Response(script_url, "x" * (1048576 + 2), "application/javascript"),
        })
        with self.assertRaises(SiopeDownloadRouteDiscoveryError) as caught:
            discover_download_route(
                self.config,
                client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
            )
        diagnostics = caught.exception.diagnostics
        self.assertEqual(1, diagnostics["declared_script_count"])
        self.assertEqual(0, diagnostics["fetched_script_count"])
        self.assertEqual(1, diagnostics["script_failure_count"])
        self.assertEqual("STOP_SIOPE_DOWNLOAD_ROUTE_RESPONSE_TOO_LARGE", diagnostics["script_failures"][0]["reason"])
        self.assertNotIn(script_url, json.dumps(diagnostics))
        self.assertNotIn("xxx", json.dumps(diagnostics))

    def test_redirect_to_non_allowlisted_host_fails_closed(self):
        opener = _FakeOpener({
            self.page_url: _Response("https://evil.example/redirect", self.page_html, "text/html"),
        })
        client = ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener)
        with self.assertRaisesRegex(SiopeDownloadRouteDiscoveryError, "REDIRECT_HOST_NOT_ALLOWED"):
            client.get_text(self.page_url, max_bytes=10000, allowed_content_types=("text/html",))

    def test_dry_run_authorizes_nothing(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "github_siope_download_route_discovery_gate.py"), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("PASS_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_DRY_RUN", payload["status"])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["artifact_downloaded"])
        self.assertFalse(payload["head_request_performed"])
        self.assertFalse(payload["collection_authorized"])
        self.assertEqual("NONE", payload["remote_writes"])


if __name__ == "__main__":
    unittest.main()
