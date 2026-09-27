from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.sources.siope_download_route_discovery import TextResponse
from robo_dados_publicos.sources.siope_public_report_surface import (
    SiopePublicReportSurfaceError,
    discover_public_report_surface,
    extract_form_contracts,
    find_exact_declared_data_link,
    load_public_report_surface_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_report_surface_gate.json"
SCRIPT = ROOT / "scripts" / "github_siope_public_report_surface_gate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-public-report-surface-gate.yml"


class FakeClient:
    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.calls: list[str] = []

    def get_text(self, url: str, *, max_bytes: int, allowed_content_types: tuple[str, ...]):
        self.calls.append(url)
        body = self.responses[url]
        return TextResponse(url=url, status=200, content_type="text/html", body=body, byte_count=len(body.encode()))


class TestM7SiopePublicReportSurface(unittest.TestCase):
    def setUp(self):
        self.cfg = load_public_report_surface_config(CONFIG)

    def test_exact_declared_data_link_is_required(self):
        html = '<a href="/siope/dadosInformadosMunicipio.do">Dados Informados pelos Municípios</a>'
        item = find_exact_declared_data_link(
            html,
            page_url=self.cfg["index_url"],
            required_anchor=self.cfg["required_index_anchor_text"],
            data_page_url=self.cfg["data_page_url"],
        )
        self.assertIsNotNone(item)
        self.assertEqual(item["host"], "webservice.fnde.gov.br")
        self.assertFalse(item["network_sent"])

    def test_wrong_anchor_or_route_is_not_promoted(self):
        html = '<a href="/siope/outro.do">Dados Informados pelos Municípios</a>'
        self.assertIsNone(find_exact_declared_data_link(
            html,
            page_url=self.cfg["index_url"],
            required_anchor=self.cfg["required_index_anchor_text"],
            data_page_url=self.cfg["data_page_url"],
        ))

    def test_form_contract_keeps_names_not_values(self):
        html = '''<form method="post" action="/siope/dadosInformadosMunicipio.do">
        <input type="hidden" name="token" value="SECRET">
        <select name="ano"><option value="2024">2024</option></select>
        <input type="text" name="municipio" value="Limeira">
        </form>'''
        forms = extract_form_contracts(
            html,
            page_url=self.cfg["data_page_url"],
            allowed_hosts=("webservice.fnde.gov.br",),
            max_forms=8,
            max_fields=48,
        )
        payload = json.dumps(forms)
        self.assertEqual(forms[0]["method"], "POST")
        self.assertEqual(forms[0]["action"]["status"], "OFFICIAL_ALLOWLIST")
        self.assertEqual([f["name"] for f in forms[0]["fields"]], ["token", "ano", "municipio"])
        self.assertNotIn("SECRET", payload)
        self.assertNotIn("Limeira", payload)
        self.assertFalse(forms[0]["action"]["network_sent"])

    def test_live_style_discovery_reads_only_exact_two_pages_and_never_submits(self):
        index = '<a href="/siope/dadosInformadosMunicipio.do">Dados Informados pelos Municípios</a>'
        data = '''<html><body><form method="GET" action="/siope/dadosInformadosMunicipio.do">
        <select name="ano"></select><select name="periodo"></select><select name="uf"></select><select name="municipio"></select>
        </form></body></html>'''
        fake = FakeClient({self.cfg["index_url"]: index, self.cfg["data_page_url"]: data})
        result = discover_public_report_surface(self.cfg, client=fake)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_REPORT_SURFACE_GATE")
        self.assertEqual(fake.calls, [self.cfg["index_url"], self.cfg["data_page_url"]])
        self.assertFalse(result["form_submission"])
        self.assertFalse(result["form_action_network_sent"])
        self.assertFalse(result["collection_authorized"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_REPORT_FORM_CONTRACT_VERIFICATION_0_8_0")

    def test_captcha_routes_to_human_challenge_without_bypass(self):
        index = '<a href="/siope/dadosInformadosMunicipio.do">Dados Informados pelos Municípios</a>'
        data = '<form action="/siope/dadosInformadosMunicipio.do"><input name="ano"></form><div class="g-recaptcha"></div>'
        fake = FakeClient({self.cfg["index_url"]: index, self.cfg["data_page_url"]: data})
        result = discover_public_report_surface(self.cfg, client=fake)
        self.assertTrue(result["captcha_present"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_REPORT_HUMAN_CHALLENGE_DECISION_0_8_0")
        self.assertFalse(result["form_submission"])

    def test_missing_form_contract_stops(self):
        index = '<a href="/siope/dadosInformadosMunicipio.do">Dados Informados pelos Municípios</a>'
        fake = FakeClient({self.cfg["index_url"]: index, self.cfg["data_page_url"]: '<html>sem formulário</html>'})
        with self.assertRaises(SiopePublicReportSurfaceError):
            discover_public_report_surface(self.cfg, client=fake)

    def test_dry_run_authorizes_nothing(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_REPORT_SURFACE_DRY_RUN")
        self.assertFalse(result["form_submission"])
        self.assertFalse(result["collection_authorized"])
        self.assertFalse(result["artifact_downloaded"])

    def test_workflow_is_manual_read_only_and_full_qa(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_public_report_surface", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        lower = text.lower()
        self.assertNotIn("schedule:", lower)
        self.assertNotIn("curl ", lower)
        self.assertNotIn("wget ", lower)
        self.assertNotIn("--head", lower)


if __name__ == "__main__":
    unittest.main()
