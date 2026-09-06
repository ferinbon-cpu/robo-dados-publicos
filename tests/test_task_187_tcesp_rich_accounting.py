import json
import unittest
from pathlib import Path

from robo_dados_publicos.accounting.tcesp_rich_expenses import (
    Task187RichExpenseStop,
    normalize_rich_expense_row,
    normalize_stage,
    parse_csv_bytes,
)
from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.observatory_products import build_accounting_ledger
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle

ROOT = Path(__file__).resolve().parents[1]
TASK185 = ROOT / "docs/evidence/TASK_185_MANUAL_JSON_LEDGER_MATERIALIZATION_0.8.0.json"
TASK186 = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
GENERATED_AT = "2026-09-06T14:28:02.336990+00:00"
SOFTWARE_VERSION = "0.8.0"

HEADERS = [
    "id_despesa_detalhe","ano_exercicio","ds_municipio","ds_orgao",
    "mes_referencia","mes_ref_extenso","tp_despesa","nr_empenho",
    "identificador_despesa","ds_despesa","dt_emissao_despesa","vl_despesa",
    "ds_funcao_governo","ds_subfuncao_governo","cd_programa","ds_programa",
    "cd_acao","ds_acao","ds_fonte_recurso","ds_cd_aplicacao_fixo",
    "ds_modalidade_lic","ds_elemento","historico_despesa",
]


def row(month=1, rid="100", stage="Empenhado", *, element="33903000 - MATERIAL DE CONSUMO"):
    return {
        "id_despesa_detalhe": str(rid),
        "ano_exercicio": "2026",
        "ds_municipio": "Limeira",
        "ds_orgao": "PREFEITURA MUNICIPAL DE LIMEIRA",
        "mes_referencia": str(month),
        "mes_ref_extenso": ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho"][month],
        "tp_despesa": stage,
        "nr_empenho": "1234-2026",
        "identificador_despesa": "CNPJ - PESSOA JURÍDICA - 12345678000190",
        "ds_despesa": "FORNECEDOR TESTE LTDA",
        "dt_emissao_despesa": "02/01/2026",
        "vl_despesa": "1234,56",
        "ds_funcao_governo": "EDUCAÇÃO",
        "ds_subfuncao_governo": "ENSINO FUNDAMENTAL",
        "cd_programa": "2001",
        "ds_programa": "EDUCACAO QUE INCLUI E TRANSFORMA VIDAS",
        "cd_acao": "2680",
        "ds_acao": "FUNCIONAMENTO DO ENSINO FUNDAMENTAL",
        "ds_fonte_recurso": "TESOURO",
        "ds_cd_aplicacao_fixo": "0220 - ENSINO FUNDAMENTAL",
        "ds_modalidade_lic": "PREGÃO ELETRÔNICO",
        "ds_elemento": element,
        "historico_despesa": "AQUISICAO DE MATERIAL.",
    }


def csv_bytes(rows):
    lines = [";".join(HEADERS)]
    for item in rows:
        lines.append(";".join(item[h] for h in HEADERS))
    return ("\r\n".join(lines) + "\r\n").encode("cp1252")


class TestTask187TcespRichAccounting(unittest.TestCase):
    def test_stage_semantics_preserve_reinforcement_as_commitment_modifier(self):
        self.assertEqual(normalize_stage("Empenhado"), ("COMMITMENT", None))
        self.assertEqual(normalize_stage("Reforço"), ("COMMITMENT", "REINFORCEMENT"))
        self.assertEqual(normalize_stage("Valor Liquidado"), ("LIQUIDATION", None))
        self.assertEqual(normalize_stage("Valor Pago"), ("PAYMENT", None))
        self.assertEqual(normalize_stage("Anulação"), ("REVERSAL", None))

    def test_official_detail_id_is_record_identity_not_supplier_identity(self):
        got = normalize_rich_expense_row(row())
        self.assertEqual(got["official_record_id"], "100")
        self.assertEqual(got["transaction_keys"]["source_expense_identifier"], "100")
        self.assertEqual(
            got["supplier_public_id"],
            "CNPJ - PESSOA JURÍDICA - 12345678000190",
        )
        self.assertNotEqual(
            got["transaction_keys"]["source_expense_identifier"],
            got["supplier_public_id"],
        )

    def test_programmatic_dimensions_are_real_but_do_not_prove_policy_identity(self):
        got = normalize_rich_expense_row(row())
        dims = got["programmatic_dimensions"]
        self.assertEqual(dims["function"], "EDUCAÇÃO")
        self.assertEqual(dims["program_code"], "2001")
        self.assertEqual(dims["action_code"], "2680")
        self.assertEqual(dims["funding_source"], "TESOURO")
        self.assertEqual(dims["expense_element"], "33903000 - MATERIAL DE CONSUMO")
        self.assertIn("EDUCATION", got["policy_domain_hints"])
        self.assertFalse(got["policy_identity_proven"])
        self.assertFalse(got["financial_policy_identity_proven"])
        self.assertIsNone(got["event_date"])
        self.assertEqual(got["expense_issue_date"], "02/01/2026")

    def test_parser_accepts_only_two_known_empty_expense_elements_and_seven_months(self):
        source = [
            row(month, str(100 + month), element="" if month == 4 else "33903000 - MATERIAL DE CONSUMO")
            for month in range(1, 8)
        ]
        # Structural parser accepts the field as nullable; the real-source
        # contract pins exactly two observed empty rows in evidence.
        got = parse_csv_bytes(csv_bytes(source))
        self.assertEqual(len(got), 7)

    def test_duplicate_official_record_id_fails_closed(self):
        source = [
            row(month, "100" if month in {1, 2} else str(100 + month))
            for month in range(1, 8)
        ]
        with self.assertRaisesRegex(Task187RichExpenseStop, "TASK187_DUPLICATE_OFFICIAL_ID"):
            parse_csv_bytes(csv_bytes(source))

    def test_rich_ledger_exposes_classification_capabilities_without_rests_payable(self):
        observations = [
            normalize_rich_expense_row(row(1, "1", "Empenhado")),
            normalize_rich_expense_row(row(2, "2", "Valor Liquidado")),
            normalize_rich_expense_row(row(3, "3", "Valor Pago")),
            normalize_rich_expense_row(row(4, "4", "Anulação")),
        ]
        product = build_accounting_ledger(
            observations,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        for capability in (
            "EDUCATION_CLASSIFICATION",
            "PROGRAMMATIC_CLASSIFICATION",
            "FUNDING_SOURCE_APPLICATION",
            "EXPENSE_ELEMENT",
            "SUPPLIER_AMOUNT",
            "EVENT_MONTH",
            "EXPENSE_ISSUE_DATE",
        ):
            self.assertIn(capability, product["capabilities"])
        self.assertNotIn("EVENT_DATE", product["capabilities"])
        self.assertNotIn("RESTS_PAYABLE", product["capabilities"])

    def test_rich_capabilities_close_acc_q2_without_overpromoting_fin_q1_or_rests_payable(self):
        t185 = json.loads(TASK185.read_text(encoding="utf-8"))
        t186 = json.loads(TASK186.read_text(encoding="utf-8"))
        bundle = build_task184_bundle(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        substantive = {
            k: v for k, v in bundle["products"].items()
            if k != "QUERY_PRODUCT_CATALOG"
        }
        accounting = {
            "product_name": "ACCOUNTING_LEDGER",
            "product_schema": "ACCOUNTING_LEDGER_V1",
            "snapshot_id": "RICH_FIXTURE",
            "content_sha256": "a" * 64,
            "row_count": 39779,
            "generated_at": GENERATED_AT,
            "software_version": SOFTWARE_VERSION,
            "rows": [],
            "capabilities": [
                "COMMITMENT_AMOUNTS","COMMITMENT_NUMBER","EDUCATION_CLASSIFICATION",
                "EVENT_MONTH","EXPENSE_ELEMENT","EXPENSE_ISSUE_DATE",
                "FUNDING_SOURCE_APPLICATION","LIQUIDATION_AMOUNTS","PAYMENT_AMOUNTS",
                "PROGRAMMATIC_CLASSIFICATION","REVERSAL_EVENTS","SOURCE_DESCRIPTION",
                "SUPPLIER_AMOUNT",
            ],
            "observed_stages": ["COMMITMENT","LIQUIDATION","PAYMENT","REVERSAL"],
        }
        revenue = {
            "product_name": "REVENUE_LEDGER",
            "product_schema": t186["revenue_ledger"]["product_schema"],
            "snapshot_id": t186["revenue_ledger"]["snapshot_id"],
            "content_sha256": t186["revenue_ledger"]["content_sha256"],
            "row_count": t186["revenue_ledger"]["row_count"],
            "generated_at": GENERATED_AT,
            "software_version": SOFTWARE_VERSION,
            "rows": [],
            "capabilities": t186["revenue_ledger"]["capabilities"],
        }
        products = _with_catalog(
            {**substantive, "ACCOUNTING_LEDGER": accounting, "REVENUE_LEDGER": revenue},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        report = question_answerability(products)
        by_id = {x["question_id"]: x for x in report["questions"]}
        self.assertEqual(by_id["FIN_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["ACC_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["ACC_Q3"]["status"], "MATERIALIZED_PARTIAL")


if __name__ == "__main__":
    unittest.main()
