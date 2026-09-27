from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task157_pncp_exact_route_search_auth_unit.v1.json"
E=ROOT/"docs/evidence/TASK_156_PNCP_API_ROUTE_SEARCH_EXECUTION_0.8.0.json"

class TestTask157(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_prior_bounded_result_not_no_match(self):
        self.assertEqual("PASS_OFFICIAL_PNCP_SEARCH_RESULTS_EXACT_TARGET_ROUTE_NOT_SURFACED_IN_BOUNDED_RESULTS",self.e["result"])
        self.assertFalse(self.e["pncp_no_match_created"])
        self.assertFalse(self.e["negative_exhaustive_conclusion_created"])
        self.assertEqual(5,self.e["authorization_state"]["remaining_units"])

    def test_unit_six(self):
        a=self.c["authorization"]
        self.assertEqual(6,a["authorization_unit_index"])
        self.assertEqual(5,a["remaining_units_before_execution"])
        self.assertEqual(4,a["remaining_units_after_execution"])

    def test_one_exact_search_only(self):
        s=self.c["search"]
        self.assertEqual("contratacoes/publicacao",s["query"])
        self.assertTrue(s["exact_phrase_target"])
        self.assertEqual(["pncp.gov.br"],s["domain_restriction"])
        self.assertEqual(1,s["search_invocations_max"])
        self.assertEqual(1,s["query_count_max"])
        self.assertEqual(0,s["result_open_invocations"])
        self.assertEqual(0,s["retry"])
        self.assertEqual(0,s["direct_download_invocations"])

    def test_fail_closed(self):
        e=self.c["epistemic_semantics"]
        self.assertTrue(e["discovery_only"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])

if __name__=="__main__":
    unittest.main()
