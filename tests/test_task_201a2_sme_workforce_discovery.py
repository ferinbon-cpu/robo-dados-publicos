import json
import unittest

from scripts.task201a2_sme_workforce_discovery import (
    derive_sanitized_result,
    discover_sme_paths,
    exact_auth_comment,
    _load,
)


def _home():
    return b"""
    <html><body>
    <p>Atribuicao para Professores efetivos da Rede Municipal.</p>
    <p>Indicacao dos Professores ( CLT ) que realizaram o Processo Seletivo.</p>
    <a href="/atribuicao_2026.php">Atribuicao 2026</a>
    <a href="/rh/docentes.php?x=1#frag">Docentes</a>
    </body></html>
    """


def _menu():
    return b"""
    <html><body>
    <a href="https://sme.limeira.sp.gov.br/pml/uploads/">Atribuicao</a>
    <a href="/app/outro.php">Outro</a>
    </body></html>
    """


def _contracted():
    return """
    <html><body>
    <h1>PROFESSORES CONTRATADOS EM CLASSE</h1>
    <p>IMPRESSAO EM: 07-09-2026</p>
    <table>
      <tr><th>MATRICULA</th><th>NOME</th><th>C.P.F.</th><th>CARGO</th><th>UNIDADE ESCOALR</th></tr>
      <tr><td>000.001-1</td><td>PESSOA TESTE A</td><td>111.111.111-11</td><td>ENSINO FUNDAMENTAL</td><td>ESCOLA A</td></tr>
      <tr><td>000.001-1</td><td>PESSOA TESTE A</td><td>111.111.111-11</td><td>ARTE</td><td>ESCOLA B</td></tr>
      <tr><td>000.002-2</td><td>PESSOA TESTE B</td><td>222.222.222-22</td><td>EDUCACAO INFANTIL</td><td>ESCOLA A</td></tr>
    </table>
    </body></html>
    """.encode("utf-8")


class TestTask201A2SmeWorkforceDiscovery(unittest.TestCase):
    def test_contract_preserves_inep_block_and_no_retry(self):
        obj = _load()
        self.assertEqual(obj["prior_inep_probe"]["status"], "TRANSPORT_BLOCKED")
        self.assertFalse(obj["prior_inep_probe"]["retry_in_task201a2"])

    def test_exact_authorization_comment(self):
        sha = "b" * 40
        self.assertEqual(
            exact_auth_comment(sha),
            (
                "TASK201A2_SME_WORKFORCE_AUTHORIZED "
                f"main={sha} issue=639 sme_attempts=2 raw_persist=0 pii_persist=0"
            ),
        )

    def test_href_discovery_is_same_host_path_only_and_strips_query(self):
        obj = _load()
        got = discover_sme_paths(
            _home(),
            base_url=obj["sources"]["sme_home"]["url"],
            obj=obj,
        )
        self.assertIn("/atribuicao_2026.php", got)
        self.assertIn("/rh/docentes.php", got)
        self.assertTrue(all("?" not in path and "#" not in path for path in got))

    def test_combined_result_is_aggregate_only(self):
        result = derive_sanitized_result(
            home_bytes=_home(),
            app_menu_bytes=_menu(),
            contracted_bytes=_contracted(),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["sme_bond_taxonomy"]["bond_categories"],
            ["EFETIVO", "CLT_PROCESSO_SELETIVO"],
        )
        self.assertEqual(
            result["sme_contracted_aggregate"]["unique_contracted_teacher_count"],
            2,
        )
        self.assertEqual(result["inep_transport"]["status"], "TRANSPORT_BLOCKED")
        self.assertFalse(result["guards"]["person_level_output"])
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("PESSOA TESTE", encoded)
        self.assertNotIn("111.111.111-11", encoded)
        self.assertNotIn("000.001-1", encoded)

    def test_dynamic_home_label_gap_does_not_block_contracted_aggregate(self):
        result = derive_sanitized_result(
            home_bytes=b"<html><body>Sistema Integrado de Gestao Educacional</body></html>",
            app_menu_bytes=_menu(),
            contracted_bytes=_contracted(),
        )
        self.assertEqual(result["status"], "PASS_WITH_DYNAMIC_HOME_LABEL_GAP")
        self.assertEqual(result["sme_bond_taxonomy"]["raw_home_label_status"], "NOT_OBSERVED_NOT_ABSENT")
        self.assertEqual(
            result["sme_contracted_aggregate"]["unique_contracted_teacher_count"],
            2,
        )
        self.assertFalse(result["guards"]["person_level_output"])


if __name__ == "__main__":
    unittest.main()
