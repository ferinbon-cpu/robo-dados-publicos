from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_public_hosted_baseline_gate.py"
SPEC = importlib.util.spec_from_file_location("public_hosted_baseline_gate", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class PublicHostedBaselineGateTests(unittest.TestCase):
    def test_pinned_baseline_and_post_baseline_closure_pass(self) -> None:
        result = mod.run()
        self.assertEqual("PASS_PUBLIC_HOSTED_BASELINE_CLOSURE", result["status"])
        self.assertEqual(0, result["historical_hosted_secret_blockers"])
        self.assertEqual(2, result["historical_opaque_reviews_resolved_exactly"])
        self.assertEqual(0, result["post_baseline_non_pr_runs"])
        self.assertEqual(0, result["post_baseline_live_drive_or_source_runs"])
        self.assertTrue(result["current_post_baseline_workflows_safe_for_pr"])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["secret_values_exposed"])
        self.assertFalse(result["repository_visibility_change_executed"])

    def test_expected_pdf_allowlist_is_exactly_two_artifacts(self) -> None:
        allowlist = mod._load(mod.ALLOWLIST)
        ids = {str(item["resource_id"]) for item in allowlist["entries"]}
        self.assertEqual(set(mod.EXPECTED_PDFS), ids)

    def test_post_baseline_workflow_set_is_exact(self) -> None:
        incremental = mod._load(mod.INCREMENTAL)
        paths = {row["path"] for row in incremental["post_baseline_workflow_set"]}
        self.assertEqual(mod.EXPECTED_WORKFLOWS, paths)


if __name__ == "__main__":
    unittest.main()
