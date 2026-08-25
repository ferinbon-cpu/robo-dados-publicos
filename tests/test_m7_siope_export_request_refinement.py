import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_download_route_discovery import ReadOnlyDeclaredResourceClient
from robo_dados_publicos.sources.siope_export_request_refinement import (
    SiopeExportRequestRefinementError,
    analyze_request_context,
    load_export_request_refinement_config,
    refine_export_request_expressions,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_request_refinement_gate.json"


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


class TestM7SiopeExportRequestRefinement(unittest.TestCase):
    def setUp(self):
        self.config = load_export_request_refinement_config(CONFIG)
        self.page_url = self.config["page_url"]
        self.script_url = "https://www.fnde.gov.br/assets/app.js"
        self.page_html = """
        <html><body>
          <h1>Dados Gerais - SIOPE</h1>
          <div>exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz</div>
          <script src="/assets/app.js"></script>
        </body></html>
        """

    def _client(self, script: str):
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            self.script_url: _Response(self.script_url, script, "application/javascript"),
        })
        return ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener), opener

    def test_config_is_read_only_and_candidate_request_is_prohibited(self):
        self.assertEqual("PASSIVE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_ONLY", self.config["mode"])
        self.assertEqual("PROHIBITED", self.config["candidate_route_request"])
        self.assertEqual("PROHIBITED", self.config["artifact_download"])
        self.assertEqual("PROHIBITED", self.config["browser_automation"])
        self.assertEqual("PROHIBITED", self.config["remote_writes"])
        self.assertEqual("DISABLED", self.config["schedule"])

    def test_base_url_plus_direct_http_expression_is_composed(self):
        context = """
        const api = { baseURL: '/plataforma-antonieta-de-barros-api' };
        function getArtifactByDataProductId(id) {
          return api.get(`/artifacts/${id}`);
        }
        """
        result = analyze_request_context(
            context,
            evidence_identifier="getArtifactByDataProductId",
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
        )
        self.assertEqual(1, result["composed_candidate_count"])
        self.assertEqual(
            "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/artifacts/{VAR}",
            result["composed_candidates"][0]["route_without_query"],
        )

    def test_unbound_neighbor_literals_are_not_candidates(self):
        context = """
        function getArtifactMetadataByDataProductId(id) {
          const labels = ['/products', '/directory', '/legal', '/payment'];
          return id;
        }
        """
        result = analyze_request_context(
            context,
            evidence_identifier="getArtifactMetadataByDataProductId",
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
        )
        self.assertEqual(0, result["request_candidate_count"])
        self.assertEqual(0, result["composed_candidate_count"])

    def test_cross_origin_request_literal_is_rejected(self):
        context = "function downloadFile(id){ return fetch(`https://evil.example/${id}`); }"
        result = analyze_request_context(
            context,
            evidence_identifier="downloadFile",
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
        )
        self.assertEqual(0, result["request_candidate_count"])

    def test_variable_request_argument_is_resolved_from_local_literal(self):
        context = """
        function downloadFile(id) {
          const route = `/download/${id}`;
          return fetch(route);
        }
        """
        result = analyze_request_context(
            context,
            evidence_identifier="downloadFile",
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
        )
        bindings = {item["binding"] for item in result["request_candidates"]}
        self.assertIn("RESOLVED_VARIABLE_REQUEST_ARGUMENT", bindings)

    def test_live_style_discovery_gets_only_page_and_declared_script(self):
        script = """
        const api = { baseURL: '/plataforma-antonieta-de-barros-api' };
        function getArtifactByDataProductId(id) { return api.get(`/artifacts/${id}`); }
        """
        client, opener = self._client(script)
        result = refine_export_request_expressions(self.config, client=client)
        self.assertEqual("PASS_M7_SIOPE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_GATE", result["status"])
        self.assertEqual("UNIQUE_REQUEST_ROUTE_EXPRESSION_OBSERVED_NOT_CALLED", result["refinement_status"])
        self.assertEqual([self.page_url, self.script_url], [item[0] for item in opener.calls])
        self.assertFalse(result["candidate_route_requested"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["collection_authorized"])

    def test_multiple_direct_request_routes_remain_ambiguous(self):
        script = """
        function getArtifactByDataProductId(id) {
          if (id) return fetch(`/one/${id}`);
          return fetch(`/two/${id}`);
        }
        """
        client, _ = self._client(script)
        result = refine_export_request_expressions(self.config, client=client)
        self.assertEqual("REQUEST_ROUTE_EXPRESSIONS_OBSERVED_AMBIGUOUS_NOT_CALLED", result["refinement_status"])
        self.assertEqual(2, result["direct_request_route_count"])

    def test_no_target_identifier_fails_closed(self):
        client, _ = self._client("const x = fetch('/ordinary');")
        with self.assertRaisesRegex(SiopeExportRequestRefinementError, "TARGET_IDENTIFIERS_NOT_OBSERVED"):
            refine_export_request_expressions(self.config, client=client)

    def test_query_values_are_removed_from_evidence(self):
        context = "function exportKey(){ return fetch('/artifact?id=20&token=secret'); }"
        result = analyze_request_context(
            context,
            evidence_identifier="exportKey",
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=1,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
        )
        self.assertEqual("https://www.fnde.gov.br/artifact", result["request_candidates"][0]["route_without_query"])
        self.assertTrue(result["request_candidates"][0]["query_present"])
        self.assertNotIn("token", json.dumps(result))
        self.assertNotIn("secret", json.dumps(result))

    def test_dry_run_authorizes_nothing(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "github_siope_export_request_refinement_gate.py"), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("PASS_M7_SIOPE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_DRY_RUN", payload["status"])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["candidate_route_requested"])
        self.assertFalse(payload["artifact_downloaded"])
        self.assertFalse(payload["collection_authorized"])


if __name__ == "__main__":
    unittest.main()
