import csv
import io
import unittest

from scripts.task185_live_accounting_gate import _build_stage_c


GENERATED_AT = "2026-09-06T09:15:00-03:00"
SOFTWARE_VERSION = "0.8.0"


def _csv_payload():
    headers = [
        "tp_despesa",
        "nr_empenho",
        "identificador_despesa",
        "ds_despesa",
        "dt_emissao_despesa",
        "vl_despesa",
        "ds_funcao_governo",
        "ds_subfuncao_governo",
        "cd_programa",
        "ds_programa",
        "cd_acao",
        "ds_acao",
        "ds_fonte_recurso",
        "ds_cd_aplicacao_fixo",
        "ds_modalidade_lic",
        "ds_elemento",
        "historico_despesa",
    ]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=headers, delimiter=";", lineterminator="\n")
    writer.writeheader()
    for stage in ("Empenhado", "Liquidado", "Pago"):
        writer.writerow(
            {
                "tp_despesa": stage,
                "nr_empenho": "1234",
                "identificador_despesa": f"EXP-{stage}",
                "ds_despesa": "Manutenção de escola",
                "dt_emissao_despesa": "2026-08-01",
                "vl_despesa": "100,00",
                "ds_funcao_governo": "Educação",
                "ds_subfuncao_governo": "Ensino Fundamental",
                "cd_programa": "2001",
                "ds_programa": "Educação",
                "cd_acao": "2010",
                "ds_acao": "Manutenção",
                "ds_fonte_recurso": "Tesouro",
                "ds_cd_aplicacao_fixo": "2200000",
                "ds_modalidade_lic": "Pregão",
                "ds_elemento": "Serviços",
                "historico_despesa": "Fixture sintética somente para teste offline.",
            }
        )
    return out.getvalue().encode("utf-8")


class TestTask185LiveGateOffline(unittest.TestCase):
    def test_stage_c_preserves_accounting_stages_without_remote_effects(self):
        payload = _csv_payload()
        inspection = {
            "csv_encoding": "utf-8",
            "csv_delimiter": ";",
            "record_count": 3,
            "csv_sha256": "a" * 64,
        }
        summary, ledger = _build_stage_c(
            payload,
            inspection,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(summary["source_row_count"], 3)
        self.assertEqual(summary["normalized_observation_count"], 3)
        self.assertEqual(summary["accounting_ledger"]["row_count"], 3)
        self.assertEqual(
            summary["accounting_ledger"]["stage_counts"],
            {"COMMITMENT": 1, "LIQUIDATION": 1, "PAYMENT": 1},
        )
        self.assertEqual(summary["answerability"]["question_count"], 38)
        self.assertFalse(summary["guards"]["weak_join_can_create_identity"])
        self.assertEqual(summary["remote_effects"]["stage_c_source_network"], 0)
        self.assertEqual(summary["remote_effects"]["stage_c_drive_write"], 0)
        self.assertEqual(ledger["row_count"], 3)
        self.assertEqual(ledger["product_schema"], "ACCOUNTING_LEDGER_V1")


if __name__ == "__main__":
    unittest.main()
