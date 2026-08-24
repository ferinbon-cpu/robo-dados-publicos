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
    status = 200
    headers = _Headers({"Content-Type": "text/html"})

    def __init__(self, body: str):
        self.body = body.encode("utf-8")

    def getcode(self):
        return self.status

    def read(self, _limit):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _ClassicBlockedOpener:
    def __init__(self, classic_url: str, antonieta_url: str, antonieta_html: str):
        self.classic_url = classic_url
        self.antonieta_url = antonieta_url
        self.antonieta_html = antonieta_html
        self.calls = []

    def __call__(self, request, timeout=0):
        self.calls.append((request.full_url, request.get_method(), timeout))
        if request.full_url == self.classic_url:
            raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_HTTP_STATUS")
        if request.full_url == self.antonieta_url:
            return _Response(self.antonieta_html)
        raise AssertionError(request.full_url)


class TestM7SiopeRouteResilience(unittest.TestCase):
    def test_classic_block_does_not_force_captcha_bypass_or_abort_antonieta(self):
        config = load_route_discovery_config(CONFIG)
        surfaces = config["surfaces"]
        expected = config["expected_antonieta"]
        antonieta_html = (
            f"<h1>{expected['product_name']}</h1>"
            f"<div>{expected['artifact_path']}</div>"
        )
        opener = _ClassicBlockedOpener(
            surfaces["classic_query"], surfaces["antonieta_product"], antonieta_html
        )
        client = PublicSurfaceClient(
            allowed_hosts=tuple(config["allowed_hosts"]),
            max_response_bytes=config["max_response_bytes"],
            opener=opener,
        )
        result = discover_siope_routes(config, client=client)
        self.assertEqual("PASS_M7_SIOPE_ROUTE_DISCOVERY_GATE", result["status"])
        self.assertEqual("UNAVAILABLE_OR_BLOCKED", result["classic_query"]["status"])
        self.assertEqual(
            "BLOCK_AUTOMATED_ACQUISITION_SURFACE_UNAVAILABLE",
            result["classic_query"]["acquisition_decision"],
        )
        self.assertEqual("OBSERVED", result["preferred_candidate"]["status"])
        self.assertFalse(result["captcha_bypass"])
        self.assertFalse(result["form_submission"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertEqual(2, len(opener.calls))


if __name__ == "__main__":
    unittest.main()
