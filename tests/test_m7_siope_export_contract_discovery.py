import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_download_route_discovery import ReadOnlyDeclaredResourceClient
from robo_dados_publicos.sources.siope_export_contract_discovery import (
    SiopeExportContractDiscoveryError,
    discover_export_contract,
    extract_route_templates,
    load_export_contract_discovery_config,
    summarize_export_controls,
    summarize_script_signals,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_contract_discovery_gate.json"


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


class TestM7SiopeExportContractDiscovery(unittest.TestCase):
    def setUp(self):
        self.config = load_export_contract_discovery_config(CONFIG)
        self.page_url = self.config["page_url"]
        self.script_url = "https://www.fnde.gov.br/assets/app.js"
        self.page_html = """
        <html><body>
          <h1>Dados Gerais - SIOPE</h1>
          <div>exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz</div>
          <button id="export" data-action="exportArtifact" data-product-id="20">Exportar artefato</button>
          <script>
            const btn = document.querySelector('[data-action="exportArtifact"]');
            btn.addEventListener('click', () => {
              const productId = btn.dataset.productId;
              const route = `/plataforma/api/artefatos/${productId}/export`;
              window.location.href = route;
            });
          </script>
          <script src="/assets/app.js"></script>
        </body></html>
        """

    def test_config_is_read_only_and_forbids_click_browser_and_download(self):
        self.assertEqual("PASSIVE_EXPORT_CONTRACT_DISCOVERY_ONLY", self.config["mode"])
        self.assertEqual("PROHIBITED", self.config["artifact_download"])
        self.assertEqual("PROHIBITED", self.config["head_request"])
        self.assertEqual("PROHIBITED", self.config["browser_automation"])
        self.assertEqual("PROHIBITED", self.config["click_execution"])
        self.assertEqual("PROHIBITED", self.config["remote_writes"])
        self.assertEqual("DISABLED", self.config["schedule"])

    def test_export_control_reports_attribute_name_and_safe_public_value_only(self):
        controls = summarize_export_controls(
            self.page_html,
            artifact_basename="SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            keywords=("download", "export", "artefato", "artifact"),
        )
        self.assertEqual(1, len(controls))
        attr = controls[0]["export_data_attributes"][0]
        self.assertEqual("data-action", attr["name"])
        self.assertEqual("EXPORT_IDENTIFIER", attr["value_class"])
        self.assertEqual("exportArtifact", attr["safe_public_value"])
        self.assertFalse(controls[0]["href_present"])
        self.assertFalse(controls[0]["action_present"])

    def test_dynamic_backtick_route_template_is_observed_but_not_called(self):
        script = "const route = `/api/artefatos/${productId}/export`;"
        templates = extract_route_templates(
            script,
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            artifact_basename="SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            keywords=("download", "export", "artefato", "artifact"),
        )
        self.assertEqual(1, len(templates))
        self.assertTrue(templates[0]["dynamic"])
        self.assertEqual("TEMPLATE_LITERAL", templates[0]["literal_kind"])
        self.assertIn("{VAR}", templates[0]["template_without_query"])

    def test_script_signals_detect_dataset_event_and_navigation(self):
        script = """
        btn.addEventListener('click', () => {
          const id = btn.dataset.productId;
          const route = `/api/artefatos/${id}/export`;
          window.location.href = route;
        });
        """
        signal = summarize_script_signals(
            script,
            source_kind="INLINE_SCRIPT",
            source_index=1,
            byte_count=len(script.encode("utf-8")),
            base_url=self.page_url,
            allowed_hosts=("www.fnde.gov.br",),
            artifact_basename="SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
            keywords=("download", "export", "artefato", "artifact"),
        )
        self.assertIn("productId", signal.dataset_keys)
        self.assertGreater(signal.mechanisms["event_listener"], 0)
        self.assertGreater(signal.mechanisms["location_navigation"], 0)
        self.assertGreater(len(signal.route_templates), 0)

    def test_discovery_reads_only_page_and_declared_script_never_route_template(self):
        external_body = "const generic = 'no export contract here';"
        opener = _FakeOpener({
            self.page_url: _Response(self.page_url, self.page_html, "text/html"),
            self.script_url: _Response(self.script_url, external_body, "application/javascript"),
        })
        result = discover_export_contract(
            self.config,
            client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
        )
        self.assertEqual("PASS_M7_SIOPE_EXPORT_CONTRACT_DISCOVERY_GATE", result["status"])
        self.assertEqual([self.page_url, self.script_url], [call[0] for call in opener.calls])
        self.assertEqual("ROUTE_TEMPLATE_OBSERVED_NOT_CALLED", result["export_contract_status"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["head_request_performed"])
        self.assertFalse(result["browser_automation_performed"])
        self.assertFalse(result["click_executed"])
        self.assertFalse(result["collection_authorized"])
        self.assertEqual("NONE", result["remote_writes"])

    def test_no_export_control_or_script_signal_fails_closed(self):
        html = """
        <html><body>
          <h1>Dados Gerais - SIOPE</h1>
          <div>exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz</div>
        </body></html>
        """
        opener = _FakeOpener({self.page_url: _Response(self.page_url, html, "text/html")})
        with self.assertRaisesRegex(SiopeExportContractDiscoveryError, "NOT_OBSERVED"):
            discover_export_contract(
                self.config,
                client=ReadOnlyDeclaredResourceClient(allowed_hosts=("www.fnde.gov.br",), opener=opener),
            )

    def test_dry_run_authorizes_nothing(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "github_siope_export_contract_discovery_gate.py"), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("PASS_M7_SIOPE_EXPORT_CONTRACT_DISCOVERY_DRY_RUN", payload["status"])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["artifact_downloaded"])
        self.assertFalse(payload["browser_automation_performed"])
        self.assertFalse(payload["click_executed"])
        self.assertFalse(payload["collection_authorized"])
        self.assertEqual("NONE", payload["remote_writes"])


if __name__ == "__main__":
    unittest.main()
