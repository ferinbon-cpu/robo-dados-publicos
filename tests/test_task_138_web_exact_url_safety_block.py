from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_138_WEB_EXACT_URL_SAFETY_BLOCK_0.8.0.json"

class TestTask138(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_stop_is_pre_source(self):
        self.assertEqual("STOP_WEB_SAFE_OPEN_PRE_SOURCE_NO_PNCP_DATA",self.e["result"])
        x=self.e["execution"]
        self.assertEqual(1,x["web_open_invocations"])
        self.assertEqual(0,x["search_queries"])
        self.assertFalse(x["source_read_proven"])
        self.assertFalse(x["pncp_data_observed"])
        self.assertEqual(0,x["retry"])

    def test_unit2_consumed_only(self):
        a=self.e["authorization_state"]
        self.assertTrue(a["authorization_unit_2_consumed"])
        self.assertEqual(8,a["authorization_units_remaining"])

    def test_no_data_conclusion_or_identity(self):
        s=self.e["epistemic_state"]
        self.assertFalse(s["candidate_found"])
        self.assertFalse(s["no_match_conclusion_created"])
        self.assertFalse(s["negative_exhaustive_conclusion_created"])
        self.assertFalse(s["financial_identity_created"])
        self.assertFalse(s["transaction_identity_created"])

if __name__=="__main__":
    unittest.main()
