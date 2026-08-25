import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-export-contract-discovery-gate.yml"


class TestM7SiopeExportContractWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_manual_only_and_confirmation_required(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_export_contract_discovery:", self.text)
        self.assertNotIn("schedule:", self.text)
        self.assertNotIn("push:", self.text)

    def test_read_only_permissions_and_pinned_actions(self):
        self.assertIn("contents: read", self.text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", self.text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", self.text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)

    def test_no_browser_click_download_drive_or_collection_commands(self):
        lower = self.text.lower()
        for forbidden in (
            "playwright",
            "selenium",
            "puppeteer",
            "curl ",
            "wget ",
            "drive_rest",
            "google_drive",
            "source_collection",
            "processing_gate",
            "reconciliation_gate",
        ):
            self.assertNotIn(forbidden, lower)

    def test_full_qa_precedes_live_network(self):
        preflight = self.text.index("Preflight offline da candidata")
        dry = self.text.index("Dry-run sem rede")
        unit = self.text.index("Testes unitários")
        regression = self.text.index("Regressão histórica")
        live = self.text.index("Descoberta passiva ao vivo")
        self.assertLess(preflight, dry)
        self.assertLess(dry, unit)
        self.assertLess(unit, regression)
        self.assertLess(regression, live)

    def test_only_sanitized_result_is_uploaded(self):
        self.assertIn("siope-export-contract-evidence/result.json", self.text)
        self.assertNotIn("$RUNNER_TEMP/siope_export_contract_result.json\n          retention-days", self.text)


if __name__ == "__main__":
    unittest.main()
