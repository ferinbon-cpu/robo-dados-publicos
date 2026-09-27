import unittest
from pathlib import Path
from robo_dados_publicos.research.task263_paired_health_645_vs_648 import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 def setUp(self):self.c=load_config(ROOT/"config/task263_paired_health_645_vs_648.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_263_TASK262_648_UNAVAILABLE_CANONICAL_0.8.0.json")
 def getter(self,url,**k):
  t=next(x for x in self.c["targets"] if x["url"]==url);ok=t["role"]=="HEALTH_CONTROL"
  return {"url_effective":url,"http_code":200 if ok else 500,"curl_exit_code":0,"curl_error":None,"content_type":"application/json","body_bytes":100,
   "body_sha256":"a"*64,"json_error":None,"selected":{"numeroControlePNCP":t["control"]} if ok else {},"diagnostic_scalars":{"status":500} if not ok else {}}
 def test_health_ok_target_bad(self):
  r=execute(self.c,self.e,getter=self.getter,offline_test_mode=True);self.assertEqual(r["outcome"],"HEALTH_CONTROL_OK_TARGET_648_UNRESOLVED");self.assertEqual(r["source_get_count"],2)
if __name__=="__main__":unittest.main()
