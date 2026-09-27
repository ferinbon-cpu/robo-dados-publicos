from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task143_indexed_chamamento_route_search.v1.json"
S=ROOT/"docs/evidence/TASK_142_CHAMAMENTO_PUBLICO_OPEN_STOP_0.8.0.json"

class TestTask143(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.s=json.loads(S.read_text(encoding="utf-8"))

    def test_task142_is_403_without_content_or_retry(self):
        self.assertEqual("STOP_CHAMAMENTO_PUBLICO_HTTP_403_NO_CONTENT",self.s["result"])
        self.assertEqual(1,self.s["click_invocations"])
        self.assertEqual(403,self.s["http_status"])
        self.assertFalse(self.s["content_returned"])
        self.assertFalse(self.s["retry_performed"])
        self.assertFalse(self.s["negative_exhaustive_conclusion_created"])

    def test_one_index_search_and_conditional_open(self):
        a=self.c["authorization"]
        self.assertEqual(8,a["authorization_unit_index"])
        self.assertEqual(1,a["search_invocations_max"])
        self.assertEqual(1,a["open_invocations_max"])
        self.assertEqual(1,self.c["search"]["search_invocations_max"])
        self.assertEqual(0,self.c["search"]["retry"])
        o=self.c["conditional_open"]
        self.assertTrue(o["only_result_under_chamamento_route"])
        self.assertTrue(o["strong_eiti_marker_required"])
        self.assertEqual(1,o["open_invocations_max"])
        self.assertEqual(0,o["followup_clicks"])

    def test_no_negative_or_financial_promotion(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertTrue(e["opened_primary_page_can_prove_identifier_if_explicit"])

    def test_design_has_no_remote_effect(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task143_design"].values()))

if __name__=="__main__":
    unittest.main()
