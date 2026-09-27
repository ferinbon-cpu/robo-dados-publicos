from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-official-olinda-api-service-discovery-gate.yml"
PRODUCTION = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"


class TestM7SiopeOfficialOlindaApiServiceDiscoveryWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.production = PRODUCTION.read_text(encoding="utf-8")

    def test_workflow_is_manual_read_only_and_requires_exact_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_official_olinda_api_service_discovery", self.text)
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertNotIn("schedule:", self.text)
        self.assertNotIn("push:", self.text)
        self.assertNotIn("pull_request:", self.text)

    def test_design_dry_run_and_full_qa_precede_live(self):
        live = self.text.index("Descobrir catálogo raiz oficial Olinda SIOPE")
        for marker in (
            "github_siope_public_indexed_get_second_example_discovery_design_gate.py",
            "github_siope_official_olinda_api_discovery_design_gate.py",
            "github_siope_official_olinda_api_service_discovery_gate.py --dry-run",
            "python -m compileall -q .",
            "python -m unittest discover -s tests -v",
            "python main.py selftest",
        ):
            self.assertLess(self.text.index(marker), live)

    def test_workflow_has_no_direct_http_post_head_browser_drive_or_pilot_command(self):
        lower = self.text.lower()
        for forbidden in ("curl ", "wget ", "--post", "head -", "websocket", "page.navigate", "gdrive", "google drive", "352690"):
            self.assertNotIn(forbidden, lower)

    def test_only_sanitized_result_is_uploaded_and_stop_propagates(self):
        path = "siope-official-olinda-api-service-discovery-evidence/result.json"
        self.assertEqual(self.text.count(path), 2)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)
        self.assertIn("if: ${{ steps.live.outcome == 'failure' }}", self.text)
        self.assertIn("run: exit 1", self.text)

    def test_production_workflow_cannot_reach_new_live_gate(self):
        self.assertNotIn("github_siope_official_olinda_api_service_discovery_gate.py", self.production)
        self.assertNotIn("M7 SIOPE OFFICIAL OLINDA API SERVICE DISCOVERY GATE", self.production)


if __name__ == "__main__":
    unittest.main()
