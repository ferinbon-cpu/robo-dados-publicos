import unittest
from pathlib import Path
from robo_dados_publicos.research.task261_three_500_reobserve import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 def setUp(self):self.c=load_config(ROOT/"config/task261_three_500_reobserve.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_261_TASK260_PARTIAL_CANONICAL_0.8.0.json")
 def getter(self,url,**k):
  ctl=next(t["control"] for t in self.c["targets"] if t["url"]==url)
  return {"url_effective":url,"http_code":500,"curl_exit_code":0,"curl_error":None,"content_type":"application/json","body_bytes":341,"body_sha256":"a"*64,"json_error":None,"top_level_keys":["message","status"],"selected":{},"diagnostic_scalars":{"status":500,"message":"x"},"raw_body_persisted":False}
 def test_unresolved(self):
  r=execute(self.c,self.e,getter=self.getter,offline_test_mode=True);self.assertEqual(r["resolved_count"],0);self.assertEqual(r["source_get_count"],3)
 def test_scalar_projection(self):self.assertEqual(scalar_projection({"a":1,"b":"z","c":[1]}),{"a":1,"b":"z"})
if __name__=="__main__":unittest.main()
