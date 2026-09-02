from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/github_task_028_loa_official_equivalence_probe_design_gate.py"


class TestTask028GateEntrypoint(unittest.TestCase):
    def test_offline_gate_passes_inside_existing_ci_discovery(self):
        result = subprocess.run(
            [sys.executable, str(GATE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(
            "PASS_TASK_028_LOA_OFFICIAL_EQUIVALENCE_PROBE_DESIGN_OFFLINE",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
