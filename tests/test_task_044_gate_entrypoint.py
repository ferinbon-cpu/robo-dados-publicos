from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_044_f01_next_evidence_readonly_gate_design.py"


class Task044GateEntrypointTests(unittest.TestCase):
    def test_gate_entrypoint_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("TASK_044_GATE_PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
