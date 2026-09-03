import unittest
from pathlib import Path

from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver


ROOT = Path(__file__).resolve().parents[1]


class TestTask081ContractCandidateHardening(unittest.TestCase):
    def test_live_number_year_collisions_without_expected_cnpj_are_rejected(self):
        rows = [
            [
                "", "CONTRATOS", "9/2025", "30903/2024", "17/03/2025", "16/03/2026",
                "ART MULTIMÍDIA - COMÉRCIO E SERVIÇOS LTDA",
                "AQUISIÇÃO DE PAINÉIS ELETRÔNICOS PARA OS ESTÁDIOS MUNICIPAIS, COM INSTALAÇÃO INCLUSA.",
                "R$307.000,00", "contrato_09_2025.pdf",
            ],
            [
                "", "ATAS", "9/2025", "24835/2024", "14/02/2025", "13/02/2026",
                "FUTURA COMÉRCIO DE PRODUTOS MÉDICOS HOSPITALARES LTDA",
                "EVENTUAL AQUISIÇÃO DE MEDICAMENTOS PADRONIZADOS",
                "R$735.109,35", "ata_09_2025.pdf",
            ],
        ]
        keys = {
            "year": 2025,
            "contract_number": "09/2025.",
            "cnpj": "12226306000140",
        }

        candidates = LimeiraContractsResolver._candidate_rows(rows, keys)

        self.assertEqual([], candidates)

    def test_zero_padded_and_trailing_punctuation_contract_reference_normalizes(self):
        rows = [[
            "", "CONTRATOS", "9/2025", "29185/2025", "17/03/2025", "16/03/2026",
            "EMPRESA EXEMPLO", "INSTALAÇÃO DE AR CONDICIONADO",
            "12.226.306/0001-40", "contrato_09_2025.pdf",
        ]]
        keys = {
            "year": 2025,
            "contract_number": "09/2025.",
            "cnpj": "12226306000140",
        }

        candidates = LimeiraContractsResolver._candidate_rows(rows, keys)

        self.assertEqual(1, len(candidates))
        self.assertIn("CONTRACT_FULL", candidates[0]["match_signals"])
        self.assertIn("CONTRACT_NUMBER_YEAR_NORMALIZED", candidates[0]["match_signals"])
        self.assertIn("CNPJ", candidates[0]["match_signals"])

    def test_contract_reference_embedded_in_documentary_text_is_allowed(self):
        rows = [["Contrato 09/2025 - objeto X", "12.226.306/0001-40"]]
        keys = {"contract_number": "09/2025", "cnpj": "12226306000140"}

        candidates = LimeiraContractsResolver._candidate_rows(rows, keys)

        self.assertEqual(1, len(candidates))
        self.assertIn("CONTRACT_FULL", candidates[0]["match_signals"])

    def test_filename_numeric_stem_does_not_substitute_for_contract_cell(self):
        rows = [[
            "", "CONTRATOS", "51/2025", "29185/2025", "EMPRESA EXEMPLO",
            "12.226.306/0001-40", "contrato_09_2025.pdf",
        ]]
        keys = {
            "year": 2025,
            "contract_number": "09/2025.",
            "cnpj": "12226306000140",
        }

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_date_fragment_does_not_substitute_for_contract_reference(self):
        rows = [["CONTRATOS", "51/2025", "17/03/2025", "12.226.306/0001-40"]]
        keys = {"contract_number": "03/2025", "cnpj": "12226306000140"}

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_dotted_process_fragment_does_not_substitute_for_contract_reference(self):
        rows = [["CONTRATOS", "51/2025", "29.185/2025", "12.226.306/0001-40"]]
        keys = {"contract_number": "185/2025", "cnpj": "12226306000140"}

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_cnpj_is_not_constructed_across_neighboring_cells(self):
        rows = [["9/2025", "12226306", "000140"]]
        keys = {
            "year": 2025,
            "contract_number": "09/2025.",
            "cnpj": "12226306000140",
        }

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_cnpj_substring_inside_larger_numeric_cell_is_rejected(self):
        rows = [["9/2025", "ID 77 - CNPJ 12.226.306/0001-40 - lote 8"]]
        keys = {"contract_number": "09/2025", "cnpj": "12226306000140"}

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_malformed_expected_cnpj_fails_closed(self):
        rows = [["9/2025", "12.226.306/0001-40"]]
        keys = {"contract_number": "09/2025", "cnpj": "12226306"}

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_cnpj_cannot_override_mismatched_contract_when_contract_key_exists(self):
        rows = [["CONTRATOS", "51/2025", "12.226.306/0001-40", "EMPRESA EXEMPLO"]]
        keys = {
            "year": 2025,
            "contract_number": "09/2025.",
            "cnpj": "12226306000140",
        }

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_contract_only_behavior_remains_available_when_no_stronger_key_exists(self):
        rows = [["CONTRATOS", "51/2025", "Fornecedor sem CNPJ publicado"]]
        keys = {"year": 2025, "contract_number": "51/2025"}

        candidates = LimeiraContractsResolver._candidate_rows(rows, keys)

        self.assertEqual(1, len(candidates))
        self.assertIn("CONTRACT_FULL", candidates[0]["match_signals"])
        self.assertIn("CONTRACT_NUMBER_YEAR_NORMALIZED", candidates[0]["match_signals"])

    def test_supplier_mismatch_blocks_contract_collision_when_cnpj_absent(self):
        rows = [["CONTRATOS", "51/2025", "OUTRO FORNECEDOR"]]
        keys = {
            "year": 2025,
            "contract_number": "51/2025",
            "contractor": "FORNECEDOR ESPERADO",
        }

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_cnpj_only_candidate_requires_task_without_contract_key(self):
        rows = [["EMPRESA EXEMPLO", "12.226.306/0001-40"]]
        keys = {"cnpj": "12226306000140"}

        candidates = LimeiraContractsResolver._candidate_rows(rows, keys)

        self.assertEqual(1, len(candidates))
        self.assertEqual(["CNPJ"], candidates[0]["match_signals"])

    def test_cnpj_only_with_known_supplier_mismatch_fails_closed(self):
        rows = [["OUTRA EMPRESA", "12.226.306/0001-40"]]
        keys = {"cnpj": "12226306000140", "contractor": "EMPRESA ESPERADA"}

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_cnpj_only_with_known_supplier_agreement_is_candidate(self):
        rows = [["EMPRESA ESPERADA LTDA", "12.226.306/0001-40"]]
        keys = {"cnpj": "12226306000140", "contractor": "EMPRESA ESPERADA"}

        candidates = LimeiraContractsResolver._candidate_rows(rows, keys)

        self.assertEqual(1, len(candidates))
        self.assertIn("CNPJ", candidates[0]["match_signals"])
        self.assertIn("SUPPLIER_NAME", candidates[0]["match_signals"])

    def test_ambiguous_multiple_contract_references_in_one_cell_fail_closed(self):
        rows = [["CONTRATOS 09/2025 substitui 10/2025", "12.226.306/0001-40"]]
        keys = {"contract_number": "09/2025", "cnpj": "12226306000140"}

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_resolve_end_to_end_uses_fail_closed_candidate_policy_without_network(self):
        landing = b'''<html><body><form method="post" action="/contracts">
        <label>Ano de Pesquisa <input name="ano_ano" type="text"></label>
        <label>Numero do Contrato <input name="numero" type="text"></label>
        <input name="bprocessa" type="submit" value="Pesquisar">
        </form></body></html>'''
        result = b'''<html><body><table>
        <tr><th>Contrato</th><th>Fornecedor</th><th>CNPJ</th></tr>
        <tr><td>Contrato 09/2025 - objeto X</td><td>OUTRA EMPRESA</td><td>12.226.306/0001-40</td></tr>
        </table></body></html>'''

        class SyntheticResolver(LimeiraContractsResolver):
            def __init__(self):
                super().__init__(search_url="https://example.test/search")
                self.calls = 0

            def _request(self, url, *, method="GET", params=None):
                self.calls += 1
                body = landing if self.calls == 1 else result
                return body, {
                    "url": url,
                    "http_status": 200,
                    "content_type": "text/html; charset=utf-8",
                }

        task = {
            "task_id": "RECTASK_SYNTHETIC_TASK081",
            "target_source": "LIMEIRA_CONTRATOS",
            "match_keys": {
                "year": 2025,
                "contract_number": "09/2025",
                "cnpj": "12226306000140",
                "contractor": "EMPRESA ESPERADA",
            },
        }
        resolver = SyntheticResolver()

        resolved = resolver.resolve(task)

        self.assertEqual("NO_MATCH", resolved.status)
        self.assertEqual([], resolved.candidates)
        self.assertEqual(2, resolver.calls)

    def test_ci_dom_binding_gate_explicitly_supports_dry_run_flag(self):
        path = ROOT / "scripts/github_siope_official_olinda_api_application_dom_structural_binding_diagnostics_gate.py"
        text = path.read_text(encoding="utf-8")

        self.assertIn('parser.add_argument("--dry-run", action="store_true")', text)
        self.assertIn("run_gate(dry=args.dry_run)", text)


if __name__ == "__main__":
    unittest.main()
