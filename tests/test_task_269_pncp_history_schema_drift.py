import unittest
from robo_dados_publicos.research.task269_pncp_history_schema_drift import *
class T(unittest.TestCase):
 def test_validate(self): self.assertEqual(validate()["status"],"PASS_TASK269_HISTORY_SCHEMA_DRIFT_CANONIZATION")
 def test_privacy(self):
  c=load(CFG);self.assertNotIn("usuarioNome",c["proposed_safe_v26_projection"])
 def test_only_intersection(self):
  e=load(EV);self.assertEqual(e["schema_comparison"]["intersection"],["justificativa"])
  self.assertFalse(e["observation"]["selected_history_actual_semantics_sufficient"])
if __name__=="__main__":unittest.main()
