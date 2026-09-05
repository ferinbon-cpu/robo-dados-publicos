from copy import deepcopy
from pathlib import Path
import unittest
from robo_dados_publicos.research.task124_tcesp_expense_scan import Task124Stop,load_task124_contract,validate_task124_contract
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task124_tcesp_limeira_2026_expense_scan.v1.json"
class TestTask124(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.c=load_task124_contract(P)
 def test_exact_one_get(self): self.assertEqual(1,self.c["network"]["get_requests_max"])
 def test_secondary_role(self): self.assertEqual("SECONDARY_AGGREGATOR",self.c["source"]["source_role"])
 def test_fuzzy_forbidden(self): self.assertFalse(self.c["scan"]["fuzzy_matching"])
 def test_network_widening_fails(self):
  for k in ("retries","pagination","redirect_host_change_allowed","other_hosts_allowed"):
   x=deepcopy(self.c); x["network"][k]=True
   with self.assertRaises(Task124Stop): validate_task124_contract(x)
 def test_promotion_fails(self):
  x=deepcopy(self.c); x["semantics"]["automatic_financial_identity"]=True
  with self.assertRaises(Task124Stop): validate_task124_contract(x)
 def test_persistence_fails(self):
  x=deepcopy(self.c); x["persistence"]["raw_csv_commit"]=True
  with self.assertRaises(Task124Stop): validate_task124_contract(x)
if __name__=="__main__": unittest.main()
