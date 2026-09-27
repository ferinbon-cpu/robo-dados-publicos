from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_048_f01_loa_scoped_silver_v2_candidate_gate.py"


class Task048GateEntrypointTests(unittest.TestCase):
    def test_gate_runs_from_repo_root(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS_TASK048_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW", completed.stdout)


if __name__ == "__main__":
    unittest.main()
