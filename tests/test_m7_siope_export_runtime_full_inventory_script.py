from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "github_siope_export_runtime_full_inventory_gate.py"


class TestM7SiopeRuntimeFullInventoryScript(unittest.TestCase):
    def test_dry_run_executes_no_browser_or_network(self):
        spec = importlib.util.spec_from_file_location("runtime_full_inventory_gate", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        payload, code = module.run_gate(
            "config/source_expansion.siope_export_runtime_route_probe_gate.json",
            dry_run=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "PASS_M7_SIOPE_EXPORT_RUNTIME_FULL_INVENTORY_DRY_RUN")
        self.assertFalse(payload["browser_execution"])
        self.assertFalse(payload["network_called"])
        self.assertFalse(payload["candidate_route_network_sent"])
        self.assertFalse(payload["collection_authorized"])
        self.assertFalse(payload["processing_authorized"])
        self.assertFalse(payload["recurrence_authorized"])
        self.assertFalse(payload["schedule_enabled"])


if __name__ == "__main__":
    unittest.main()
