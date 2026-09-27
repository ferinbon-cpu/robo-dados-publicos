from copy import deepcopy
from pathlib import Path
import unittest
from robo_dados_publicos.research.task126_primary_procurement_surface_selection import Task126Stop,load_task126_contract,validate_task126_contract

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task126_primary_procurement_surface_selection.v1.json"

class TestTask126(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_task126_contract(P)

    def test_primary_jom_is_only_selected_candidate(self):
        selected=[x for x in self.c["candidates"] if x["selected_for_next_read"]]
        self.assertEqual(1,len(selected))
        self.assertEqual("JOM_7126_2025_EITI_CREDENCIAMENTO",selected[0]["id"])
        self.assertEqual("MUNICIPAL_PRIMARY_NORMATIVE_PROCUREMENT",selected[0]["source_role"])

    def test_next_read_is_one_exact_get_no_retry(self):
        s=self.c["selection"]
        self.assertEqual(1,s["max_source_gets"])
        self.assertFalse(s["retry"])
        self.assertEqual(0,s["redirects_max"])

    def test_no_weak_identity_promotion(self):
        self.assertTrue(all(v is False for v in self.c["guards"].values()))

    def test_tcesp_remains_secondary(self):
        t=[x for x in self.c["candidates"] if x["id"]=="TCESP_HTML_EXPENSE_DETAIL"][0]
        self.assertEqual("SECONDARY_AGGREGATOR",t["source_role"])
        self.assertTrue(t["municipal_primary_verification_required"])

    def test_widening_live_scope_fails(self):
        x=deepcopy(self.c); x["selection"]["max_source_gets"]=2
        with self.assertRaisesRegex(Task126Stop,"GET_BUDGET"):
            validate_task126_contract(x)
        x=deepcopy(self.c); x["future_source_read_authorized"]=True
        with self.assertRaisesRegex(Task126Stop,"FUTURE_SOURCE"):
            validate_task126_contract(x)

if __name__=="__main__":
    unittest.main()
