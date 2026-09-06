import json
import unittest

from robo_dados_publicos.accounting.tcesp_json_api import (
    Task185JsonStop,
    normalize_json_expense_row,
    source_capabilities,
    validate_payload,
)


class TestTask185TcespJsonApi(unittest.TestCase):
    def sample(self, event="Empenhado", month="Janeiro"):
        return {
            "orgao":"PREFEITURA MUNICIPAL DE LIMEIRA",
            "mes":month,
            "evento":event,
            "nr_empenho":"100-2026",
            "id_fornecedor":"CNPJ - PESSOA JURÍDICA - 45132495000140",
            "nm_fornecedor":"FORNECEDOR TESTE",
            "dt_emissao_despesa":"05/01/2026",
            "vl_despesa":"123,45",
        }

    def test_direct_array_schema_and_hash(self):
        payload = json.dumps([self.sample()], ensure_ascii=False).encode("utf-8")
        rows, meta = validate_payload(payload, month=1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(meta["row_count"], 1)
        self.assertEqual(len(meta["body_sha256"]), 64)

    def test_missing_field_stops(self):
        row = self.sample()
        del row["vl_despesa"]
        with self.assertRaises(Task185JsonStop):
            validate_payload(json.dumps([row]).encode("utf-8"), month=1)

    def test_wrong_month_content_stops(self):
        payload = json.dumps([self.sample(month="Fevereiro")]).encode("utf-8")
        with self.assertRaises(Task185JsonStop):
            validate_payload(payload, month=1)

    def test_normalization_preserves_supplier_but_not_programmatic_claim(self):
        row = self.sample(event="Valor Pago")
        obs = normalize_json_expense_row(row, source_body_sha256="a"*64, month=1)
        self.assertEqual(obs["stage"], "PAYMENT")
        self.assertEqual(obs["amount_brl"], "123.45")
        self.assertEqual(obs["supplier_name"], "FORNECEDOR TESTE")
        self.assertIsNone(obs["programmatic_dimensions"]["program_code"])
        self.assertFalse(obs["policy_identity_proven"])

    def test_reinforcement_is_commitment_modifier(self):
        obs = normalize_json_expense_row(self.sample(event="Reforço"), source_body_sha256="b"*64, month=1)
        self.assertEqual(obs["stage"], "COMMITMENT")
        self.assertEqual(obs["stage_modifier"], "REINFORCEMENT")

    def test_capabilities_are_stage_specific_and_do_not_invent_classification(self):
        observations = [
            normalize_json_expense_row(self.sample(event=e), source_body_sha256=str(i)*64, month=1)
            for i,e in enumerate(["Empenhado","Valor Liquidado","Valor Pago"], start=1)
        ]
        caps = source_capabilities(observations)
        self.assertIn("COMMITMENT_AMOUNTS", caps)
        self.assertIn("LIQUIDATION_AMOUNTS", caps)
        self.assertIn("PAYMENT_AMOUNTS", caps)
        self.assertIn("SUPPLIER_AMOUNT", caps)
        self.assertNotIn("PROGRAMMATIC_CLASSIFICATION", caps)
        self.assertNotIn("RESTS_PAYABLE", caps)


if __name__ == "__main__":
    unittest.main()
