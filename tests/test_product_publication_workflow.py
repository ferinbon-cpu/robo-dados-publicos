import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "product-output-publication-gate.yml"


class TestProductPublicationWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.active_lines = [line for line in cls.text.splitlines() if not line.lstrip().startswith("#")]

    def test_workflow_is_manual_only_and_requires_exact_confirmation(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("confirm_product_publication:", self.text)
        self.assertIn("default: false", self.text)
        self.assertIn("inputs.confirm_product_publication == true", self.text)
        self.assertFalse(any(line.strip() == "schedule:" for line in self.active_lines))

    def test_workflow_has_read_only_github_permission_and_pinned_actions(self):
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", self.text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", self.text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_full_qa_runs_before_live_publication(self):
        preflight = self.text.index("python scripts/github_preflight.py")
        unit = self.text.index("python -m unittest discover -s tests -v")
        regression = self.text.index("python main.py selftest")
        dry_run = self.text.index("github_product_publication_gate.py --dry-run")
        live = self.text.index('github_product_publication_gate.py > "$RUNNER_TEMP/product_publication_result.json"')
        self.assertLess(preflight, unit)
        self.assertLess(unit, regression)
        self.assertLess(regression, dry_run)
        self.assertLess(dry_run, live)

    def test_historical_gates_are_not_reachable(self):
        self.assertNotIn("github_processing_gate.py", self.text)
        self.assertNotIn("github_reconciliation_gate.py", self.text)
        self.assertNotIn("sources.jornal_oficial_7310_gate.json", self.text)
        self.assertNotIn("confirm_processing", self.text)
        self.assertNotIn("confirm_reconciliation", self.text)
        self.assertNotIn("confirm_source_collection", self.text)

    def test_only_sanitized_result_is_uploaded(self):
        self.assertIn("publication-gate-evidence/result.json", self.text)
        self.assertIn("product-publication-gate-${{ github.run_id }}", self.text)
        self.assertNotIn("product_bundle", self.text)
        self.assertNotIn("outputs_id", self.text)
        self.assertNotIn("remote_id", self.text)


if __name__ == "__main__":
    unittest.main()
