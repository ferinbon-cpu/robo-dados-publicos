from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Task249GateIntegrationTests(unittest.TestCase):
    def test_gate_is_part_of_full_unit_suite(self) -> None:
        path = ROOT / "scripts/github_task_249_jom_bounded_pdf_acquisition_gate.py"
        spec = importlib.util.spec_from_file_location("task249_gate", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.main(), 0)


if __name__ == "__main__":
    unittest.main()
