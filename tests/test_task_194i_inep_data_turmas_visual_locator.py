import unittest

from scripts.task194i_inep_data_turmas_visual_locator import (
    exact_auth_comment,
    locate_turmas_visuals,
)


class TestTask194ITurmasVisualLocator(unittest.TestCase):
    def contract(self):
        return {
            "match_token":"turm",
            "identifier_keys":[
                "Entity","Property","Measure","Column","Table","Field","queryRef","nativeQueryRef",
                "displayName","visualType","objectName","groupName","Name"
            ],
            "allowed_context_tokens":["turm","ano","munic","depend","rede","escola"],
            "limits":{
                "max_visuals":120,
                "max_matches_per_visual":40,
                "max_identifiers_per_visual":160,
                "max_text_chars":180,
            },
        }

    def test_exact_auth_comment(self):
        sha="a"*40
        self.assertEqual(
            exact_auth_comment(sha),
            f"TASK194I_TURMAS_VISUAL_AUTHORIZED main={sha} issue=617 max_http_requests=2 querydata=0",
        )

    def test_ranks_real_turma_field_above_navigation_link(self):
        doc={
            "pages":{"pages":[
                {
                    "name":"page0","displayName":"Visão geral",
                    "visualContainers":[
                        {
                            "objectName":"nav1",
                            "content":{"visual":{
                                "visualType":"actionButton",
                                "visualContainerObjects":{
                                    "visualLink":[{"properties":{"tooltip":{"expr":{"Literal":{"Value":"Turmas"}}}}}]
                                }
                            }}
                        },
                        {
                            "objectName":"card1",
                            "content":{"visual":{
                                "visualType":"card",
                                "query":{
                                    "queryState":{
                                        "Values":{"projections":[{
                                            "field":{"Measure":{
                                                "Expression":{"SourceRef":{"Entity":"FATO_TURMA"}},
                                                "Property":"QT_TUR_BAS"
                                            }},
                                            "queryRef":"FATO_TURMA.QT_TUR_BAS",
                                            "nativeQueryRef":"Turmas",
                                            "displayName":"Número de Turmas"
                                        }]}
                                    }
                                },
                                "visualContainerObjects":{
                                    "title":[{"properties":{"text":{"expr":{"Literal":{"Value":"Número de Turmas"}}}}}]
                                }
                            }}
                        }
                    ]
                }
            ]}
        }
        got=locate_turmas_visuals(doc,self.contract())
        self.assertEqual(got["matched_visual_count"],2)
        top=got["ranked_candidates"][0]
        self.assertEqual(top["object_name"],"card1")
        self.assertGreater(top["turma_field_score"],0)
        vals={x["value"] for x in top["identifiers"]}
        self.assertIn("QT_TUR_BAS",vals)
        self.assertIn("FATO_TURMA",vals)

    def test_non_turma_visual_is_excluded(self):
        doc={"pages":{"pages":[{"visualContainers":[{
            "objectName":"x","content":{"visual":{"visualType":"slicer","query":{"queryState":{
                "Values":{"projections":[{"displayName":"Município","queryRef":"DIM_MUN.NO_MUNICIPIO"}]}
            }}}}
        }]}]}}
        with self.assertRaisesRegex(Exception,"TASK194I_NO_TURM_VISUAL"):
            locate_turmas_visuals(doc,self.contract())


if __name__ == "__main__":
    unittest.main()
