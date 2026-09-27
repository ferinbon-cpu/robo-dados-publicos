from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-public-runtime-action-control-semantics-diagnostics-gate.yml"


class TestM7SiopePublicRuntimeActionControlSemanticsWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_is_manual_read_only_and_requires_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_public_runtime_action_control_semantics_diagnostics", self.text)
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertNotIn("schedule:", self.text)
        self.assertNotIn("push:", self.text)
        self.assertNotIn("pull_request:", self.text)

    def test_full_qa_and_design_precede_live_gate(self):
        live = self.text.index("Observar relações booleanas do hidden acao")
        for marker in (
            "github_siope_public_runtime_control_value_consistency_review_gate.py",
            "github_siope_public_runtime_action_control_semantics_diagnostics_design_gate.py",
            "github_siope_public_runtime_action_control_semantics_diagnostics_gate.py --dry-run",
            "python -m unittest discover -s tests -v",
            "python main.py selftest",
        ):
            self.assertLess(self.text.index(marker), live)

    def test_workflow_has_no_submit_post_download_or_drive_command(self):
        lower = self.text.lower()
        self.assertNotIn("curl ", lower)
        self.assertNotIn("wget ", lower)
        self.assertNotIn("gdrive", lower)
        self.assertNotIn("google drive", lower)
        self.assertNotIn("--post", lower)
        self.assertNotIn("head -", lower)

    def test_only_sanitized_result_is_uploaded_and_stop_propagates(self):
        self.assertIn("siope-public-runtime-action-control-semantics-evidence/result.json", self.text)
        self.assertIn("if: ${{ steps.live.outcome == 'failure' }}", self.text)
        self.assertIn("run: exit 1", self.text)


if __name__ == "__main__":
    unittest.main()
