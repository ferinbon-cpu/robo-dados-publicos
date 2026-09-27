from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/github_task_247_jom_rolling_discovery_gate.py"


def load_gate_module():
    spec = importlib.util.spec_from_file_location("task247_gate", GATE)
    if spec is None or spec.loader is None:
        raise RuntimeError("TASK247_GATE_IMPORT_SPEC")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTask247GateIntegration(unittest.TestCase):
    def test_task247_gate_runs_inside_full_unit_suite(self):
        result = load_gate_module().run()
        self.assertEqual(result["status"], "PASS_TASK247_ROLLING_DISCOVERY_CARRIER_OFFLINE")
        self.assertEqual(result["baseline_total"], 99)
        self.assertEqual(result["delta_window"], ["2026-09-09", "2026-09-16"])
        self.assertEqual(result["document_downloads"], 0)
        self.assertFalse(result["drive_write"])
        self.assertFalse(result["serving_write"])
        self.assertFalse(result["publication"])
        self.assertFalse(result["schedule"])
        self.assertFalse(result["recurrence"])
        self.assertTrue(result["live_authorization_required"])


if __name__ == "__main__":
    unittest.main()
