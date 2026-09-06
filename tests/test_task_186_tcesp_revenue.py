import json
import unittest
from pathlib import Path

from robo_dados_publicos.accounting.tcesp_revenue import (
    Task186RevenueStop,
    normalize_revenue_row,
    parse_csv_bytes,
)
from robo_dados_publicos.analytics.observatory_knowledge_pack import (
    question_answerability,
)
from robo_dados_publicos.analytics.observatory_products import build_revenue_ledger
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_186_TCESP_REVENUE_LEDGER_0.8.0.json"
TASK185_EVIDENCE = ROOT / "docs/evidence/TASK_185_MANUAL_JSON_LEDGER_MATERIALIZATION_0.8.0.json"
GENERATED_AT = "2026-09-06T14:05:02.574464+00:00"
SOFTWARE_VERSION = "0.8.0"


HEADERS = [
    "id_rec_arrec_detalhe","ano_exercicio","ds_municipio","ds_orgao",
    "mes_referencia","mes_ref_extenso","ds_poder","ds_fonte_recurso",
    "ds_cd_aplicacao_fixo","ds_cd_aplicacao_variavel","ds_categoria",
    "ds_subcategoria","ds_fonte","ds_d1","ds_dd2","ds_d3","ds_tipo",
    "vl_arrecadacao",
]


def row(month=1, rid="100", value="182462,26", *, eti=False, interest=False):
    return {
        "id_rec_arrec_detalhe": str(rid),
        "ano_exercicio": "2026",
        "ds_municipio": "Limeira",
        "ds_orgao": "PREFEITURA MUNICIPAL DE LIMEIRA",
        "mes_referencia": str(month),
        "mes_ref_extenso": ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho"][month],
        "ds_poder": "EXECUTIVO",
        "ds_fonte_recurso": "05 - TRANSFERÊNCIAS E CONVÊNIOS FEDERAIS-VINCULADOS",
        "ds_cd_aplicacao_fixo": "260 - EDUCAÇÃO - FUNDEB - RECURSOS PRÓPRIOS",
        "ds_cd_aplicacao_variavel": "70 - FUNDEB - Fomento a matrículas ETI" if eti else "00 - CÓDIGO DE APLICAÇÃO NÃO CONTÉM/INFORMOU PARTE VARIÁVEL",
        "ds_categoria": "10000000 - Receitas Correntes",
        "ds_subcategoria": "17000000 - Transferências Correntes",
        "ds_fonte": "17100000 - Transferências da União",
        "ds_d1": "17150000 - Transferências de Outras Instituições Públicas",
        "ds_dd2": "13210100 - Remuneração de Depósitos Bancários" if interest else (
            "17155300 - Complementação da União ao Fundeb para matrículas em tempo integral"
            if eti else "17515000 - Transferências do FUNDEB"
        ),
        "ds_d3": "13210110 - Remuneração de Depósitos Bancários - Geral" if interest else "17515000 - Transferências do FUNDEB",
        "ds_tipo": "13210111 - Remuneração - Principal" if interest else "17515001 - Transferências do FUNDEB - Principal",
        "vl_arrecadacao": value,
    }


def csv_bytes(rows):
    lines = [";".join(HEADERS)]
    for r in rows:
        lines.append(";".join(r[h] for h in HEADERS))
    return ("\r\n".join(lines) + "\r\n").encode("cp1252")


class TestTask186TcespRevenue(unittest.TestCase):
    def test_parse_accepts_all_seven_months_and_negative_adjustment(self):
        source = [row(m, str(100 + m), "-0,01" if m == 4 else "10,00") for m in range(1, 8)]
        got = parse_csv_bytes(csv_bytes(source))
        self.assertEqual(len(got), 7)
        self.assertEqual(got[3]["vl_arrecadacao"], "-0,01")

    def test_duplicate_official_id_fails_closed(self):
        source = [row(m, "100" if m in {1, 2} else str(100 + m)) for m in range(1, 8)]
        with self.assertRaisesRegex(Task186RevenueStop, "TASK186_REVENUE_DUPLICATE_ID"):
            parse_csv_bytes(csv_bytes(source))

    def test_eti_transfer_and_financial_remuneration_are_distinct(self):
        transfer = normalize_revenue_row(row(1, "1", "182462,26", eti=True))
        interest = normalize_revenue_row(row(3, "2", "22641,08", eti=True, interest=True))
        self.assertTrue(transfer["eti_classification"])
        self.assertTrue(transfer["eti_direct_transfer"])
        self.assertFalse(transfer["eti_financial_remuneration"])
        self.assertTrue(interest["eti_classification"])
        self.assertFalse(interest["eti_direct_transfer"])
        self.assertTrue(interest["eti_financial_remuneration"])

    def test_revenue_ledger_preserves_official_identity_and_capabilities(self):
        observations = [
            normalize_revenue_row(row(1, "1", "182462,26", eti=True)),
            normalize_revenue_row(row(3, "2", "22641,08", eti=True, interest=True)),
        ]
        product = build_revenue_ledger(
            observations,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(product["row_count"], 2)
        self.assertIn("OFFICIAL_RECORD_ID", product["capabilities"])
        self.assertIn("FUNDING_SOURCE", product["capabilities"])
        self.assertIn("APPLICATION_VARIABLE", product["capabilities"])
        self.assertIn("ETI_REVENUE_CLASSIFICATION", product["capabilities"])
        self.assertEqual(product["rows"][0]["source_family"], "TCE_SP_REVENUES")

    def test_real_revenue_capabilities_make_fin_q3_answerable(self):
        bundle = build_task184_bundle(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        observations = [
            normalize_revenue_row(row(1, "1", "19807535,04")),
            normalize_revenue_row(row(1, "2", "182462,26", eti=True)),
        ]
        revenue = build_revenue_ledger(
            observations,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        substantive = {
            k: v for k, v in bundle["products"].items()
            if k != "QUERY_PRODUCT_CATALOG"
        }
        products = _with_catalog(
            {**substantive, "REVENUE_LEDGER": revenue},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        report = question_answerability(products)
        by_id = {x["question_id"]: x for x in report["questions"]}
        self.assertEqual(by_id["FIN_Q3"]["status"], "MATERIALIZED_ANSWERABLE")


    def test_canonical_evidence_recomputes_full_38_question_gain(self):
        e = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        t185 = json.loads(TASK185_EVIDENCE.read_text(encoding="utf-8"))
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
            "snapshot_id": t185["accounting_ledger"]["snapshot_id"],
            "content_sha256": t185["accounting_ledger"]["content_sha256"],
            "row_count": t185["accounting_ledger"]["row_count"],
            "generated_at": GENERATED_AT,
            "software_version": SOFTWARE_VERSION,
            "rows": [],
            "capabilities": t185["accounting_ledger"]["capabilities"],
        }
        revenue = {
            "product_name": "REVENUE_LEDGER",
            "product_schema": e["revenue_ledger"]["product_schema"],
            "snapshot_id": e["revenue_ledger"]["snapshot_id"],
            "content_sha256": e["revenue_ledger"]["content_sha256"],
            "row_count": e["revenue_ledger"]["row_count"],
            "generated_at": GENERATED_AT,
            "software_version": SOFTWARE_VERSION,
            "rows": [],
            "capabilities": e["revenue_ledger"]["capabilities"],
        }
        before_products = _with_catalog(
            {**substantive, "ACCOUNTING_LEDGER": accounting},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        after_products = _with_catalog(
            {**substantive, "ACCOUNTING_LEDGER": accounting, "REVENUE_LEDGER": revenue},
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        before = question_answerability(before_products)
        after = question_answerability(after_products)
        self.assertEqual(before["status_counts"], e["answerability"]["before_status_counts"])
        self.assertEqual(after["status_counts"], e["answerability"]["after_status_counts"])
        changed = [
            q["question_id"]
            for q in after["questions"]
            if q["status"] != next(
                b["status"] for b in before["questions"]
                if b["question_id"] == q["question_id"]
            )
        ]
        self.assertEqual(changed, ["FIN_Q3"])
        by_id = {x["question_id"]: x for x in after["questions"]}
        self.assertEqual(by_id["FIN_Q3"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(e["eti"]["direct_transfer_net_brl"], "3606418.18")
        self.assertEqual(e["eti"]["financial_remuneration_net_brl"], "85724.69")
        self.assertFalse(e["source"]["august_present_in_snapshot"])


if __name__ == "__main__":
    unittest.main()
