from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.task166_pncp_modality9_direct_json import (
    Task166Stop,
    combine_pages,
    load_config,
    scan_page,
)

CONFIG = ROOT / "config/task166_pncp_modality9_direct_json_sweep.v1.json"


def rec(seq, process, obj, value, control):
    return {
        "anoCompra": 2026,
        "sequencialCompra": seq,
        "numeroControlePNCP": control,
        "processo": process,
        "numeroCompra": process.replace("I", ""),
        "objetoCompra": obj,
        "valorTotalEstimado": value,
        "valorTotalHomologado": None,
        "dataPublicacaoPncp": "2026-08-19T00:00:00",
        "modalidadeId": 9,
        "modalidadeNome": "Inexigibilidade",
        "orgaoEntidade": {"cnpj": "45132495000140", "razaoSocial": "MUNICIPIO DE LIMEIRA"},
        "unidadeOrgao": {"municipioNome": "Limeira", "ufSigla": "SP"},
    }


class TestTask166(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_config(CONFIG)

    def test_target_i00084(self):
        payload = {
            "data": [rec(593, "I00084", "CURSO DE CAPACITACAO", 12400.0, "45132495000140-1-000593/2026")],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "numeroPagina": 1,
            "paginasRestantes": 0,
        }
        page = scan_page(payload, self.c, 1)
        self.assertEqual("I00084", page["target_hits"][0]["target_id"])
        combined = combine_pages([page])
        self.assertTrue(combined["exhaustive_within_exact_scope"])

    def test_school_pass_is_education_relevant(self):
        payload = {
            "data": [rec(360, "I00001", "AQUISICAO DE PASSE ESCOLAR", 3816720.0, "45132495000140-1-000360/2026")],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "numeroPagina": 1,
            "paginasRestantes": 0,
        }
        page = scan_page(payload, self.c, 1)
        self.assertEqual("SCHOOL_PASS", page["target_hits"][0]["target_id"])
        self.assertEqual(1, len(page["education_hits"]))
        self.assertEqual(0, len(page["explicit_eiti_hits"]))

    def test_wrong_cnpj_fails_closed(self):
        x = rec(1, "I1", "CURSO", 1, "x")
        x["orgaoEntidade"]["cnpj"] = "00000000000000"
        payload = {"data": [x], "totalRegistros": 1, "totalPaginas": 1, "numeroPagina": 1, "paginasRestantes": 0}
        with self.assertRaises(Task166Stop):
            scan_page(payload, self.c, 1)

    def test_partial_pagination_fails_closed(self):
        payload = {
            "data": [rec(1, "I1", "OUTRO", 1, "x")],
            "totalRegistros": 2,
            "totalPaginas": 2,
            "numeroPagina": 1,
            "paginasRestantes": 1,
        }
        page = scan_page(payload, self.c, 1)
        with self.assertRaises(Task166Stop):
            combine_pages([page])


if __name__ == "__main__":
    unittest.main()
