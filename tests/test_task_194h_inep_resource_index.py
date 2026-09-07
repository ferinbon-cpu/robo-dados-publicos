import json
import unittest
from scripts.task194h_inep_resource_index import exact_auth_comment,resource_index

class TestTask194HResourceIndex(unittest.TestCase):
    def test_auth(self):
        sha="a"*40
        self.assertEqual(exact_auth_comment(sha),f"TASK194H_INEP_RESOURCE_INDEX_AUTHORIZED main={sha} issue=613 max_http_requests=2 blob_gets=0 querydata=0")
    def test_index_keeps_metadata_not_blob_content(self):
        models={
          "exploration":{
            "resourcePackages":[
              {"id":7,"items":[
                {"path":"Report/Layout","type":"json","resourcePackageId":7,"resourcePackageItemBlobInfoId":99,"secret":"LEAK_ME_NOT"},
                {"path":"StaticResources/logo.png","type":"image","resourcePackageId":7,"resourcePackageItemBlobInfoId":100}
              ]}
            ],
            "pods":[{"id":1,"name":"pod","secret":"NO"}]
          },
          "package":{"pbixResources":[{"path":"Other/Resource","resourcePackageId":8,"resourcePackageItemBlobInfoId":101,"secret":"NO2"}]}
        }
        c={"allowed_scalar_keys":["id","name","path","type","resourcePackageId","resourcePackageItemBlobInfoId","resourcePackage","packageId","objectId","reportBlobInfoIdV1","reportBlobVersion"]}
        r=resource_index(models,c)
        self.assertEqual(r["resource_record_count"],3)
        self.assertEqual(r["blob_id_count"],3)
        self.assertIn("Report/Layout",r["paths"])
        s=json.dumps(r)
        self.assertNotIn("LEAK_ME_NOT",s); self.assertNotIn("NO2",s)
        self.assertEqual(r["blob_gets"],0); self.assertFalse(r["querydata_called"]); self.assertFalse(r["class_count_materialized"])
if __name__=="__main__": unittest.main()
