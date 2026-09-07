import json
import unittest

from scripts.task194h_inep_data_exploration_document_schema import (
    _extract_document,
    exact_auth_comment,
    inspect_document,
)


class TestTask194HExplorationDocumentSchema(unittest.TestCase):
    def test_exact_auth_comment(self):
        sha="a"*40
        self.assertEqual(
            exact_auth_comment(sha),
            f"TASK194H_EXPLORATION_DOCUMENT_AUTHORIZED main={sha} issue=615 max_http_requests=2 querydata=0",
        )

    def test_extracts_json_string_document(self):
        visual={
            "objectName":"abc123",
            "config":json.dumps({
                "singleVisual":{
                    "visualType":"card",
                    "vcObjects":{
                        "title":[{"properties":{"text":{"expr":{"Literal":{"Value":"Número de Turmas"}}}}}]
                    }
                }
            }),
            "query":json.dumps({
                "Commands":[{
                    "SemanticQueryDataShapeCommand":{
                        "Query":{
                            "From":[{"Name":"t","Entity":"Turma","Type":0}],
                            "Select":[
                                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"t"}},"Property":"QT_TUR_BAS"}}}}
                            ]
                        }
                    }
                }]
            }),
        }
        raw=json.dumps({"sections":[{"visualContainers":[visual]}]})
        models={"exploration":{"explorationContent":{"explorationDocument":raw}}}
        doc,meta=_extract_document(models)
        self.assertTrue(meta["parsed_from_json_string"])
        self.assertEqual(doc["sections"][0]["visualContainers"][0]["objectName"],"abc123")

    def test_inspection_finds_query_identifiers_and_matching_text(self):
        contract={
            "interesting_keys":[
                "config","query","prototypequery","semanticquery","datatransforms","visualtype",
                "objectname","title","filter","filters","select","where","from","measure",
                "column","property","entity","table","field"
            ],
            "allowed_text_tokens":["turm","matr","munic","depend","rede","escola","ano"],
            "limits":{
                "max_paths":700,
                "max_identifiers":500,
                "max_matching_texts":250,
                "max_depth":14,
                "max_text_chars":140,
            },
        }
        doc={
            "sections":[{
                "visualContainers":[{
                    "objectName":"abc123",
                    "config":json.dumps({
                        "singleVisual":{
                            "visualType":"card",
                            "vcObjects":{
                                "title":[{"properties":{"text":{"expr":{"Literal":{"Value":"Número de Turmas"}}}}}]
                            }
                        }
                    }),
                    "query":json.dumps({
                        "Query":{
                            "From":[{"Name":"t","Entity":"Turma"}],
                            "Select":[{
                                "Column":{
                                    "Expression":{"SourceRef":{"Source":"t"}},
                                    "Property":"QT_TUR_BAS"
                                }
                            },{
                                "Column":{
                                    "Expression":{"SourceRef":{"Source":"t"}},
                                    "Property":"NO_MUNICIPIO"
                                }
                            }]
                        }
                    })
                }]
            }]
        }
        got=inspect_document(doc,contract)
        values={x["value"] for x in got["identifiers"]}
        self.assertIn("card",values)
        self.assertIn("Turma",values)
        self.assertIn("QT_TUR_BAS",values)
        self.assertIn("NO_MUNICIPIO",values)
        self.assertGreaterEqual(got["matching_text_count"],1)
        self.assertGreaterEqual(got["parsed_nested_json_count"],2)

    def test_no_querydata_or_values_are_materialized_by_inspector(self):
        contract={
            "interesting_keys":["query","select","where","property","entity"],
            "allowed_text_tokens":["turm"],
            "limits":{
                "max_paths":20,
                "max_identifiers":20,
                "max_matching_texts":20,
                "max_depth":10,
                "max_text_chars":100,
            },
        }
        got=inspect_document({"query":{"Select":[{"Property":"QT_TUR_BAS"}]}},contract)
        self.assertNotIn("rows",got)
        self.assertNotIn("values",got)
        self.assertNotIn("querydata",got)


if __name__ == "__main__":
    unittest.main()
