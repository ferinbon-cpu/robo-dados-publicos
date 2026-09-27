import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_037_loa_jom_targeted_ocr_review_gate.py"


class Task037GateEntrypointTests(unittest.TestCase):
    def test_gate_entrypoint_passes(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS_TASK_037_LOA_JOM_TARGETED_OCR_REVIEW", completed.stdout)
        self.assertIn("TASK037_NUMERIC_TABLE_REVIEW_PAGES=480,481", completed.stdout)
        self.assertIn("TASK037_F01_STATUS=NOT_SILVER", completed.stdout)


if __name__ == "__main__":
    unittest.main()
