from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task156_pncp_api_route_search_auth_unit.v1.json"
E=ROOT/"docs/evidence/TASK_155_PNCP_DADOS_ABERTOS_EXECUTION_0.8.0.json"

class TestTask156(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_prior_success(self):
        self.assertEqual("PASS_OFFICIAL_PNCP_DADOS_ABERTOS_PAGE_REACHED",self.e["result"])
        self.assertTrue(self.e["execution"]["official_open_data_api_description_observed"])
        self.assertTrue(self.e["execution"]["api_access_without_registration_or_login_observed"])
        self.assertEqual(6,self.e["authorization_state"]["remaining_units"])

    def test_unit_five(self):
        a=self.c["authorization"]
        self.assertEqual(5,a["authorization_unit_index"])
        self.assertEqual(6,a["remaining_units_before_execution"])
        self.assertEqual(5,a["remaining_units_after_execution"])
        self.assertTrue(a["consume_on_single_search_invocation"])

    def test_one_official_search_only(self):
        s=self.c["search"]
        self.assertEqual(1,s["search_invocations_max"])
        self.assertEqual(1,s["query_count_max"])
        self.assertEqual(["pncp.gov.br"],s["domain_restriction"])
        self.assertEqual(0,s["result_open_invocations"])
        self.assertEqual(0,s["clicks"])
        self.assertEqual(0,s["retry"])
        self.assertEqual(0,s["direct_download_invocations"])

    def test_fail_closed(self):
        e=self.c["epistemic_semantics"]
        self.assertTrue(e["discovery_only"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])

if __name__=="__main__":
    unittest.main()
