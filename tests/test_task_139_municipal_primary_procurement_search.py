from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task139_municipal_primary_procurement_search.v1.json"
S=ROOT/"docs/evidence/TASK_138_WEB_SEARCH_PREFLIGHT_STOP_0.8.0.json"

class TestTask139(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.s=json.loads(S.read_text(encoding="utf-8"))

    def test_task138_stopped_without_open(self):
        self.assertEqual("STOP_SEARCH_PREFLIGHT_EXACT_API_URL_NOT_RETURNED",self.s["result"])
        self.assertEqual(1,self.s["search_invocations"])
        self.assertEqual(0,self.s["open_invocations"])
        self.assertFalse(self.s["exact_pinned_api_url_returned"])
        self.assertFalse(self.s["negative_conclusion_created"])

    def test_one_municipal_search_and_one_conditional_open(self):
        a=self.c["authorization"]
        self.assertEqual(4,a["authorization_unit_index"])
        self.assertEqual(1,a["search_invocations_max"])
        self.assertEqual(1,a["open_invocations_max"])
        self.assertEqual(1,self.c["search"]["search_invocations_max"])
        self.assertEqual(0,self.c["search"]["retry"])
        o=self.c["conditional_open"]
        self.assertTrue(o["open_only_official_municipal_result"])
        self.assertTrue(o["strong_policy_marker_required"])
        self.assertEqual(1,o["open_invocations_max"])
        self.assertEqual(0,o["followup_clicks"])
        self.assertEqual(0,o["retry"])

    def test_primary_can_only_prove_explicit_identifier_binding(self):
        e=self.c["epistemic_semantics"]
        self.assertEqual("CORROBORATED",e["search_snippet_max_status"])
        self.assertTrue(e["opened_primary_page_can_prove_administrative_identifier_if_explicitly_bound_to_object"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])

    def test_design_has_no_remote_effect(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task139_design"].values()))

if __name__=="__main__":
    unittest.main()
