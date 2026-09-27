import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_039_loa_scoped_silver_candidate_review_gate.py"

class Task039GateEntrypointTests(unittest.TestCase):
    def test_gate_entrypoint_passes(self):
        completed = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS_TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW", completed.stdout)
        self.assertIn("SEPARATE_AUTH_REQUIRED", completed.stdout)
        self.assertIn("TASK039_F01_STATUS=NOT_SILVER", completed.stdout)

if __name__ == "__main__":
    unittest.main()
