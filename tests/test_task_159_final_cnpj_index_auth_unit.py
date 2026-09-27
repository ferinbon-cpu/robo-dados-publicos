from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "config/task159_final_cnpj_index_auth_unit.v1.json"
E = ROOT / "docs/evidence/TASK_158_EXECUTION_0.8.0.json"

class TestTask159(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))
        cls.e = json.loads(E.read_text(encoding="utf-8"))

    def test_prior_batch_state(self):
        self.assertEqual(3, self.e["searches"])
        self.assertEqual([7,8,9], self.e["units_consumed"])
        self.assertFalse(self.e["relevant_candidate_found"])
        self.assertEqual(1, self.e["remaining_units"])

    def test_final_unit(self):
        a = self.c["authorization"]
        self.assertEqual(10, a["authorization_unit_index"])
        self.assertEqual(1, a["remaining_units_before_execution"])
        self.assertEqual(0, a["remaining_units_after_execution"])

    def test_one_exact_search_only(self):
        s = self.c["search"]
        self.assertEqual("45132495000140", s["query"])
        self.assertEqual("pncp.gov.br", s["domain"])
        self.assertEqual(1, s["search_invocations_max"])
        self.assertEqual(0, s["result_open_invocations"])
        self.assertEqual(0, s["retry"])

    def test_fail_closed(self):
        e = self.c["semantics"]
        self.assertTrue(e["bounded_discovery_only"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])

if __name__ == "__main__":
    unittest.main()
