from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task142_municipal_chamamento_publico_surface.v1.json"
S=ROOT/"docs/evidence/TASK_141_INDEXED_LICITACOES_ROUTE_SEARCH_STOP_0.8.0.json"

class TestTask142(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.s=json.loads(S.read_text(encoding="utf-8"))

    def test_task141_stop_is_non_negative(self):
        self.assertEqual("STOP_INDEXED_LICITACOES_SEARCH_NO_QUALIFIED_ROUTE_RESULT",self.s["result"])
        self.assertEqual(1,self.s["search_invocations"])
        self.assertEqual(0,self.s["open_invocations"])
        self.assertFalse(self.s["negative_exhaustive_conclusion_created"])

    def test_unit7_one_click_only(self):
        a=self.c["authorization"]
        self.assertEqual(7,a["authorization_unit_index"])
        self.assertEqual(1,a["click_invocations_max"])
        x=self.c["execution"]
        self.assertTrue(x["click_known_link_once"])
        self.assertEqual(0,x["search_invocations"])
        self.assertEqual(0,x["additional_opens"])
        self.assertEqual(0,x["additional_clicks"])
        self.assertEqual(0,x["retry"])

    def test_known_chamamento_link_is_pinned(self):
        s=self.c["source_referent"]
        self.assertEqual("turn649568view0",s["opened_primary_page_ref"])
        self.assertEqual(92,s["link_id"])
        self.assertEqual("Chamamento Público",s["link_label"])

    def test_no_inference_or_promotion(self):
        e=self.c["epistemic_semantics"]
        self.assertTrue(e["surface_name_does_not_prove_eiti_linkage"])
        self.assertTrue(e["returned_page_can_yield_candidate_only_if_explicit_eiti_or_oficineiros_credenciamento_binding"])
        self.assertTrue(e["stable_identifier_candidate_requires_explicit_binding"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])
        self.assertFalse(self.c["followup_procurement_or_financial_action_authorized"])

if __name__=="__main__":
    unittest.main()
