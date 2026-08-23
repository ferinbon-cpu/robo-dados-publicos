import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from robo_dados_publicos.discovery.portal_probe import PortalProbe, sanitize_url


class DiscoveryHandler(BaseHTTPRequestHandler):
    robots_body = b"User-agent: *\nAllow: /\n"
    challenge = False

    def do_GET(self):
        if self.path == "/robots.txt":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(self.robots_body)))
            self.end_headers(); self.wfile.write(self.robots_body); return
        if self.path.startswith("/start"):
            self.send_response(302)
            self.send_header("Location", "/login.html")
            self.end_headers(); return
        if self.path == "/login.html":
            if self.challenge:
                body = b"<html><title>Verify</title><body>Verify you are human - CAPTCHA</body></html>"
            else:
                body = b'''<html><head><title>Portal</title><script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css"></head><body><a href="/public/export.csv">Export</a><form method="post" action="/api/query"></form></body></html>'''
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        self.send_response(404); self.end_headers()

    def log_message(self, *args):
        pass


class DisallowHandler(DiscoveryHandler):
    robots_body = b"User-agent: *\nDisallow: /start\n"


class ChallengeHandler(DiscoveryHandler):
    challenge = True


class TestTdaDiscovery(unittest.TestCase):
    def _run(self, handler):
        server = HTTPServer(("127.0.0.1", 0), handler)
        th = threading.Thread(target=server.serve_forever, daemon=True); th.start()
        self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_port}/start?token=secret&x=1"
        return PortalProbe(allow_insecure_localhost=True).probe(url)

    def test_passive_probe_maps_redirects_and_static_surface(self):
        out = self._run(DiscoveryHandler)
        self.assertEqual("PASS_DISCOVERY", out.status)
        self.assertEqual("SPA_ENTRY_OR_AUTH_GATE", out.surface_class)
        self.assertEqual(1, len(out.redirects))
        self.assertIn("%5BREDACTED%5D", out.requested_url)
        self.assertTrue(any(x.endswith("/assets/app.js") for x in out.scripts))
        self.assertTrue(any("export.csv" in x for x in out.endpoint_hints))
        self.assertTrue(any("/api/query" in x for x in out.endpoint_hints))

    def test_robots_disallow_stops_before_target_fetch(self):
        out = self._run(DisallowHandler)
        self.assertEqual("STOP_ROBOTS_DISALLOW", out.status)
        self.assertEqual("NOT_FETCHED", out.surface_class)
        self.assertIsNone(out.final_url)

    def test_human_challenge_is_detected_without_bypass(self):
        out = self._run(ChallengeHandler)
        self.assertEqual("STOP_HUMAN_CHALLENGE", out.status)
        self.assertTrue(out.challenge_detected)

    def test_sensitive_query_sanitizer(self):
        got = sanitize_url("https://example.org/a?token=abc&code=xyz&year=2026")
        self.assertNotIn("abc", got)
        self.assertNotIn("xyz", got)
        self.assertIn("year=2026", got)

    def test_sanitizer_preserves_nonstandard_valueless_public_query(self):
        url = "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418"
        self.assertEqual(url, sanitize_url(url))

    def test_json_output_contains_no_unredacted_query_secret(self):
        out = self._run(DiscoveryHandler)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "probe.json"
            PortalProbe.write_json(out, p)
            text = p.read_text(encoding="utf-8")
            self.assertNotIn("token=secret", text)
            parsed = json.loads(text)
            self.assertEqual("PASS_DISCOVERY", parsed["status"])


if __name__ == "__main__":
    unittest.main()
