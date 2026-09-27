import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_route_discovery import (
    PublicSurfaceClient,
    SiopeRouteDiscoveryError,
    discover_siope_routes,
    inspect_antonieta_surface,
    inspect_classic_surface,
    load_route_discovery_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_route_discovery_gate.json"


class _Headers(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class _Response:
    def __init__(self, body: str, content_type: str = "text/html", status: int = 200):
        self._body = body.encode("utf-8")
        self.headers = _Headers({"Content-Type": content_type})
        self.status = status

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


class TestM7SiopeRouteDiscovery(unittest.TestCase):
    def setUp(self):
        self.config = load_route_discovery_config(CONFIG)
        self.classic_html = """
            <html><body><form>
            <select name="anos"></select><select name="periodos"></select>
            <select name="cod_uf"></select><select name="municipios"></select>
            <select name="admin"></select><select name="planilhas"></select>
            <input name="acao"><input name="pag"><input name="descricaoItem">
            <input name="descricaodoItem"><input name="nivel">
            <div class="g-recaptcha"></div>
            </form></body></html>
        """
        self.antonieta_html = """
            <html><body><h1>Dados Gerais - SIOPE</h1>
            <div>exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz</div>
            <button>Exportar artefato</button></body></html>
        """

    def test_config_is_manual_read_only_contract(self):
        self.assertEqual("PASSIVE_ROUTE_DISCOVERY_ONLY", self.config["mode"])
        self.assertEqual("READ_ONLY_GET", self.config["network"])
        self.assertEqual("PROHIBITED", self.config["remote_writes"])
        self.assertEqual("PROHIBITED", self.config["form_submission"])
        self.assertEqual("PROHIBITED", self.config["captcha_bypass"])
        self.assertEqual("PROHIBITED", self.config["artifact_download"])
        self.assertEqual("DISABLED", self.config["schedule"])

    def test_classic_surface_detects_captcha_and_parameters_without_submission(self):
        result = inspect_classic_surface(
            self.classic_html,
            tuple(self.config["classic_query_parameters_observed"]),
        )
        self.assertTrue(result["captcha_detected"])
        self.assertFalse(result["form_submitted"])
        self.assertEqual(11, len(result["expected_parameters_observed"]))
        self.assertEqual("BLOCK_AUTOMATED_ACQUISITION_HUMAN_CHALLENGE", result["acquisition_decision"])

    def test_antonieta_declared_artifact_is_candidate_not_proof(self):
        expected = self.config["expected_antonieta"]
        result = inspect_antonieta_surface(
            self.antonieta_html,
            expected_name=expected["product_name"],
            expected_path=expected["artifact_path"],
        )
        self.assertTrue(result["product_name_verified"])
        self.assertEqual(expected["artifact_path"], result["artifact_path_declared"])
        self.assertEqual(0, result["explicit_download_url_count"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertEqual("CANDIDATE_REQUIRES_ARTIFACT_VERIFICATION_GATE", result["acquisition_decision"])

    def test_antonieta_accepts_only_explicit_absolute_download_url_as_observation(self):
        expected = self.config["expected_antonieta"]
        html = self.antonieta_html.replace(
            "<button>Exportar artefato</button>",
            '<a href="https://www.fnde.gov.br/download/SIOPE_DADOS_GERAIS_SIOPE.txt.gz">Exportar artefato</a>',
        )
        result = inspect_antonieta_surface(
            html,
            expected_name=expected["product_name"],
            expected_path=expected["artifact_path"],
        )
        self.assertEqual(1, result["explicit_download_url_count"])
        self.assertTrue(result["explicit_download_url_observed"].startswith("https://"))
        self.assertFalse(result["artifact_downloaded"])

    def test_missing_declared_artifact_fails_closed(self):
        expected = self.config["expected_antonieta"]
        with self.assertRaisesRegex(SiopeRouteDiscoveryError, "ARTIFACT_NOT_DECLARED"):
            inspect_antonieta_surface(
                "<h1>Dados Gerais - SIOPE</h1>",
                expected_name=expected["product_name"],
                expected_path=expected["artifact_path"],
            )

    def test_client_allows_only_declared_https_hosts(self):
        client = PublicSurfaceClient(
            allowed_hosts=tuple(self.config["allowed_hosts"]),
            max_response_bytes=self.config["max_response_bytes"],
            opener=_FakeOpener({}),
        )
        with self.assertRaisesRegex(SiopeRouteDiscoveryError, "HOST_NOT_ALLOWED"):
            client.get("https://example.com/siope")
        with self.assertRaisesRegex(SiopeRouteDiscoveryError, "HOST_NOT_ALLOWED"):
            client.get("http://www.fnde.gov.br/siope")

    def test_discovery_gets_exactly_two_pages_and_never_downloads_artifact(self):
        surfaces = self.config["surfaces"]
        opener = _FakeOpener({
            surfaces["classic_query"]: _Response(self.classic_html),
            surfaces["antonieta_product"]: _Response(self.antonieta_html),
        })
        client = PublicSurfaceClient(
            allowed_hosts=tuple(self.config["allowed_hosts"]),
            max_response_bytes=self.config["max_response_bytes"],
            opener=opener,
        )
        result = discover_siope_routes(self.config, client=client)
        self.assertEqual("PASS_M7_SIOPE_ROUTE_DISCOVERY_GATE", result["status"])
        self.assertEqual(2, len(opener.calls))
        self.assertTrue(all(method == "GET" for _, method, _ in opener.calls))
        self.assertFalse(result["form_submission"])
        self.assertFalse(result["captcha_bypass"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["collection_authorized"])
        self.assertEqual("NONE", result["remote_writes"])

    def test_route_remains_unproven_after_discovery(self):
        surfaces = self.config["surfaces"]
        opener = _FakeOpener({
            surfaces["classic_query"]: _Response(self.classic_html),
            surfaces["antonieta_product"]: _Response(self.antonieta_html),
        })
        result = discover_siope_routes(
            self.config,
            client=PublicSurfaceClient(
                allowed_hosts=tuple(self.config["allowed_hosts"]),
                max_response_bytes=self.config["max_response_bytes"],
                opener=opener,
            ),
        )
        self.assertEqual("CANDIDATE_IDENTIFIED_ARTIFACT_NOT_VERIFIED", result["acquisition_route_status"])
        self.assertEqual(
            "M7_SIOPE_ANTONIETA_ARTIFACT_VERIFICATION_GATE_0_8_0",
            result["next_gate"],
        )

    def test_dry_run_calls_no_network_and_authorizes_nothing(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "github_siope_route_discovery_gate.py"), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("PASS_M7_SIOPE_ROUTE_DISCOVERY_DRY_RUN", payload["status"])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["form_submission"])
        self.assertFalse(payload["captcha_bypass"])
        self.assertFalse(payload["artifact_downloaded"])
        self.assertFalse(payload["collection_authorized"])
        self.assertEqual("NONE", payload["remote_writes"])

    def test_response_size_limit_fails_closed(self):
        url = self.config["surfaces"]["classic_query"]
        opener = _FakeOpener({url: _Response("x" * 30)})
        client = PublicSurfaceClient(
            allowed_hosts=tuple(self.config["allowed_hosts"]),
            max_response_bytes=10,
            opener=opener,
        )
        with self.assertRaisesRegex(SiopeRouteDiscoveryError, "RESPONSE_TOO_LARGE"):
            client.get(url)


if __name__ == "__main__":
    unittest.main()
