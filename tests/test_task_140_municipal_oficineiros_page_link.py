from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task140_municipal_oficineiros_page_link.v1.json"
S=ROOT/"docs/evidence/TASK_139_MUNICIPAL_PRIMARY_SEARCH_STOP_0.8.0.json"

class TestTask140(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.s=json.loads(S.read_text(encoding="utf-8"))

    def test_task139_zero_results_created_no_negative(self):
        self.assertEqual("STOP_MUNICIPAL_SEARCH_ZERO_RESULTS_NO_OPEN",self.s["result"])
        self.assertEqual(1,self.s["search_invocations"])
        self.assertEqual(0,self.s["open_invocations"])
        self.assertEqual(0,self.s["search_results"])
        self.assertFalse(self.s["negative_exhaustive_conclusion_created"])

    def test_one_search_open_and_conditional_click(self):
        a=self.c["authorization"]
        self.assertEqual(5,a["authorization_unit_index"])
        self.assertEqual(1,a["search_invocations_max"])
        self.assertEqual(1,a["open_invocations_max"])
        self.assertEqual(1,a["click_invocations_max"])
        e=self.c["execution"]
        self.assertTrue(e["search_exact_title_once"])
        self.assertTrue(e["open_only_exact_known_primary_page"])
        self.assertTrue(e["click_only_explicit_edital_credenciamento_or_processo_link"])
        self.assertEqual(0,e["retry"])
        self.assertEqual(0,e["followup_searches"])

    def test_identity_promotion_is_strict(self):
        e=self.c["epistemic_semantics"]
        self.assertTrue(e["opened_page_can_prove_only_explicit_content"])
        self.assertTrue(e["clicked_official_artifact_can_prove_administrative_identifier_if_explicitly_bound_to_object"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])

    def test_design_has_no_remote_effect(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task140_design"].values()))

if __name__=="__main__":
    unittest.main()
