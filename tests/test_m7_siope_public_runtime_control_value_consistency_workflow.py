from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-public-runtime-control-value-consistency-diagnostics-gate.yml"
PRODUCTION = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"


class TestM7SiopePublicRuntimeControlValueConsistencyWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_is_manual_read_only_and_requires_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_public_runtime_control_value_consistency_diagnostics", self.text)
        self.assertIn("contents: read", self.text)
        self.assertNotIn("schedule:", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_full_qa_and_design_precede_live(self):
        design = self.text.index("github_siope_public_runtime_control_value_consistency_diagnostics_design_gate.py")
        dry = self.text.index("github_siope_public_runtime_control_value_consistency_diagnostics_gate.py --dry-run")
        tests = self.text.index("python -m unittest discover -s tests -v")
        regression = self.text.index("python main.py selftest")
        live = self.text.index("--output siope-public-runtime-control-value-consistency-evidence/result.json")
        self.assertLess(design, dry)
        self.assertLess(dry, tests)
        self.assertLess(tests, regression)
        self.assertLess(regression, live)

    def test_only_sanitized_result_is_uploaded_and_stop_propagates(self):
        self.assertIn("siope-public-runtime-control-value-consistency-evidence/result.json", self.text)
        self.assertIn("if: ${{ always() }}", self.text)
        self.assertIn("steps.live.outcome == 'failure'", self.text)
        self.assertNotIn("actions/download-artifact", self.text)

    def test_workflow_does_not_submit_post_or_send_pilot_values(self):
        lowered = self.text.lower()
        for forbidden in ("curl ", "wget ", "page.navigate", "form.submit", "request.post", "cod_muni=352690"):
            self.assertNotIn(forbidden, lowered)
        self.assertNotIn("google_drive", lowered)

    def test_production_workflow_cannot_reach_consistency_gate(self):
        production = PRODUCTION.read_text(encoding="utf-8")
        self.assertNotIn("control_value_consistency", production)
        self.assertNotIn("github_siope_public_runtime_control_value_consistency_diagnostics_gate.py", production)


if __name__ == "__main__":
    unittest.main()
