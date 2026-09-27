import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_050_f01_loa_scoped_silver_v2_persistence_gate.py"


class Task050GateEntrypointTests(unittest.TestCase):
    def test_gate_runs_from_repo_root(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS_TASK050_LOA_SCOPED_SILVER_V2_PERSISTENCE_REVIEW", completed.stdout)


if __name__ == "__main__":
    unittest.main()
