from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_160_PNCP_AUTHORIZATION_BATCH_CLOSURE_0.8.0.json"

class TestTask160(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads(E.read_text(encoding="utf-8"))

    def test_all_ten_units_are_accounted_for(self):
        self.assertEqual(10,self.e["units_granted"])
        self.assertEqual(10,self.e["units_consumed"])
        self.assertEqual(0,self.e["units_remaining"])
        self.assertEqual(list(range(1,11)),[x["unit"] for x in self.e["ledger"]])

    def test_transport_and_navigation_successes_are_preserved(self):
        by_unit={x["unit"]:x for x in self.e["ledger"]}
        self.assertEqual("PNCP_ORIGIN_REACHED",by_unit[1]["outcome"])
        self.assertEqual("OFFICIAL_DADOS_ABERTOS_REACHED",by_unit[4]["outcome"])

    def test_no_negative_or_identity_promotion(self):
        s=self.e["epistemic_state"]
        self.assertFalse(s["pncp_no_match_created"])
        self.assertFalse(s["negative_exhaustive_conclusion_created"])
        self.assertFalse(s["administrative_identifier_candidate_created"])
        self.assertFalse(s["financial_identity_created"])
        self.assertFalse(s["transaction_identity_created"])
        self.assertFalse(s["supplier_linkage_created"])

    def test_fresh_authorization_is_required(self):
        self.assertEqual(
            "FRESH_EXPLICIT_OWNER_AUTHORIZATION_REQUIRED_BEFORE_ANY_FURTHER_LIVE_SOURCE_OPERATION",
            self.e["next_boundary"],
        )

if __name__=="__main__":
    unittest.main()
