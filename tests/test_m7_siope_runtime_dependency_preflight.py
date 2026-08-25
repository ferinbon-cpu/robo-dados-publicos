from __future__ import annotations

from pathlib import Path
import unittest

from scripts.github_siope_runtime_dependency_preflight import run_preflight


ROOT = Path(__file__).resolve().parents[1]


class TestM7SiopeRuntimeDependencyPreflight(unittest.TestCase):
    def test_websocket_client_is_pinned_in_both_manifests(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("websocket-client==1.9.0", requirements)
        self.assertIn("websocket-client==1.9.0", pyproject)

    def test_preflight_passes_with_installed_pinned_dependency(self):
        payload, code = run_preflight()
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS_M7_SIOPE_RUNTIME_DEPENDENCY_PREFLIGHT")
        self.assertEqual(payload["failed_checks"], [])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["collection_authorized"])
        self.assertFalse(payload["processing_authorized"])
        self.assertEqual(payload["remote_writes"], "NONE")

    def test_runtime_workflow_runs_dependency_preflight_before_live_gate(self):
        workflow = (ROOT / ".github" / "workflows" / "siope-public-get-runtime-route-diagnostics-gate.yml").read_text(encoding="utf-8")
        dependency_step = "python scripts/github_siope_runtime_dependency_preflight.py"
        dry_run_step = "python scripts/github_siope_public_get_runtime_route_diagnostics_gate.py --dry-run"
        self.assertIn(dependency_step, workflow)
        self.assertLess(workflow.index(dependency_step), workflow.index(dry_run_step))


if __name__ == "__main__":
    unittest.main()
