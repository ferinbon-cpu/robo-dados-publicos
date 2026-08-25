from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.sources.siope_download_route_discovery import TextResponse
from robo_dados_publicos.sources.siope_ws_public_discovery import (
    SiopeWsPublicDiscoveryError,
    discover_ws_public_surface,
    extract_declared_ws_links,
    load_ws_public_discovery_config,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_ws_public_discovery_design.json"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-ws-public-discovery-gate.yml"
SCRIPT = ROOT / "scripts" / "github_siope_ws_public_discovery_gate.py"


class FakeClient:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.calls: list[str] = []

    def get_text(self, url: str, *, max_bytes: int, allowed_content_types: tuple[str, ...]):
        self.calls.append(url)
        body = self.responses.get(url, "<html><body>sem sinal</body></html>")
        return TextResponse(url=url, status=200, content_type="text/html", body=body, byte_count=len(body.encode()))


class TestM7SiopeWsPublicDiscovery(unittest.TestCase):
    def setUp(self):
        self.cfg = load_ws_public_discovery_config(CONFIG)

    def test_query_values_are_removed_from_declared_endpoint(self):
        html = '<a href="https://webservice.fnde.gov.br/siope/webservice?token=SECRET&ano=2024">WS-SIOPE webservice</a>'
        links = extract_declared_ws_links(
            html,
            page_url="https://www.fnde.gov.br/siope/download.do",
            allowed_hosts=("www.fnde.gov.br", "webservice.fnde.gov.br"),
        )
        self.assertEqual(len(links), 1)
        item = links[0]
        self.assertEqual(item["classification"], "EXPLICIT_WS_ENDPOINT_LINK")
        self.assertEqual(item["query_keys"], ["ano", "token"])
        self.assertNotIn("SECRET", json.dumps(item))
        self.assertNotIn("2024", json.dumps(item))
        self.assertFalse(item["network_sent"])

    def test_textual_ws_siope_mention_without_explicit_link_stops(self):
        responses = {
            self.cfg["initial_urls"][0]: "<html><body>Inclusão indicadores no WS-SIOPE</body></html>",
            self.cfg["initial_urls"][1]: "<html><body>Dados informados</body></html>",
        }
        fake = FakeClient(responses)
        with self.assertRaises(SiopeWsPublicDiscoveryError) as ctx:
            discover_ws_public_surface(self.cfg, client=fake)
        self.assertIn("NO_EXPLICIT_ENDPOINT_OR_DOCUMENTATION", str(ctx.exception))
        self.assertEqual(fake.calls, self.cfg["initial_urls"])
        self.assertFalse(ctx.exception.diagnostics["endpoint_candidate_network_sent"])

    def test_explicit_endpoint_link_passes_without_fetching_endpoint(self):
        endpoint = "https://webservice.fnde.gov.br/siope/webservice?wsdl=true&token=SECRET"
        responses = {
            self.cfg["initial_urls"][0]: f'<html><body><a href="{endpoint}">Webservice WS-SIOPE</a></body></html>',
            self.cfg["initial_urls"][1]: "<html><body>Dados informados</body></html>",
        }
        fake = FakeClient(responses)
        result = discover_ws_public_surface(self.cfg, client=fake)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_WS_PUBLIC_DISCOVERY_GATE")
        self.assertEqual(result["explicit_candidate_count"], 1)
        self.assertNotIn(endpoint, fake.calls)
        self.assertEqual(fake.calls, self.cfg["initial_urls"])
        self.assertFalse(result["endpoint_candidate_network_sent"])
        payload = json.dumps(result)
        self.assertNotIn("SECRET", payload)

    def test_explicit_text_documentation_may_be_followed_but_binary_is_not(self):
        doc = "https://www.fnde.gov.br/siope/manual-integracao.html"
        pdf = "https://www.fnde.gov.br/siope/manual-integracao.pdf"
        first = (
            '<html><body>WS-SIOPE '
            f'<a href="{doc}">Manual de integração</a> '
            f'<a href="{pdf}">Manual de integração</a>'
            '</body></html>'
        )
        responses = {
            self.cfg["initial_urls"][0]: first,
            self.cfg["initial_urls"][1]: "<html><body>Dados informados</body></html>",
            doc: "<html><body>Documentação pública do WS-SIOPE</body></html>",
        }
        fake = FakeClient(responses)
        result = discover_ws_public_surface(self.cfg, client=fake)
        self.assertIn(doc, fake.calls)
        self.assertNotIn(pdf, fake.calls)
        self.assertGreaterEqual(result["explicit_candidate_count"], 2)

    def test_design_keeps_authentication_collection_and_download_closed(self):
        rules = self.cfg["discovery_rules"]
        self.assertFalse(rules["authenticate"])
        self.assertFalse(rules["bypass_captcha"])
        self.assertFalse(rules["capture_credentials"])
        self.assertFalse(rules["capture_cookies"])
        self.assertFalse(rules["download_artifacts"])
        self.assertFalse(self.cfg["collection_authorized"])
        self.assertFalse(self.cfg["processing_authorized"])
        self.assertFalse(self.cfg["recurrence_authorized"])
        self.assertFalse(self.cfg["schedule_enabled"])

    def test_direct_dry_run_has_no_network_or_authorization(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_WS_PUBLIC_DISCOVERY_DRY_RUN")
        self.assertFalse(result["endpoint_candidate_network_sent"])
        self.assertFalse(result["authentication_performed"])
        self.assertFalse(result["artifact_downloaded"])

    def test_workflow_is_manual_read_only_full_qa_and_sanitized(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_ws_public_discovery", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("siope-ws-public-discovery-evidence/result.json", text)
        lower = text.lower()
        self.assertNotIn("schedule:", lower)
        self.assertNotIn("curl ", lower)
        self.assertNotIn("wget ", lower)
        self.assertNotIn("--head", lower)


if __name__ == "__main__":
    unittest.main()
