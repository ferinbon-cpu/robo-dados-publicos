import unittest
from pathlib import Path
from robo_dados_publicos.research.task257_task256_raw_location_header import *
ROOT=Path(__file__).resolve().parents[1]
class Fake:
    def __init__(self,m): self.m=m
    def get(self,url,*,connect_timeout,max_time): return dict(self.m)
class T(unittest.TestCase):
    def setUp(self):
        self.c=load_config(ROOT/"config/task257_task256_raw_location_header.v1.json")
        self.e=load_evidence(ROOT/"docs/evidence/TASK_257_TASK256_HTTP301_CANONICAL_0.8.0.json")
    def meta(self,**kw):
        m={"requested_url":self.c["probe"]["requested_url"],"curl_exit_code":0,"curl_error":None,
           "http_code":301,"url_effective":self.c["probe"]["requested_url"],
           "location_headers":["https://pncp.gov.br/new"],"location_header_count":1,
           "remote_ip":"1.2.3.4","remote_port":443,"time_namelookup":.1,"time_connect":.2,
           "time_appconnect":.3,"time_starttransfer":.4,"time_total":.5,
           "remote_get_count":1,"response_body_persisted":False,"raw_headers_persisted":False}
        m.update(kw); return m
    def test_parse(self):
        self.assertEqual(parse_location_headers("HTTP/2 301\r\nLoCaTiOn: /abc\r\n"),["/abc"])
    def test_single(self):
        r=execute_probe(self.c,self.e,transport=Fake(self.meta()),authorization=None,expected_implementation_sha="0"*40,offline_test_mode=True)
        self.assertEqual(r["outcome"],"SINGLE_LOCATION_HEADER_CAPTURED")
        self.assertEqual(r["location"],"https://pncp.gov.br/new")
        self.assertFalse(r["raw_headers_persisted"])
    def test_missing(self):
        r=execute_probe(self.c,self.e,transport=Fake(self.meta(location_headers=[],location_header_count=0)),authorization=None,expected_implementation_sha="0"*40,offline_test_mode=True)
        self.assertEqual(r["outcome"],"REDIRECT_STATUS_WITHOUT_LOCATION_HEADER")
    def test_drift(self):
        with self.assertRaisesRegex(Task257Stop,"TASK257_EFFECTIVE_URL_DRIFT"):
            execute_probe(self.c,self.e,transport=Fake(self.meta(url_effective="https://bad/")),authorization=None,expected_implementation_sha="0"*40,offline_test_mode=True)
if __name__=="__main__": unittest.main()
