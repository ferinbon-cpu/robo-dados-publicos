from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task138_pncp_web_search_preflight.v1.json"
S=ROOT/"docs/evidence/TASK_137_WEB_EXACT_URL_SAFE_OPEN_STOP_0.8.0.json"

class TestTask138(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(C.read_text(encoding="utf-8"))
        cls.s=json.loads(S.read_text(encoding="utf-8"))

    def test_task137_stop_is_pre_source(self):
        self.assertEqual("STOP_PRE_SOURCE_WEB_SAFE_OPEN_REJECTED",self.s["result"])
        self.assertEqual(1,self.s["web_open_invocations"])
        self.assertFalse(self.s["pncp_content_returned"])
        self.assertFalse(self.s["source_data_observed"])
        self.assertFalse(self.s["negative_conclusion_created"])
        self.assertFalse(self.s["retry_performed"])

    def test_search_preflight_is_one_search_then_conditional_one_open(self):
        a=self.c["authorization"]
        self.assertEqual(3,a["authorization_unit_index"])
        self.assertEqual(1,a["search_invocations_max"])
        self.assertEqual(1,a["open_invocations_max"])
        self.assertEqual(1,self.c["search"]["search_invocations_max"])
        self.assertEqual(0,self.c["search"]["retry"])
        o=self.c["conditional_open"]
        self.assertTrue(o["allowed_only_if_exact_api_url_returned_by_search"])
        self.assertEqual(1,o["open_invocations_max"])
        self.assertEqual(0,o["followup_clicks"])
        self.assertEqual(0,o["followup_searches"])
        self.assertEqual(0,o["retry"])

    def test_negative_and_identity_promotion_stay_blocked(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertTrue(e["primary_municipal_verification_required"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])

    def test_design_has_no_remote_effect(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task138_design"].values()))

if __name__=="__main__":
    unittest.main()
