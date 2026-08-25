import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-download-route-discovery-gate.yml"
PRODUCTION = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"


class TestM7SiopeDownloadRouteWorkflow(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.production = PRODUCTION.read_text(encoding="utf-8")

    def test_manual_only_and_confirmation_required(self):
        self.assertRegex(self.text, r"(?m)^  workflow_dispatch:\s*$")
        self.assertIn("confirm_download_route_discovery:", self.text)
        self.assertIn("inputs.confirm_download_route_discovery == true", self.text)
        self.assertNotRegex(self.text, r"(?m)^  schedule:\s*$")

    def test_read_only_permissions_and_pinned_actions(self):
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", self.text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", self.text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_full_qa_precedes_live_network(self):
        positions = [
            self.text.index("github_preflight.py"),
            self.text.index("--dry-run"),
            self.text.index("compileall"),
            self.text.index("unittest discover"),
            self.text.index("main.py selftest"),
            self.text.index("Descoberta passiva ao vivo"),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_only_sanitized_result_is_uploaded(self):
        self.assertIn("siope-download-route-evidence/result.json", self.text)
        self.assertIn("siope-download-route-discovery-${{ github.run_id }}", self.text)
        self.assertNotIn("$RUNNER_TEMP/siope_download_route_result.json\n          retention", self.text)

    def test_no_drive_collection_processing_or_artifact_fetch_commands(self):
        forbidden = (
            "GOOGLE_DRIVE_CLIENT_ID",
            "GOOGLE_DRIVE_CLIENT_SECRET",
            "GOOGLE_DRIVE_REFRESH_TOKEN",
            "DriveRESTClient",
            "main.py run",
            "github_processing_gate.py",
            "github_reconciliation_gate.py",
            "curl ",
            "wget ",
            "requests.get",
            "HEAD ",
        )
        for marker in forbidden:
            self.assertNotIn(marker, self.text)

    def test_production_workflow_cannot_reach_new_gate(self):
        self.assertNotIn("github_siope_download_route_discovery_gate.py", self.production)
        self.assertNotIn("confirm_download_route_discovery", self.production)


if __name__ == "__main__":
    unittest.main()
