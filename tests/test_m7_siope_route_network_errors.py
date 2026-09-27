import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_route_discovery import (
    PublicSurfaceClient,
    SiopeRouteDiscoveryError,
    discover_siope_routes,
    load_route_discovery_config,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_route_discovery_gate.json"


class _Headers(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class _Response:
    def __init__(self, body: str, *, url: str, content_type: str = "text/html", status: int = 200):
        self._body = body.encode("utf-8")
        self._url = url
        self.headers = _Headers({"Content-Type": content_type})
        self.status = status

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url

    def read(self, _limit):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _TimeoutThenAntonietaOpener:
    def __init__(self, classic_url: str, antonieta_url: str, antonieta_html: str):
        self.classic_url = classic_url
        self.antonieta_url = antonieta_url
        self.antonieta_html = antonieta_html
        self.calls = []

    def __call__(self, request, timeout=0):
        self.calls.append((request.full_url, timeout))
        if request.full_url == self.classic_url:
            raise TimeoutError("simulated timeout")
        if request.full_url == self.antonieta_url:
            return _Response(self.antonieta_html, url=self.antonieta_url)
        raise AssertionError(request.full_url)


class TestM7SiopeRouteNetworkErrors(unittest.TestCase):
    def setUp(self):
        self.config = load_route_discovery_config(CONFIG)
        self.classic = self.config["surfaces"]["classic_query"]
        self.antonieta = self.config["surfaces"]["antonieta_product"]
        self.antonieta_html = (
            "<html><body><h1>Dados Gerais - SIOPE</h1>"
            "<div>exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz</div>"
            "<button>Exportar artefato</button></body></html>"
        )

    def test_native_timeout_is_sanitized_as_route_timeout(self):
        def opener(_request, timeout=0):
            self.assertEqual(20, timeout)
            raise TimeoutError("raw network detail must not escape")

        client = PublicSurfaceClient(
            allowed_hosts=tuple(self.config["allowed_hosts"]),
            max_response_bytes=self.config["max_response_bytes"],
            opener=opener,
        )
        with self.assertRaisesRegex(SiopeRouteDiscoveryError, "^STOP_SIOPE_ROUTE_TIMEOUT$"):
            client.get(self.classic)

    def test_classic_timeout_does_not_abort_required_antonieta_probe(self):
        opener = _TimeoutThenAntonietaOpener(self.classic, self.antonieta, self.antonieta_html)
        client = PublicSurfaceClient(
            allowed_hosts=tuple(self.config["allowed_hosts"]),
            max_response_bytes=self.config["max_response_bytes"],
            opener=opener,
        )
        result = discover_siope_routes(self.config, client=client)
        self.assertEqual("PASS_M7_SIOPE_ROUTE_DISCOVERY_GATE", result["status"])
        self.assertEqual("UNAVAILABLE_OR_BLOCKED", result["classic_query"]["status"])
        self.assertEqual("STOP_SIOPE_ROUTE_TIMEOUT", result["classic_query"]["reason"])
        self.assertTrue(result["preferred_candidate"]["product_name_verified"])
        self.assertEqual([self.classic, self.antonieta], [url for url, _ in opener.calls])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["collection_authorized"])
        self.assertEqual("NONE", result["remote_writes"])

    def test_redirect_to_non_allowlisted_host_fails_closed(self):
        def opener(_request, timeout=0):
            return _Response("<html></html>", url="https://example.com/redirected")

        client = PublicSurfaceClient(
            allowed_hosts=tuple(self.config["allowed_hosts"]),
            max_response_bytes=self.config["max_response_bytes"],
            opener=opener,
        )
        with self.assertRaisesRegex(SiopeRouteDiscoveryError, "REDIRECT_HOST_NOT_ALLOWED"):
            client.get(self.antonieta)


if __name__ == "__main__":
    unittest.main()
