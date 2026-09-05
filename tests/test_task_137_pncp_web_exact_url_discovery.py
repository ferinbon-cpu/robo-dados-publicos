from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task137_pncp_web_exact_url_discovery.v1.json"

class TestTask137(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(P.read_text(encoding="utf-8"))

    def test_single_exact_web_open_only(self):
        self.assertEqual("OPEN_EXACT_URL",self.c["web_transport"]["operation"])
        self.assertEqual(1,self.c["web_transport"]["open_invocations_max"])
        self.assertEqual(0,self.c["web_transport"]["search_queries"])
        self.assertEqual(0,self.c["web_transport"]["followup_clicks"])
        self.assertEqual(0,self.c["web_transport"]["followup_opens"])
        self.assertEqual(0,self.c["web_transport"]["retry"])

    def test_second_authorization_unit_is_bounded(self):
        a=self.c["authorization"]
        self.assertEqual(10,a["owner_authorization_units_granted"])
        self.assertEqual(2,a["authorization_unit_index"])
        self.assertEqual(1,a["max_web_open_invocations"])
        self.assertTrue(a["does_not_broaden_task133"])

    def test_web_transport_cannot_prove_no_match(self):
        e=self.c["epistemic_semantics"]
        self.assertTrue(e["candidate_discovery_allowed"])
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertTrue(e["primary_municipal_verification_required"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])

    def test_design_has_no_remote_effect(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task137_design"].values()))
        self.assertFalse(self.c["followup_endpoints_authorized"])

if __name__=="__main__":
    unittest.main()
