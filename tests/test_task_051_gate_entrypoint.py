import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_051_f01_eiti_granular_execution_source_selection_gate.py"


class Task051GateEntrypointTests(unittest.TestCase):
    def test_gate_runs_from_repo_root(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS_TASK051_GRANULAR_EXECUTION_SOURCE_SELECTION_REVIEW", completed.stdout)


if __name__ == "__main__":
    unittest.main()
