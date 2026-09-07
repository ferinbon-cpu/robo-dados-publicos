import base64
import gzip
import json
import unittest

from scripts.task194f_inep_data_embedded_visual_probe import (
    exact_auth_comment,
    sanitize_models,
)


class TestTask194FEmbeddedVisualProbe(unittest.TestCase):
    def test_exact_auth_comment(self):
        sha="a"*40
        self.assertEqual(
            exact_auth_comment(sha),
            f"TASK194F_INEP_DATA_EMBEDDED_AUTHORIZED main={sha} issue=609 max_http_requests=2 querydata=0",
        )

    def test_sanitizer_finds_embedded_target_without_unrelated_rows(self):
        embedded_obj={
            "data":{
                "descriptor":{
                    "Select":[
                        {"Kind":1,"GroupKeys":[{"Source":{"Entity":"Indicadores","Property":"Nome"}}]},
                        {"Kind":1,"GroupKeys":[{"Source":{"Entity":"Indicadores","Property":"Valor"}}]},
                    ]
                },
                "dsr":{
                    "DS":[
                        {
                            "PH":[{"DM0":[{"C":["Limeira","Municipal","Número de Turmas",650]}]}],
                            "ValueDicts":{"cidade":{"1":"Outra Cidade"}},
                        }
                    ]
                },
            }
        }
        raw=json.dumps(embedded_obj,ensure_ascii=False).encode("utf-8")
        encoded=base64.b64encode(gzip.compress(raw)).decode("ascii")
        config=json.dumps(
            {
                "name":"visual-turmas",
                "singleVisual":{"visualType":"card"},
                "title":"Número de Turmas",
            },
            ensure_ascii=False,
        )
        models={
            "models":[{"id":"123","dbName":"db"}],
            "exploration":{
                "sections":[
                    {
                        "displayName":"Indicadores - Estatísticas gerais",
                        "visualContainers":[
                            {
                                "config":config,
                                "dataBinaryBase64Encoded":encoded,
                                "x":1,
                            },
                            {"x":2},
                        ],
                    }
                ]
            },
        }
        contract={
            "target_tokens":["turma","classe","limeira","municipal","alunos por turma","media de alunos por turma"],
            "limits":{
                "max_matched_literals_per_payload":25,
                "max_literal_chars":240,
                "max_candidate_visuals":200,
            },
        }
        result=sanitize_models(models,contract)
        self.assertEqual(result["visual_count"],2)
        self.assertEqual(result["embedded_payload_count"],1)
        self.assertEqual(result["candidate_count"],1)
        c=result["candidates"][0]
        self.assertIn("turma",c["config_match"]["matched_tokens"])
        self.assertIn("limeira",c["embedded_match"]["matched_tokens"])
        self.assertIn("Limeira",c["embedded_match"]["matched_literals"])
        self.assertIn("Municipal",c["embedded_match"]["matched_literals"])
        self.assertNotIn("Outra Cidade",c["embedded_match"]["matched_literals"])
        props={x.get("property") for x in c["embedded_match"]["descriptor_select"]}
        self.assertIn("Nome",props)
        self.assertFalse(result["querydata_called"])
        self.assertFalse(result["class_count_materialized"])
        self.assertFalse(result["raw_embedded_binary_persisted"])


if __name__ == "__main__":
    unittest.main()
