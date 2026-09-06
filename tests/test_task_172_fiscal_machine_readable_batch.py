import io
import json
import unittest
import zipfile

from robo_dados_publicos.research.task172_fiscal_machine_readable_batch import (
    Task172Stop,
    declared_machine_routes,
    load_contract,
    summarize_csv,
    summarize_json,
    summarize_zip,
    validate_contract,
)


class TestTask172FiscalMachineReadableBatch(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def test_contract_passes_and_is_bounded(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["source_count"], 12)
        self.assertEqual(got["max_requests"], 13)
        self.assertTrue(got["live_authorized"])

    def test_source_groups_and_hosts_are_exact(self):
        ids = [x["id"] for x in self.contract["sources"]]
        self.assertEqual(4, sum(x.startswith("SICONFI_") for x in ids))
        self.assertEqual(4, sum(x.startswith("FNDE_FUNDEB_") for x in ids))
        self.assertEqual(3, sum(x.startswith("TCESP_") for x in ids))
        self.assertEqual(1, sum(x.startswith("TDA_") for x in ids))
        self.assertEqual(
            {
                "apidatalake.tesouro.gov.br",
                "www.gov.br",
                "transparencia.tce.sp.gov.br",
                "transparencia.limeira.sp.gov.br",
            },
            set(self.contract["network_policy"]["allowed_hosts"]),
        )

    def test_siconfi_routes_are_json_and_limeira_filtered(self):
        rows = [x for x in self.contract["sources"] if x["id"].startswith("SICONFI_")]
        for row in rows:
            self.assertEqual(row["format"], "JSON")
            self.assertIn("id_ente=3526902", row["url"])
        self.assertTrue(any("Anexo%2008" in row["url"] for row in rows))

    def test_fnde_uses_declared_csv_not_invented_json(self):
        rows = [x for x in self.contract["sources"] if x["id"].startswith("FNDE_FUNDEB_")]
        self.assertTrue(all(x["format"] == "CSV" for x in rows))
        self.assertTrue(all(x["url"].endswith(".csv") for x in rows))

    def test_current_tce_routes_are_direct_declared_zip_files(self):
        rows = [x for x in self.contract["sources"] if x["id"].startswith("TCESP_")]
        self.assertTrue(all(x["format"] == "ZIP" for x in rows))
        self.assertIn("despesas-limeira-2026.zip", [x["url"].split("/")[-1] for x in rows])

    def test_json_summary_does_not_copy_arbitrary_fields(self):
        payload = {
            "items": [
                {
                    "an_exercicio": 2025,
                    "no_anexo": "RREO-Anexo 08",
                    "rotulo": "MDE",
                    "valor": 123.45,
                    "secret_unrelated_payload": "X" * 5000,
                }
            ]
        }
        got = summarize_json(json.dumps(payload).encode())
        self.assertEqual(got["record_count"], 1)
        self.assertEqual(got["limeira_selected_rows"][0]["valor"], 123.45)
        self.assertNotIn("secret_unrelated_payload", got["limeira_selected_rows"][0])

    def test_csv_summary_selects_limeira_only(self):
        data = "UF;Ente Federado;Codigo IBGE;Valor\nSP;Campinas;3509502;10\nSP;LIMEIRA;3526902;20\n".encode()
        got = summarize_csv(data, ["LIMEIRA", "3526902"])
        self.assertEqual(len(got["limeira_selected_rows"]), 1)
        row = got["limeira_selected_rows"][0]
        self.assertEqual(row["Ente Federado"], "LIMEIRA")

    def test_zip_summary_never_extracts_to_disk_and_is_bounded(self):
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("despesas.csv", "empenho;fornecedor;valor\n1;A;10\n2;B;20\n")
        got = summarize_zip(bio.getvalue())
        self.assertEqual(got["zip_member_names"], ["despesas.csv"])
        self.assertGreaterEqual(got["record_count"], 2)
        self.assertLessEqual(len(got["limeira_selected_rows"]), 30)

    def test_zip_path_traversal_fails_closed(self):
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            zf.writestr("../escape.csv", "a;b\n1;2\n")
        with self.assertRaisesRegex(Task172Stop, "TASK172_ZIP_PATH"):
            summarize_zip(bio.getvalue())

    def test_tda_declared_route_parser_accepts_only_explicit_allowlisted_machine_links(self):
        html = b"""
        <html><body>
          <a href="/export/dados.csv">CSV</a>
          <a href="https://evil.example/api/data">evil</a>
          <a href="/home.aspx">home</a>
          <a href="/api/public/despesas">api</a>
        </body></html>
        """
        got = declared_machine_routes(
            html,
            "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418",
            self.contract,
        )
        self.assertEqual(
            got,
            [
                "https://transparencia.limeira.sp.gov.br/export/dados.csv",
                "https://transparencia.limeira.sp.gov.br/api/public/despesas",
            ],
        )

    def test_fail_closed_semantics_are_preserved(self):
        adj = self.contract["adjudication"]
        self.assertEqual(adj["transport_failure"], "SOURCE_TRANSPORT_UNAVAILABLE_NOT_NO_DATA")
        self.assertEqual(adj["empty_machine_readable_result"], "EMPTY_WITHIN_EXACT_QUERY_NOT_GLOBAL_ABSENCE")
        self.assertFalse(adj["policy_identity_promotion"])
        self.assertFalse(adj["financial_identity_promotion"])
        self.assertFalse(adj["payment_promotion"])


if __name__ == "__main__":
    unittest.main()
