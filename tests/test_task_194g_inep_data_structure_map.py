import json
import unittest

from scripts.task194g_inep_data_structure_map import (
    exact_auth_comment,
    structural_map,
)


class TestTask194GStructureMap(unittest.TestCase):
    def test_exact_auth_comment(self):
        sha="a"*40
        self.assertEqual(
            exact_auth_comment(sha),
            f"TASK194G_INEP_DATA_STRUCTURE_AUTHORIZED main={sha} issue=611 max_http_requests=2 querydata=0",
        )

    def test_structure_map_finds_objectname_crossref_without_leaking_value(self):
        object_name="visual-abc"
        models={
            "models":[
                {
                    "id":"123",
                    "dbName":"db",
                    "conceptualSchema":{"secret":"DO_NOT_PERSIST_THIS_RAW_VALUE"},
                }
            ],
            "exploration":{
                "report":{"name":"resources/Layout.layout"},
                "sections":[
                    {
                        "name":"page1",
                        "visualContainers":[
                            {
                                "id":1,
                                "objectName":object_name,
                                "x":1,"y":2,"z":3,"width":10,"height":20,
                            }
                        ],
                    }
                ],
                "resourcePackages":{
                    "visual-abc":{
                        "config":{"secret":"OTHER_SECRET_VALUE"},
                    }
                },
            },
        }
        contract={
            "interesting_key_tokens":[
                "config","query","data","resource","visual","object","schema","package","layout","pod","concept"
            ],
            "limits":{
                "max_interesting_paths":500,
                "max_objectname_crossrefs":300,
                "max_depth":8,
            },
        }
        result=structural_map(models,contract)
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["objectnames"]["visual_container_unique_count"],1)
        self.assertEqual(result["objectnames"]["crossreferenced_unique_count"],1)
        self.assertEqual(result["objectnames"]["crossreferenced_sample"],[object_name])
        paths=[x["path"] for x in result["objectnames"]["crossrefs"]]
        self.assertTrue(any("resourcePackages.visual-abc" in p for p in paths))
        interesting=[x["path"] for x in result["interesting_paths"]]
        self.assertTrue(any("conceptualSchema" in p for p in interesting))
        self.assertTrue(any("resourcePackages" in p for p in interesting))
        payload=json.dumps(result,ensure_ascii=False)
        self.assertNotIn("DO_NOT_PERSIST_THIS_RAW_VALUE",payload)
        self.assertNotIn("OTHER_SECRET_VALUE",payload)
        self.assertFalse(result["querydata_called"])
        self.assertFalse(result["class_count_materialized"])
        self.assertFalse(result["raw_models_persisted"])

    def test_primary_visual_objectname_is_not_false_crossref(self):
        models={
            "models":[{"id":"1"}],
            "exploration":{
                "sections":[
                    {
                        "visualContainers":[
                            {"objectName":"only-primary","x":1,"y":1,"z":1,"width":1,"height":1}
                        ]
                    }
                ]
            },
        }
        contract={
            "interesting_key_tokens":["object","visual","config","query","data"],
            "limits":{
                "max_interesting_paths":500,
                "max_objectname_crossrefs":300,
                "max_depth":8,
            },
        }
        result=structural_map(models,contract)
        self.assertEqual(result["objectnames"]["visual_container_unique_count"],1)
        self.assertEqual(result["objectnames"]["crossreferenced_unique_count"],0)
        self.assertEqual(result["objectnames"]["crossref_count"],0)


if __name__ == "__main__":
    unittest.main()
