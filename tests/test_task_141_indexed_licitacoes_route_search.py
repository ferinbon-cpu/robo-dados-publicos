from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task141_indexed_licitacoes_route_search.v1.json"
R=ROOT/"docs/evidence/TASK_140_MUNICIPAL_OFICINEIROS_PAGE_LINK_RESULT_0.8.0.json"

class TestTask141(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.r=json.loads(R.read_text(encoding="utf-8"))

    def test_task140_primary_page_confirmed_object_but_no_identifier(self):
        self.assertEqual("PASS_PRIMARY_PAGE_OBJECT_CONFIRMED_NO_IDENTIFIER_LINK_403",self.r["result"])
        self.assertTrue(self.r["epistemic_state"]["policy_procurement_object_primary_confirmed"])
        self.assertFalse(self.r["epistemic_state"]["administrative_identifier_found"])
        self.assertEqual(403,self.r["execution"]["click_http_status"])
        self.assertEqual(0,self.r["execution"]["retry"])

    def test_one_index_search_and_one_conditional_open(self):
        a=self.c["authorization"]
        self.assertEqual(6,a["authorization_unit_index"])
        self.assertEqual(1,a["search_invocations_max"])
        self.assertEqual(1,a["open_invocations_max"])
        self.assertEqual(1,self.c["search"]["search_invocations_max"])
        self.assertEqual(0,self.c["search"]["retry"])
        o=self.c["conditional_open"]
        self.assertTrue(o["only_result_under_official_licitacoes_route"])
        self.assertTrue(o["strong_eiti_marker_required"])
        self.assertEqual(1,o["open_invocations_max"])
        self.assertEqual(0,o["followup_clicks"])

    def test_no_negative_or_financial_promotion(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertTrue(e["opened_primary_procurement_page_can_prove_identifier_if_explicit"])

    def test_design_has_no_remote_effect(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task141_design"].values()))

if __name__=="__main__":
    unittest.main()
