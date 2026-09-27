import unittest
from robo_dados_publicos.research.task275_linked_contract_http400_diagnostic import *
class T(unittest.TestCase):
 def setUp(self):self.c=load_config();self.e=load_evidence()
 def test_diag_allow(self):
  x={"status":400,"error":"Bad Request","message":"x"*700,"trace":"secret","niFornecedor":"x","other":"no"}
  d=sanitize_diagnostic(x,self.c);self.assertEqual(d["status"],400);self.assertEqual(len(d["message"]),500);self.assertNotIn("trace",d);self.assertNotIn("niFornecedor",d);self.assertNotIn("other",d)
 def test_http400(self):
  def g(url,**kw):return {"requested_url":url,"http_code":400,"content_type":"application/json","url_effective":url,"curl_exit_code":0,"curl_error":None,"body_bytes":10,"body_sha256":"a"*64,"json_error":None,"json_shape":"OBJECT","row_count":None,"response_keys":["error","message","status"],"purchase_identity_valid":None,"contracts":[],"contracts_sha256":None,"diagnostic_scalars":{"status":400,"message":"bad"},"diagnostic_sha256":"b"*64,"remote_get_count":1,"raw_body_persisted":False}
  r=execute(self.c,self.e,getter=g,offline_test_mode=True);self.assertEqual(r["outcome"],"LINKED_CONTRACT_ROUTE_HTTP400_SAFE_DIAGNOSTIC_CAPTURED");self.assertFalse(r["absence_inference_allowed"])
 def test_no_auth(self):
  r=execute(self.c,self.e,authorization=None,expected_implementation_sha="0"*40);self.assertEqual(r["source_get_count"],0)
if __name__=="__main__":unittest.main()
