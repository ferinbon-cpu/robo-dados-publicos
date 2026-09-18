import unittest
from pathlib import Path
from robo_dados_publicos.research.task274_linked_contract_probe_645 import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
    def setUp(self):
        self.c=load_config(ROOT/"config/task274_linked_contract_probe_645.v1.json")
        self.e=load_evidence(ROOT/"docs/evidence/TASK_274_PRELIVE_LINKED_CONTRACT_645_0.8.0.json")
    def test_projection_excludes_noncontract_identity(self):
        row={"numeroControlePNCPCompra":"45132495000140-1-000645/2026","niFornecedor":"redacted","nomeRazaoSocialFornecedor":"redacted","usuarioNome":"redacted","valorGlobal":10}
        out=sanitize(row,self.c)
        self.assertNotIn("niFornecedor",out);self.assertNotIn("usuarioNome",out);self.assertEqual(out["valorGlobal"],10)
    def test_empty_list_operational_not_absent(self):
        def g(url,**kw):
            return {"requested_url":url,"http_code":200,"content_type":"application/json","url_effective":url,"curl_exit_code":0,"curl_error":None,"body_bytes":2,"body_sha256":"a"*64,"json_error":None,"json_shape":"LIST","row_count":0,"item_keys":[],"purchase_identity_valid":True,"contracts":[],"contracts_sha256":"b"*64,"remote_get_count":1,"raw_body_persisted":False}
        r=execute(self.c,self.e,getter=g,offline_test_mode=True)
        self.assertEqual(r["outcome"],"LINKED_CONTRACT_ROUTE_HTTP200_EMPTY_LIST");self.assertFalse(r["absence_inference_allowed"])
    def test_no_auth(self):
        self.assertEqual(execute(self.c,self.e,authorization=None,expected_implementation_sha="0"*40)["source_get_count"],0)
if __name__=="__main__":unittest.main()
