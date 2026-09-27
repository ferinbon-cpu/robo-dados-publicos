import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-route-discovery-gate.yml"
PRODUCTION = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"


class TestM7SiopeRouteWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.active_lines = [line for line in cls.text.splitlines() if not line.lstrip().startswith("#")]

    def test_manual_only_and_explicit_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_route_discovery:", self.text)
        self.assertIn("default: false", self.text)
        self.assertIn("inputs.confirm_route_discovery == true", self.text)
        self.assertFalse(any(line.strip() == "schedule:" for line in self.active_lines))

    def test_read_only_github_permissions_pinned_actions_and_no_oauth(self):
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", self.text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", self.text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)
        self.assertIn("persist-credentials: false", self.text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_ID", self.text)
        self.assertNotIn("GOOGLE_DRIVE_CLIENT_SECRET", self.text)
        self.assertNotIn("GOOGLE_DRIVE_REFRESH_TOKEN", self.text)

    def test_full_qa_and_dry_run_precede_live_gets(self):
        preflight = self.text.index("python scripts/github_preflight.py")
        dry = self.text.index("github_siope_route_discovery_gate.py --dry-run")
        compile_step = self.text.index("python -m compileall -q .")
        unit = self.text.index("python -m unittest discover -s tests -v")
        history = self.text.index("python main.py selftest")
        live = self.text.index('github_siope_route_discovery_gate.py > "$RUNNER_TEMP/siope_route_result.json"')
        self.assertLess(preflight, dry)
        self.assertLess(dry, compile_step)
        self.assertLess(compile_step, unit)
        self.assertLess(unit, history)
        self.assertLess(history, live)

    def test_workflow_contains_no_collection_processing_reconciliation_or_drive_commands(self):
        forbidden = (
            "main.py run",
            "sources.jornal_oficial_7310_gate.json",
            "github_processing_gate.py",
            "github_reconciliation_gate.py",
            "github_product_publication_gate.py",
            "DriveRESTClient",
            "outputs_id",
            "confirm_source_collection",
            "confirm_processing",
            "confirm_reconciliation",
            "confirm_product_publication",
        )
        for marker in forbidden:
            self.assertNotIn(marker, self.text)

    def test_only_sanitized_result_is_artifact(self):
        self.assertIn("siope-route-evidence/result.json", self.text)
        self.assertIn("siope-route-discovery-${{ github.run_id }}", self.text)
        self.assertNotIn("$RUNNER_TEMP/siope_route_result.json\n          retention", self.text)
        self.assertNotIn(".txt.gz", self.text)

    def test_production_workflow_cannot_reach_route_discovery(self):
        production = PRODUCTION.read_text(encoding="utf-8")
        self.assertNotIn("confirm_route_discovery", production)
        self.assertNotIn("github_siope_route_discovery_gate.py", production)
        self.assertNotIn("source_expansion.siope_route_discovery_gate.json", production)


if __name__ == "__main__":
    unittest.main()
