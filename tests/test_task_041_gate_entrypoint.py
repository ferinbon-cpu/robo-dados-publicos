from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_041_f01_jom_native_ppa_ldo_readiness_gate.py"


class Task041GateEntrypointTest(unittest.TestCase):
    def test_gate_entrypoint_passes(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(
            "PASS_TASK041_JOM_NATIVE_PPA_LDO_SCOPED_SILVER_CANDIDATES_READY_NO_WRITE",
            completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
