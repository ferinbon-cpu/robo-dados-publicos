import unittest
from robo_dados_publicos.research.task166_pncp_modality9_closure import validate


class TestTask166Closure(unittest.TestCase):
    def test_closure(self):
        out=validate()
        self.assertEqual("VALID",out["status"])
        self.assertEqual(96,out["records"])
        self.assertEqual(0,out["explicit_eiti_matches"])
        self.assertEqual("45132495000140-1-000368/2026",out["school_pass_id"])
        self.assertEqual("45132495000140-1-000593/2026",out["i00084_id"])
        self.assertEqual(716,out["cumulative_records"])


if __name__=="__main__":
    unittest.main()
