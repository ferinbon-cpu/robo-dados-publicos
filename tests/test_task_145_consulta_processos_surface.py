from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task145_consulta_processos_surface.v1.json"
S=ROOT/"docs/evidence/TASK_144_TRANSPARENCY_EITI_PROCUREMENT_SEARCH_STOP_0.8.0.json"

class TestTask145(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.s=json.loads(S.read_text(encoding="utf-8"))

    def test_task144_stop_is_bounded_and_non_negative(self):
        self.assertEqual("STOP_TRANSPARENCY_SEARCH_ZERO_RESULTS_NO_OPEN",self.s["result"])
        self.assertEqual(1,self.s["search_invocations"])
        self.assertEqual(0,self.s["open_invocations"])
        self.assertFalse(self.s["negative_exhaustive_conclusion_created"])

    def test_final_unit_is_one_click_only(self):
        a=self.c["authorization"]
        self.assertEqual(10,a["authorization_unit_index"])
        self.assertEqual(10,a["owner_authorization_units_granted"])
        self.assertEqual(1,a["click_invocations_max"])
        self.assertTrue(a["authorization_exhausted_after_execution"])
        x=self.c["execution"]
        self.assertTrue(x["click_known_process_consultation_link_once"])
        self.assertEqual(0,x["search_invocations"])
        self.assertEqual(0,x["form_submissions"])
        self.assertEqual(0,x["additional_opens"])
        self.assertEqual(0,x["additional_clicks"])
        self.assertEqual(0,x["retry"])

    def test_process_surface_cannot_promote_identity_by_existence(self):
        e=self.c["epistemic_semantics"]
        self.assertTrue(e["surface_existence_does_not_prove_eiti_identifier"])
        self.assertTrue(e["returned_page_can_prove_identifier_only_if_explicitly_bound_to_eiti_object"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])
        self.assertFalse(self.c["followup_process_query_or_form_submission_authorized"])

    def test_design_has_no_remote_effects(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task145_design"].values()))

if __name__=="__main__":
    unittest.main()
