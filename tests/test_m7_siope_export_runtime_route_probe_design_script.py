from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_siope_export_runtime_route_probe_design_gate.py"

spec = importlib.util.spec_from_file_location("runtime_probe_design_gate", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class TestM7SiopeRuntimeRouteProbeDesignScript(unittest.TestCase):
    def test_run_gate_passes_without_browser_or_network(self):
        payload, code = module.run_gate("config/source_expansion.siope_export_runtime_route_probe_design.json")
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_GATE")
        self.assertFalse(payload["browser_execution"])
        self.assertFalse(payload["click_executed"])
        self.assertFalse(payload["candidate_route_network_sent"])
        self.assertFalse(payload["artifact_downloaded"])
        self.assertEqual(payload["remote_writes"], "NONE")


if __name__ == "__main__":
    unittest.main()
