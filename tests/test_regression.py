import unittest
from pathlib import Path
from robo_dados_publicos.qa.regression import RegressionSuite

class TestHistoricalRegression(unittest.TestCase):
    def test_all_historical_regressions(self):
        fx = Path(__file__).parent / "fixtures"
        summary = RegressionSuite(fx).run()
        failed = [r for r in summary["results"] if r["status"] == "FAIL"]
        self.assertEqual([], failed, msg="Falhas:\n" + "\n".join(map(str, failed)))

if __name__ == "__main__":
    unittest.main()
