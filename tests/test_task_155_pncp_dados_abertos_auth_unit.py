from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task155_pncp_dados_abertos_click_auth_unit.v1.json"
E=ROOT/"docs/evidence/TASK_154_PNCP_DIRECT_DOWNLOAD_EXECUTION_0.8.0.json"

class TestTask155(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_prior_stop_and_budget(self):
        self.assertEqual("STOP_DIRECT_DOWNLOAD_URL_NOT_SUCCESSFULLY_VIEWED_PRE_SOURCE",self.e["result"])
        self.assertEqual(7,self.e["authorization_state"]["remaining_units"])
        self.assertFalse(self.e["execution"]["pncp_source_reach_established"])

    def test_unit_four_of_ten(self):
        a=self.c["authorization"]
        self.assertEqual(10,a["owner_authorization_units_granted"])
        self.assertEqual(4,a["authorization_unit_index"])
        self.assertEqual(7,a["remaining_units_before_execution"])
        self.assertEqual(6,a["remaining_units_after_execution"])
        self.assertTrue(a["consume_on_single_click_invocation"])

    def test_exact_visible_official_link(self):
        s=self.c["source"]
        self.assertEqual("turn141163view0",s["previous_web_ref"])
        self.assertEqual(12,s["visible_link_id"])
        self.assertEqual("Dados Abertos",s["visible_link_label"])
        self.assertTrue(s["official_navigation_only"])

    def test_one_click_only(self):
        x=self.c["execution"]
        self.assertEqual(1,x["click_invocations_max"])
        self.assertEqual(0,x["search_queries"])
        self.assertEqual(0,x["web_open_invocations"])
        self.assertEqual(0,x["retry"])
        self.assertEqual(0,x["followup_clicks"])
        self.assertEqual(0,x["parameterized_api_opens"])
        self.assertEqual(0,x["direct_download_invocations"])
        self.assertFalse(x["raw_payload_persistence"])
        self.assertTrue(x["execute_only_after_merge"])

    def test_fail_closed(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["tool_failure_is_source_response"])
        self.assertEqual("CORROBORATED",e["administrative_identifier_candidate_max_status"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])

if __name__=="__main__":
    unittest.main()
