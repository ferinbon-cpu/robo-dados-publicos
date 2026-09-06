import unittest
from pathlib import Path

from robo_dados_publicos.research.task168_pncp_consulta_contracts_fallback import (
    Task168BStop,
    build_url,
    combine_pages,
    load_config,
    scan_page,
)


def config():
    return load_config(Path("config/task168_pncp_consulta_contracts_fallback.v1.json"))


class TestTask168BPncpConsultaContractsFallback(unittest.TestCase):
    def test_exact_official_consulta_scope_is_pinned(self):
        cfg = config()
        url = build_url(cfg, 1)
        self.assertIn("https://pncp.gov.br/api/consulta/v1/contratos?", url)
        self.assertIn("dataInicial=20260608", url)
        self.assertIn("dataFinal=20260905", url)
        self.assertIn("cnpjOrgao=45132495000140", url)
        self.assertIn("tamanhoPagina=500", url)
        self.assertEqual(cfg["source"]["maxPaginas"], 20)

    def test_scan_page_matches_only_exact_purchase_control_id(self):
        cfg = config()
        payload = {
            "data": [
                {
                    "numeroControlePNCP": "45132495000140-2-000001/2026",
                    "numeroControlePNCPCompra": "45132495000140-1-000368/2026",
                    "numeroContratoEmpenho": "C1",
                    "orgaoEntidade": {"cnpj": "45132495000140"},
                },
                {
                    "numeroControlePNCP": "45132495000140-2-000002/2026",
                    "numeroControlePNCPCompra": "45132495000140-1-000999/2026",
                    "numeroContratoEmpenho": "C2",
                    "orgaoEntidade": {"cnpj": "45132495000140"},
                },
            ],
            "totalRegistros": 2,
            "totalPaginas": 1,
            "numeroPagina": 1,
            "paginasRestantes": 0,
        }
        page = scan_page(payload, cfg, 1)
        self.assertEqual(len(page["matches"]), 1)
        self.assertEqual(page["matches"][0]["target_id"], "SCHOOL_PASS")

    def test_entity_mismatch_fails_closed_even_on_target_match(self):
        cfg = config()
        payload = {
            "data": [{
                "numeroControlePNCPCompra": "45132495000140-1-000368/2026",
                "orgaoEntidade": {"cnpj": "99999999999999"},
            }],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "numeroPagina": 1,
            "paginasRestantes": 0,
        }
        with self.assertRaises(Task168BStop):
            scan_page(payload, cfg, 1)

    def test_combine_requires_complete_pagination(self):
        pages = [{
            "requested_page": 1,
            "reported_page": 1,
            "totalRegistros": 501,
            "totalPaginas": 2,
            "paginasRestantes": 1,
            "record_count": 500,
            "matches": [],
        }]
        with self.assertRaises(Task168BStop):
            combine_pages(pages)

    def test_complete_pagination_supports_bounded_negative(self):
        pages = [
            {
                "requested_page": 1,
                "reported_page": 1,
                "totalRegistros": 2,
                "totalPaginas": 2,
                "paginasRestantes": 1,
                "record_count": 1,
                "matches": [],
            },
            {
                "requested_page": 2,
                "reported_page": 2,
                "totalRegistros": 2,
                "totalPaginas": 2,
                "paginasRestantes": 0,
                "record_count": 1,
                "matches": [],
            },
        ]
        result = combine_pages(pages)
        self.assertTrue(result["exhaustive_within_exact_scope"])
        self.assertEqual(result["target_match_count"], 0)


if __name__ == "__main__":
    unittest.main()
