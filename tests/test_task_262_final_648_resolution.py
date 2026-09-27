import unittest
from pathlib import Path
from robo_dados_publicos.research.task262_final_648_resolution import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 def setUp(self):self.c=load_config(ROOT/"config/task262_final_648_resolution.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_262_TASK261_TRANSIENT_JDBC_CANONICAL_0.8.0.json")
 def test_exact(self):
  t=self.c["target"]
  def g(url,**k):return {"url_effective":url,"http_code":200,"curl_exit_code":0,"curl_error":None,"content_type":"application/json","body_bytes":100,"body_sha256":"a"*64,"json_error":None,"top_level_keys":["numeroControlePNCP"],"selected":{"numeroControlePNCP":t["control"]},"diagnostic_scalars":{}}
  r=execute(self.c,self.e,getter=g,offline_test_mode=True);self.assertEqual(r["outcome"],"EXACT_CONTROL_RESOLVED")
 def test_unresolved(self):
  def g(url,**k):return {"url_effective":url,"http_code":500,"curl_exit_code":0,"curl_error":None,"content_type":"application/json","body_bytes":341,"body_sha256":"b"*64,"json_error":None,"top_level_keys":["status"],"selected":{},"diagnostic_scalars":{"status":500}}
  r=execute(self.c,self.e,getter=g,offline_test_mode=True);self.assertEqual(r["outcome"],"FINAL_CONTROL_STILL_UNRESOLVED");self.assertFalse(r["absence_inference_allowed"])
if __name__=="__main__":unittest.main()
