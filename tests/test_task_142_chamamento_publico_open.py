from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task142_chamamento_publico_open.v1.json"
S=ROOT/"docs/evidence/TASK_141_INDEXED_LICITACOES_ROUTE_SEARCH_STOP_0.8.0.json"

class TestTask142(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.s=json.loads(S.read_text(encoding="utf-8"))

    def test_task141_did_not_open_irrelevant_result(self):
        self.assertEqual("STOP_INDEXED_LICITACOES_NO_RELEVANT_ROUTE_RESULT",self.s["result"])
        self.assertEqual(1,self.s["search_invocations"])
        self.assertEqual(0,self.s["open_invocations"])
        self.assertFalse(self.s["returned_result_under_licitacoes_route"])
        self.assertFalse(self.s["negative_exhaustive_conclusion_created"])

    def test_exactly_one_chamamento_click(self):
        a=self.c["authorization"]
        self.assertEqual(7,a["authorization_unit_index"])
        self.assertEqual(1,a["click_invocations_max"])
        e=self.c["execution"]
        self.assertTrue(e["click_known_chamamento_link_once"])
        self.assertEqual(0,e["search_invocations"])
        self.assertEqual(0,e["additional_opens"])
        self.assertEqual(0,e["additional_clicks"])
        self.assertEqual(0,e["retry"])

    def test_no_negative_or_identity_promotion(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])

    def test_design_has_no_remote_effect(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task142_design"].values()))

if __name__=="__main__":
    unittest.main()
