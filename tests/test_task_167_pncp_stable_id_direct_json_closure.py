import unittest
from robo_dados_publicos.research.task167_pncp_stable_id_direct_json_closure import validate


class TestTask167Closure(unittest.TestCase):
    def test_closure(self):
        out=validate()
        self.assertEqual("VALID",out["status"])
        self.assertEqual("45132495000140-1-000368/2026",out["school_pass_id"])
        self.assertEqual("45132495000140-1-000593/2026",out["course_id"])
        self.assertEqual(2,out["public_detail_successes"])
        self.assertEqual(10,out["integration_503_requests"])
        self.assertEqual(6,out["public_contract_timeout_requests"])
        self.assertFalse(out["contract_identity_proven"])


if __name__=="__main__":
    unittest.main()
