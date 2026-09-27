import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestBI005GateEntrypoint(unittest.TestCase):
    def test_gate_entrypoint_passes_offline(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/github_bi_005_generalized_serving_executor_gate.py"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn(
            "PASS_BI_005_FINAL_SERVING_INTEGRATION_OFFLINE", result.stdout
        )


if __name__ == "__main__":
    unittest.main()
