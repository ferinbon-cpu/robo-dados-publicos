import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from robo_dados_publicos.manual_ingest.mde_fundeb import (
    F02IngestStop,
    F02SourceContract,
    classify_f02_text,
    validate_f02_source_bytes,
)
from robo_dados_publicos.manual_ingest.mde_fundeb_parser import (
    load_f02_ingest_plan,
    normalize_f02_document,
    parse_fundeb_local,
    parse_mde_25_local,
    parse_rreo_mde,
    reconcile_f02,
)


RREO_TEXT = """
MUNICIPIO DE LIMEIRA
Relatorio Resumido da Execucao Orcamentaria
Demonstrativo das Receitas e Despesas com Manutencao e Desenvolvimento do Ensino - MDE
Periodo de Referencia: JANEIRO a ABRIL 2026 / BIMESTRE: MARCO-ABRIL
RREO - ANEXO 8 (LDB, art.72)
3 - TOTAL DA RECEITA RESULTANTE DE IMPOSTOS 1.395.706.204,43 477.974.870,08
4 - TOTAL DESTINADO AO FUNDEB-20% 152.655.663,02 56.621.833,68
25% DE ((1.1) 196.270.888,07 62.871.883,83
6 - TOTAL DAS RECEITAS DO FUNDEB RECEBIDAS 204.310.244,38 70.620.568,12
9 - TOTAL DOS RECURSOS DO FUNDEB DISPONIVEIS PARA UTILIZACAO (6 + 8) 71.668.089,20
11- TOTAL DAS DESPESAS CUSTEADAS C/RECURSOS DO FUNDEB
RECEBIDAS NO EXERCICIO 129.124.321,63 62.841.461,94 43.847.432,77
12- Total das Despesas do FUNDEB com Profissionais da
Educacao Basica 128.900.343,54 62.617.483,85 43.623.454,68
15- Minimo de 70% do FUNDEB na Remuneracao dos Profissionais da Educacao Basica 49.434.397,68 62.617.483,85 62.617.483,85 88,67
29- APLICACAO EM MDE SOBRE A RECEITA RESULTANTE DE IMPOSTOS 119.493.717,52 115.982.840,60 24,27
"""

FUNDEB_TEXT = """
Prefeitura Municipal de Limeira
APLICACAO COM RECURSOS DO FUNDEB
22/05/2026 POSICAO EM 30/04/2026 Pagina 1
RECEITA DO FUNDEB RETENCOES AO FUNDEB
Principal (I) 198.489.969,37 69.842.340,65 152.259.900,22 56.621.833,48
TOTAL (I+II+III+IV+V+VI+VII+VIII+IX+X) 204.319.468,70 70.662.083,95 69.842.340,65 56.621.833,48
APLICACAO MINIMA - PROFISSIONAIS DA EDUCACAO BASICA
TOTAL  (min. 90%)** 129.124.321,63 182,73 62.841.461,94 88,93 43.847.432,77 62,05
PROFISSIONAIS DA EDUCACAO BASICA* - exceto
Complementacao da Uniao VAAR (min. 70%) 128.900.343,54 182,42 62.617.483,85 88,62 43.623.454,68 61,74
"""

MDE25_TEXT = """
Prefeitura Municipal de Limeira
APLICACAO DOS RECURSOS PROPRIOS EM ENSINO - POR DATA
22/05/2026 POSICAO EM 30/04/2026 Pagina 1
RECEITA DE IMPOSTOS APLICACAO MINIMA CONSTITUCIONAL
Total 1.393.727.390,62 477.974.870,08
Retencoes ao FUNDEB 152.259.900,22 56.621.833,48
DESPESAS PROPRIAS EM EDUCACAO
DESPESAS TOTAIS
TOTAL 192.993.733,99 40,38 111.043.318,30 23,23 99.563.903,63 20,83
DESPESAS LIQUIDAS
Ensino Fundamental 78.323.066,84 16,39 32.754.512,39 6,85 24.995.305,53 5,23
TOTAL 192.796.668,89 40,34 110.846.253,20 23,19 86.592.437,82 18,12
"""


def contract(family):
    return F02SourceContract(
        source_id=f"TEST_{family}",
        family=family,
        role="TEST",
        drive_file_id=f"drive-{family}",
        expected_sha256="0" * 64,
        expected_bytes=1,
        expected_pages=1,
    )


class ManualSupervisedIngestF02Tests(unittest.TestCase):
    def test_classifier_exactly_one_family(self):
        for text, family in (
            (RREO_TEXT, "RREO_MDE"),
            (FUNDEB_TEXT, "FUNDEB_LOCAL"),
            (MDE25_TEXT, "MDE_25_LOCAL"),
        ):
            with self.subTest(family=family):
                self.assertEqual(classify_f02_text(text), family)

    def test_classifier_unknown_and_ambiguous_are_stop(self):
        with self.assertRaisesRegex(F02IngestStop, "UNKNOWN_DOCUMENT"):
            classify_f02_text("documento sem assinatura conhecida")
        with self.assertRaisesRegex(F02IngestStop, "AMBIGUOUS_DOCUMENT"):
            classify_f02_text(FUNDEB_TEXT + "\n" + MDE25_TEXT)

    def test_rreo_parser_pins_official_values(self):
        record = parse_rreo_mde(RREO_TEXT)
        self.assertEqual(record["period_end"], "2026-04-30")
        self.assertEqual(record["authority"], "OFFICIAL_MDE_PRIMARY")
        self.assertEqual(record["metrics"]["tax_revenue_realized"], "477974870.08")
        self.assertEqual(record["metrics"]["fundeb_limit_expense_liquidated"], "62841461.94")
        self.assertEqual(record["metrics"]["fundeb_professionals_percent"], "88.67")
        self.assertEqual(record["metrics"]["mde_percent"], "24.27")

    def test_local_parsers_preserve_methodology_specific_percentages(self):
        fundeb = parse_fundeb_local(FUNDEB_TEXT)
        mde25 = parse_mde_25_local(MDE25_TEXT)
        self.assertEqual(fundeb["period_end"], "2026-04-30")
        self.assertEqual(mde25["period_end"], "2026-04-30")
        self.assertEqual(fundeb["metrics"]["fundeb_application_liquidated_percent"], "88.93")
        self.assertEqual(fundeb["metrics"]["fundeb_professionals_liquidated_percent_local"], "88.62")
        self.assertEqual(mde25["metrics"]["education_expense_liquidated_percent"], "23.23")
        self.assertEqual(mde25["metrics"]["education_net_expense_liquidated_percent"], "23.19")

    def test_normalizer_rejects_contract_family_mismatch(self):
        with self.assertRaisesRegex(F02IngestStop, "CONTRACT_MISMATCH"):
            normalize_f02_document(contract("RREO_MDE"), FUNDEB_TEXT)

    def test_reconciliation_preserves_exact_matches_and_methodology_differences(self):
        result = reconcile_f02([
            parse_rreo_mde(RREO_TEXT),
            parse_fundeb_local(FUNDEB_TEXT),
            parse_mde_25_local(MDE25_TEXT),
        ])
        self.assertEqual(result["status"], "PASS_F02_RECONCILIATION")
        self.assertTrue(all(result["exact_checks"].values()))
        self.assertEqual(
            result["methodology_differences"]["fundeb_retained_local_minus_rreo_destined"],
            "-0.20",
        )
        self.assertEqual(
            result["methodology_differences"]["mde_liquidated_percent_local_minus_rreo_official"],
            "-1.04",
        )
        self.assertEqual(result["authority_rule"], "RREO_MDE_FOR_OFFICIAL_MDE_CLAIMS")
        self.assertFalse(result["promotion"]["gold_authorized"])

    def test_reconciliation_period_mismatch_is_stop(self):
        records = [
            parse_rreo_mde(RREO_TEXT),
            parse_fundeb_local(FUNDEB_TEXT),
            parse_mde_25_local(MDE25_TEXT),
        ]
        records[2]["period_end"] = "2026-05-31"
        with self.assertRaisesRegex(F02IngestStop, "PERIOD_MISMATCH"):
            reconcile_f02(records)

    def test_reconciliation_expected_exact_mismatch_is_stop(self):
        records = [
            parse_rreo_mde(RREO_TEXT),
            parse_fundeb_local(FUNDEB_TEXT),
            parse_mde_25_local(MDE25_TEXT),
        ]
        records[1]["metrics"]["fundeb_professionals_liquidated"] = "1.00"
        with self.assertRaisesRegex(F02IngestStop, "EXPECTED_EXACT_MISMATCH"):
            reconcile_f02(records)

    def test_immutable_validator_checks_hash_bytes_pages_and_text(self):
        payload = b"abc"
        pinned = F02SourceContract(
            source_id="X",
            family="RREO_MDE",
            role="TEST",
            drive_file_id="drive-x",
            expected_sha256=hashlib.sha256(payload).hexdigest(),
            expected_bytes=3,
            expected_pages=7,
        )
        fake_pdf = {
            "pages": 7,
            "text_pages": 7,
            "text_chars": 10,
            "has_text_layer": True,
            "text": RREO_TEXT,
        }
        with patch(
            "robo_dados_publicos.manual_ingest.mde_fundeb.inspect_f02_pdf",
            return_value=fake_pdf,
        ):
            result = validate_f02_source_bytes(pinned, payload)
            self.assertEqual(result["status"], "PASS_F02_SOURCE_BYTES_VERIFIED")
            bad = F02SourceContract(
                source_id="X",
                family="RREO_MDE",
                role="TEST",
                drive_file_id="drive-x",
                expected_sha256="0" * 64,
                expected_bytes=3,
                expected_pages=7,
            )
            with self.assertRaisesRegex(F02IngestStop, "IMMUTABLE_MISMATCH"):
                validate_f02_source_bytes(bad, payload)

    def test_plan_forbids_promotion(self):
        config = {
            "mode": "MANUAL_SUPERVISED_INGEST",
            "source_precedence": {
                "mde_official_claim": "RREO_MDE",
                "fundeb_local_report": "LOCAL_MONITORING_PERIOD_MATCH_REQUIRED",
                "mde_25_local_report": "AUXILIARY_MONITORING_NOT_SUBSTITUTE_FOR_RREO",
            },
            "sources": [
                {
                    "source_id": f"S{i}",
                    "family": family,
                    "role": "TEST",
                    "drive_file_id": f"D{i}",
                    "expected_sha256": str(i) * 64,
                    "expected_bytes": i + 1,
                    "expected_pages": 1,
                }
                for i, family in enumerate(
                    ("RREO_MDE", "FUNDEB_LOCAL", "MDE_25_LOCAL"), start=1
                )
            ],
            "promotion": {
                "bronze_mutation_authorized_by_this_contract": False,
                "silver_authorized_by_this_contract": False,
                "gold_authorized": False,
                "serving_authorized": False,
                "site_mutation_authorized": False,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f02.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            self.assertEqual(len(load_f02_ingest_plan(str(path))["contracts"]), 3)

            config["promotion"]["silver_authorized_by_this_contract"] = True
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(F02IngestStop, "UNAUTHORIZED_PROMOTION"):
                load_f02_ingest_plan(str(path))


if __name__ == "__main__":
    unittest.main()
