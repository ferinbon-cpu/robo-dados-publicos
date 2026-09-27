import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_038_loa_jom_numeric_table_visual_validation_gate.py"

class Task038GateEntrypointTests(unittest.TestCase):
    def test_gate_entrypoint_passes(self):
        completed = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS_TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION", completed.stdout)

if __name__ == "__main__":
    unittest.main()
