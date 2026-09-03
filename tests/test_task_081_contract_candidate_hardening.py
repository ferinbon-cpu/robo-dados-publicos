import unittest

from robo_dados_publicos.reconciliation.resolvers import LimeiraContractsResolver


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

    def test_matching_contract_and_expected_cnpj_is_candidate(self):
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
        self.assertIn("CONTRACT_STEM_PLUS_YEAR", candidates[0]["match_signals"])
        self.assertIn("CNPJ", candidates[0]["match_signals"])

    def test_cnpj_is_not_constructed_across_neighboring_cells(self):
        rows = [["9/2025", "12226306", "000140"]]
        keys = {
            "year": 2025,
            "contract_number": "09/2025.",
            "cnpj": "12226306000140",
        }

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))

    def test_contract_only_behavior_remains_available_when_no_stronger_key_exists(self):
        rows = [["CONTRATOS", "51/2025", "2025", "Fornecedor sem CNPJ publicado"]]
        keys = {"year": 2025, "contract_number": "51/2025"}

        candidates = LimeiraContractsResolver._candidate_rows(rows, keys)

        self.assertEqual(1, len(candidates))
        self.assertIn("CONTRACT_FULL", candidates[0]["match_signals"])

    def test_supplier_mismatch_blocks_contract_collision_when_cnpj_absent(self):
        rows = [["CONTRATOS", "51/2025", "2025", "OUTRO FORNECEDOR"]]
        keys = {
            "year": 2025,
            "contract_number": "51/2025",
            "contractor": "FORNECEDOR ESPERADO",
        }

        self.assertEqual([], LimeiraContractsResolver._candidate_rows(rows, keys))


if __name__ == "__main__":
    unittest.main()
