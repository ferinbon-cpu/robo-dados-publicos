import unittest
from robo_dados_publicos.research.task277_linked_contract_http404_diagnostic import *
class T(unittest.TestCase):
 def setUp(self):self.c=load_config();self.e=load_evidence()
 def test_diag_safe(self):
  d=sanitize_diagnostic({"status":404,"message":"x"*700,"path":"/a","trace":"secret","niFornecedor":"x","foo":"bar"},self.c)
  self.assertEqual(d["status"],404);self.assertEqual(len(d["message"]),500);self.assertNotIn("trace",d);self.assertNotIn("niFornecedor",d);self.assertNotIn("foo",d)
 def test_404(self):
  self.assertEqual(classify(404,"OBJECT",False,[],{}),"LINKED_CONTRACT_PAGE1_HTTP404_SAFE_DIAGNOSTIC_CAPTURED")
 def test_zero(self):
  self.assertEqual(classify(200,"OBJECT",True,[],{"totalRegistros":0,"totalPaginas":0,"paginasRestantes":0}),"LINKED_CONTRACT_PAGE1_COMPLETE_ZERO_ROWS")
 def test_no_auth(self):
  r=execute(self.c,self.e,authorization=None,expected_implementation_sha="0"*40);self.assertEqual(r["source_get_count"],0)
if __name__=="__main__":unittest.main()
