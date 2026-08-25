import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-export-callsite-route-gate.yml"
PRODUCTION = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"


class TestM7SiopeExportCallsiteWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.production = PRODUCTION.read_text(encoding="utf-8")

    def test_manual_only_and_confirmation_required(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_export_callsite_route_discovery:", self.text)
        self.assertIn("inputs.confirm_export_callsite_route_discovery == true", self.text)
        self.assertNotIn("schedule:", self.text.split("permissions:", 1)[0])

    def test_read_only_permissions_and_pinned_actions(self):
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", self.text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", self.text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)

    def test_full_qa_precedes_live_network(self):
        live = self.text.index("Descoberta passiva ao vivo")
        self.assertLess(self.text.index("Preflight offline da candidata"), live)
        self.assertLess(self.text.index("Dry-run sem rede"), live)
        self.assertLess(self.text.index("Testes unitários"), live)
        self.assertLess(self.text.index("Regressão histórica"), live)

    def test_no_browser_click_download_drive_or_collection_commands(self):
        forbidden = ["playwright", "selenium", "chromium", "google-chrome", "gcloud", "drive", "main.py run", "curl ", "wget ", "requests.head"]
        lower = self.text.lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), lower)

    def test_production_workflow_cannot_reach_callsite_gate(self):
        self.assertNotIn("github_siope_export_callsite_route_gate.py", self.production)
        self.assertNotIn("M7 SIOPE EXPORT CALLSITE ROUTE DISCOVERY GATE", self.production)


if __name__ == "__main__":
    unittest.main()
