import unittest
from pathlib import Path
from robo_dados_publicos.research.task268_pncp_history_probe_645 import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
    def setUp(self):
        self.c=load_config(ROOT/"config/task268_pncp_history_probe_645.v1.json")
        self.e=load_evidence(ROOT/"docs/evidence/TASK_268_PRELIVE_PNCP_HISTORY_645_0.8.0.json")
    def test_http200_list(self):
        def g(url,**kw):
            return {"requested_url":url,"remote_get_count":1,"raw_body_persisted":False,"url_effective":url,
                    "http_code":200,"content_type":"application/json","curl_exit_code":0,"curl_error":None,
                    "body_bytes":10,"body_sha256":"a"*64,"json_error":None,"json_shape":"LIST","event_count":1,
                    "event_keys":["sequencialHistorico","situacaoCompraNome"],"selected_history":[{"sequencialHistorico":1,"situacaoCompraNome":"Divulgada"}],"diagnostic_scalars":{}}
        r=execute(self.c,self.e,getter=g,offline_test_mode=True)
        self.assertEqual(r["outcome"],"DOCUMENTED_HISTORY_ROUTE_HTTP200_LIST")
        self.assertEqual(r["event_count"],1)
        self.assertFalse(r["traverse_exposed_links"])
    def test_missing_auth_stops(self):
        r=execute(self.c,self.e,authorization=None,expected_implementation_sha="0"*40)
        self.assertEqual(r["status"],"STOP_TASK268_LIVE_NOT_AUTHORIZED")
        self.assertEqual(r["source_get_count"],0)
    def test_history_allow_matches_task167(self):
        self.assertEqual(self.c["history_allow"],sorted(HISTORY_ALLOW))
if __name__=="__main__": unittest.main()
