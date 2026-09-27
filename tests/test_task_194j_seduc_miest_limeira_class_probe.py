import unittest

from scripts.task194j_seduc_miest_limeira_class_probe import (
    exact_auth_comment,
    inspect_csv,
)


class TestTask194JSeducMiestProbe(unittest.TestCase):
    def contract(self):
        return {
            "target":{
                "municipality_name":"LIMEIRA",
                "municipality_tokens":["MUNIC","MUN","CIDADE"],
                "interesting_header_tokens":[
                    "CLAS","TURM","MATR","REDE","DEPEND","MUNIC","CIDADE",
                    "ESCOLA","CIE","CICLO","ENSINO","DIRETORIA","TIPO"
                ],
            },
            "limits":{
                "max_distinct_values_per_field":80,
                "max_category_fields":40,
                "max_numeric_summary_fields":60,
            },
        }

    def test_exact_auth_comment(self):
        sha="a"*40
        self.assertEqual(
            exact_auth_comment(sha),
            f"TASK194J_SEDUC_MIEST_AUTHORIZED main={sha} issue=619 max_http_requests=1 materialize=0",
        )

    def test_limeira_network_groups_are_sanitized(self):
        raw=(
            "MUNICIPIO;DEPENDENCIA;CICLO;CLASSES;MATRICULAS\n"
            "LIMEIRA;MUNICIPAL;EI;10;200\n"
            "LIMEIRA;MUNICIPAL;EF AI;20;500\n"
            "LIMEIRA;ESTADUAL;EF AF;30;800\n"
            "CAMPINAS;MUNICIPAL;EI;99;999\n"
        ).encode("utf-8")
        got=inspect_csv(raw,self.contract())
        self.assertEqual(got["row_count"],4)
        self.assertEqual(got["limeira_row_count"],3)
        self.assertIn("MUNICIPIO",got["municipality_candidate_fields"])
        self.assertEqual(
            got["limeira_grouped_by_network_candidates"]["DEPENDENCIA"]["MUNICIPAL"]["numeric_sums"]["CLASSES"],
            30.0,
        )
        self.assertEqual(
            got["limeira_grouped_by_network_candidates"]["DEPENDENCIA"]["ESTADUAL"]["numeric_sums"]["MATRICULAS"],
            800.0,
        )

    def test_no_limeira_fails_closed(self):
        raw=("MUNICIPIO;CLASSES\nCAMPINAS;10\n").encode("utf-8")
        with self.assertRaisesRegex(Exception,"TASK194J_LIMEIRA_NOT_FOUND"):
            inspect_csv(raw,self.contract())


if __name__ == "__main__":
    unittest.main()
