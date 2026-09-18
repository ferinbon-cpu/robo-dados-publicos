import unittest
from robo_dados_publicos.research.task267_pncp_items_8of8_canonization import validate,load_evidence
class T(unittest.TestCase):
 def test_all(self):self.assertEqual(validate()["items"],40)
 def test_653_open_diagnostic(self):
  e=load_evidence();m=next(x for x in e["controls"] if x["control"].endswith("000653/2026"));self.assertFalse(m["matches_detail_estimated_value"]);self.assertEqual(m["difference"],-16921.62)
 def test_tokens_exhausted(self):self.assertEqual(load_evidence()["authorization"]["tokens_remaining"],0)
if __name__=="__main__":unittest.main()
