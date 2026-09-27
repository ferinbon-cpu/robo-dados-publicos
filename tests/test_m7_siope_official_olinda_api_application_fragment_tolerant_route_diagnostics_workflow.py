from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "siope-official-olinda-api-application-fragment-tolerant-route-diagnostics-gate.yml"


class TestM7SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_manual_read_only_and_exact_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_official_olinda_application_fragment_tolerant_route_diagnostics:", self.text)
        self.assertIn("contents: read", self.text)
        self.assertNotIn("schedule:", self.text)
        self.assertNotIn("push:", self.text)

    def test_review_dry_run_and_full_qa_precede_live(self):
        review = self.text.index("github_siope_official_olinda_api_application_surface_boolean_diagnostics_review_gate.py")
        dry = self.text.index("github_siope_official_olinda_api_application_fragment_tolerant_route_diagnostics_gate.py --dry-run")
        tests = self.text.index("python -m unittest discover -s tests -v")
        regressions = self.text.index("python main.py selftest")
        live = self.text.index("--output siope-official-olinda-fragment-tolerant-route-diagnostics-evidence/result.json")
        self.assertLess(review, dry)
        self.assertLess(dry, tests)
        self.assertLess(tests, regressions)
        self.assertLess(regressions, live)

    def test_only_sanitized_result_uploaded_and_stop_propagates(self):
        self.assertIn("siope-official-olinda-fragment-tolerant-route-diagnostics-evidence/result.json", self.text)
        self.assertIn("if: ${{ steps.live.outcome == 'failure' }}", self.text)
        self.assertIn("run: exit 1", self.text)

    def test_workflow_has_no_direct_data_post_head_drive_or_limeira_command(self):
        lowered = self.text.lower()
        for forbidden in ("curl ", "wget ", "requests.get", "requests.post", "method=post", "method=head", "352690", "google drive", "gcloud auth"):
            self.assertNotIn(forbidden, lowered)

    def test_production_workflow_cannot_reach_new_gate(self):
        production = (ROOT / ".github" / "workflows" / "robo-dados-publicos.yml").read_text(encoding="utf-8")
        self.assertNotIn("github_siope_official_olinda_api_application_fragment_tolerant_route_diagnostics_gate.py", production)
        self.assertNotIn("M7 SIOPE OFFICIAL OLINDA APPLICATION FRAGMENT TOLERANT ROUTE DIAGNOSTICS GATE", production)


if __name__ == "__main__":
    unittest.main()
