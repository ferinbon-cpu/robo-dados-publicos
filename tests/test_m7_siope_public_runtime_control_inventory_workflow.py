from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-public-runtime-control-inventory-gate.yml"


class TestM7SiopePublicRuntimeControlInventoryWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_is_manual_read_only_and_requires_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_public_runtime_control_inventory", self.text)
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertNotIn("schedule:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertNotIn("push:", self.text)

    def test_full_qa_and_design_gates_precede_live_inventory(self):
        required = [
            "github_siope_runtime_dependency_preflight.py",
            "github_preflight.py",
            "github_source_expansion_design_gate.py",
            "github_siope_public_runtime_route_contract_review_gate.py",
            "github_siope_public_runtime_control_interaction_diagnostics_design_gate.py",
            "github_siope_public_runtime_control_inventory_gate.py --dry-run",
            "python -m compileall -q .",
            "python -m unittest discover -s tests -v",
            "python main.py selftest",
            "Inventariar controles DOM públicos sem interação",
        ]
        positions = [self.text.index(item) for item in required]
        self.assertEqual(positions, sorted(positions))

    def test_workflow_uploads_only_sanitized_result_and_propagates_stop(self):
        self.assertIn("siope-public-runtime-control-inventory-evidence/result.json", self.text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)
        self.assertIn("continue-on-error: true", self.text)
        self.assertIn("steps.live.outcome == 'failure'", self.text)
        for forbidden in ("curl ", "wget ", "gh api", "gcloud", "drive", "oauth", "selenium", "playwright"):
            self.assertNotIn(forbidden, self.text.lower())

    def test_workflow_does_not_encode_interaction_or_form_submission(self):
        for forbidden in ("click", "dispatchEvent", "requestSubmit", ".submit(", "--head", "download-artifact"):
            self.assertNotIn(forbidden, self.text)


if __name__ == "__main__":
    unittest.main()
