from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "scripts" / "github_task_010j_siope_cml_codec_gate.py"
SPEC = importlib.util.spec_from_file_location("task_010j_gate", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)


class Task010JGateTests(unittest.TestCase):
    def test_current_tree_passes(self):
        self.assertEqual(gate.main(), 0)

    def test_network_subprocess_ctypes_and_execution_imports_fail(self):
        for forbidden in ("requests", "socket", "subprocess", "ctypes", "cffi"):
            with self.subTest(forbidden=forbidden), tempfile.TemporaryDirectory() as directory:
                surface = Path(directory) / "fake.py"
                surface.write_text(f"import {forbidden}\n", encoding="utf-8")
                with mock.patch.object(gate, "SURFACES", (surface,)), self.assertRaises(SystemExit):
                    gate.main()

    def test_execution_call_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            surface = Path(directory) / "fake.py"
            surface.write_text("exec('x')\n", encoding="utf-8")
            with mock.patch.object(gate, "SURFACES", (surface,)), self.assertRaises(SystemExit):
                gate.main()

    def test_semantic_promotion_fails(self):
        promoted = dict(gate.EXPECTED_STATE, S1_NUM_POPU="PROVEN")
        with mock.patch.dict(gate.EXPECTED_STATE, promoted, clear=True):
            with self.assertRaises(SystemExit):
                gate.main()
