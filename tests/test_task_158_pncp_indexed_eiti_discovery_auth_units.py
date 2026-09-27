from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task158_pncp_indexed_eiti_discovery_auth_units.v1.json"
E=ROOT/"docs/evidence/TASK_157_PNCP_EXACT_ROUTE_SEARCH_EXECUTION_0.8.0.json"

class TestTask158(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_prior_result_and_budget(self):
        self.assertEqual("PASS_OFFICIAL_PNCP_APP_INDEX_SURFACES_FOUND_EXACT_API_ROUTE_NOT_SURFACED",self.e["result"])
        self.assertEqual(4,self.e["authorization_state"]["remaining_units"])
        self.assertFalse(self.e["pncp_no_match_created"])

    def test_units_and_reservation(self):
        a=self.c["authorization"]
        self.assertEqual([7,8,9],a["allowed_search_unit_indices"])
        self.assertEqual(10,a["reserved_open_unit_index"])
        self.assertEqual(4,a["remaining_units_before_execution"])
        self.assertEqual(3,a["max_units_consumed_by_task"])
        self.assertTrue(a["stop_early_on_relevant_candidate"])

    def test_three_searches_max_no_opens(self):
        s=self.c["search"]
        self.assertEqual(["pncp.gov.br"],s["domain_restriction"])
        self.assertEqual(3,len(s["queries"]))
        self.assertEqual(3,s["search_invocations_max"])
        self.assertTrue(s["one_query_per_invocation"])
        self.assertEqual(0,s["result_open_invocations"])
        self.assertEqual(0,s["retry"])
        self.assertEqual(0,s["direct_download_invocations"])

    def test_candidate_rule_and_fail_closed(self):
        r=self.c["candidate_rule"]
        self.assertEqual("45132495000140",r["required_cnpj_token"])
        self.assertEqual("CORROBORATED",r["candidate_max_status"])
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertTrue(e["unit_10_must_remain_unconsumed"])

if __name__=="__main__":
    unittest.main()
