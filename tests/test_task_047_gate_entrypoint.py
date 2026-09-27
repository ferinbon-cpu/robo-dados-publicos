from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_047_f01_ppa_scoped_silver_v2_persistence_gate.py"


class Task047GateEntrypointTests(unittest.TestCase):
    def test_entrypoint_passes(self):
        completed = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS_TASK047_PPA_SCOPED_SILVER_V2_PERSISTENCE_REVIEW", completed.stdout)


if __name__ == "__main__":
    unittest.main()
