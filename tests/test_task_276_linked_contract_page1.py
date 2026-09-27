import unittest
from robo_dados_publicos.research.task276_linked_contract_page1 import *
class T(unittest.TestCase):
 def setUp(self):self.c=load_config();self.e=load_evidence()
 def test_complete_zero(self):
  m={"http_code":200,"json_shape":"OBJECT","page_contract_valid":True,"page_meta":{"totalRegistros":0,"totalPaginas":0,"numeroPagina":1,"paginasRestantes":0,"empty":True},"contracts":[]}
  self.assertEqual(classify(m),"LINKED_CONTRACT_PAGE1_COMPLETE_ZERO_ROWS")
 def test_complete_rows(self):
  m={"http_code":200,"json_shape":"OBJECT","page_contract_valid":True,"page_meta":{"totalRegistros":1,"totalPaginas":1,"numeroPagina":1,"paginasRestantes":0,"empty":False},"contracts":[{"numeroControlePNCPCompra":self.c["target"]["purchase_control"]}]}
  self.assertEqual(classify(m),"LINKED_CONTRACT_PAGE1_COMPLETE_WITH_ROWS")
 def test_partial(self):
  m={"http_code":200,"json_shape":"OBJECT","page_contract_valid":True,"page_meta":{"totalRegistros":80,"totalPaginas":2,"numeroPagina":1,"paginasRestantes":1,"empty":False},"contracts":[{}]*50}
  self.assertEqual(classify(m),"LINKED_CONTRACT_PAGE1_PARTIAL_MORE_PAGES")
 def test_privacy(self):
  row={"numeroControlePNCPCompra":self.c["target"]["purchase_control"],"numeroContratoEmpenho":"1","niFornecedor":"123","nomeRazaoSocialFornecedor":"X","usuarioNome":"Y"}
  out=sanitize_contract(row,self.c);self.assertNotIn("niFornecedor",out);self.assertNotIn("nomeRazaoSocialFornecedor",out);self.assertNotIn("usuarioNome",out)
 def test_no_auth(self):
  r=execute(self.c,self.e,authorization=None,expected_implementation_sha="0"*40);self.assertEqual(r["source_get_count"],0)
if __name__=="__main__":unittest.main()
