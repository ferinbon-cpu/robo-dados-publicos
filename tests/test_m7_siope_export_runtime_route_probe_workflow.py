from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-export-runtime-route-probe-gate.yml"


class TestM7SiopeExportRuntimeRouteProbeWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_manual_only_and_confirmation_required(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_export_runtime_route_probe", self.text)
        self.assertNotIn("schedule:", self.text)
        self.assertNotIn("push:", self.text)

    def test_read_only_permissions_and_pinned_actions(self):
        self.assertIn("contents: read", self.text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", self.text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", self.text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)

    def test_no_browser_download_or_system_package_install(self):
        lowered = self.text.lower()
        for forbidden in ("playwright install", "apt-get", "apt ", "wget ", "curl ", "chromedriver install"):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("requirements-runtime-probe.txt", self.text)

    def test_full_qa_precedes_live_probe(self):
        live = self.text.index("Probe runtime ao vivo com abort antes da rede")
        for marker in ("Preflight offline da candidata", "Validar desenho do runtime probe", "Dry-run sem navegador e sem rede", "Compilar", "Testes unitários", "Regressão histórica"):
            self.assertLess(self.text.index(marker), live)

    def test_no_drive_collection_processing_or_head_commands(self):
        lowered = self.text.lower()
        for forbidden in ("drive", "oauth", "source collection", "source_processing", "curl -i", "curl --head", "requests.head"):
            self.assertNotIn(forbidden, lowered)

    def test_only_sanitized_result_is_uploaded(self):
        self.assertIn("siope-export-runtime-route-evidence/result.json", self.text)
        self.assertNotIn("$RUNNER_TEMP/siope_export_runtime_route_result.json\n          retention-days", self.text)


if __name__ == "__main__":
    unittest.main()
