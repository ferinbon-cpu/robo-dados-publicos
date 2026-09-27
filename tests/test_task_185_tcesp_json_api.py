import json
import unittest

from robo_dados_publicos.accounting.tcesp_json_api import (
    Task185JsonStop,
    normalize_json_expense_row,
    source_capabilities,
    validate_payload,
)
from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.observatory_products import build_accounting_ledger
from robo_dados_publicos.analytics.task184_local_bundle import _with_catalog, build_task184_bundle


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
        self.assertEqual(obs["entity_name"], "PREFEITURA MUNICIPAL DE LIMEIRA")
        self.assertIsNone(obs["event_date"])
        self.assertEqual(obs["expense_issue_date"], "05/01/2026")
        self.assertEqual(obs["event_month"], 1)
        self.assertIsNone(obs["programmatic_dimensions"]["program_code"])
        self.assertFalse(obs["policy_identity_proven"])

    def test_contract_pins_180_second_timeout(self):
        from robo_dados_publicos.accounting.tcesp_json_api import load_contract
        self.assertEqual(load_contract()["source"]["network_timeout_seconds"], 180)

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
        self.assertIn("EXPENSE_ISSUE_DATE", caps)
        self.assertIn("EVENT_MONTH", caps)
        self.assertNotIn("EVENT_DATE", caps)
        self.assertNotIn("PROGRAMMATIC_CLASSIFICATION", caps)
        self.assertNotIn("RESTS_PAYABLE", caps)

    def test_json_ledger_is_capability_aware_for_accounting_questions(self):
        observations = [
            normalize_json_expense_row(self.sample(event=e), source_body_sha256=(str(i) * 64)[:64], month=1)
            for i,e in enumerate(["Empenhado","Valor Liquidado","Valor Pago"], start=1)
        ]
        ledger = build_accounting_ledger(
            observations,
            generated_at="2026-09-06T12:00:00Z",
            software_version="0.8.0",
        )
        self.assertIn("COMMITMENT_AMOUNTS", ledger["capabilities"])
        self.assertIn("EXPENSE_ISSUE_DATE", ledger["capabilities"])
        self.assertIn("EVENT_MONTH", ledger["capabilities"])
        self.assertNotIn("EVENT_DATE", ledger["capabilities"])
        self.assertEqual(ledger["rows"][0]["observation_period"], "2026:01")
        self.assertNotIn("PROGRAMMATIC_CLASSIFICATION", ledger["capabilities"])
        self.assertNotIn("RESTS_PAYABLE", ledger["capabilities"])

        task184 = build_task184_bundle(
            generated_at="2026-09-06T12:00:00Z",
            software_version="0.8.0",
        )
        substantive = {k:v for k,v in task184["products"].items() if k != "QUERY_PRODUCT_CATALOG"}
        products = _with_catalog(
            {**substantive, "ACCOUNTING_LEDGER": ledger},
            generated_at="2026-09-06T12:00:00Z",
            software_version="0.8.0",
        )
        report = question_answerability(products)
        status = {row["question_id"]: row["status"] for row in report["questions"]}
        self.assertEqual(status["ACC_Q1"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(status["ACC_Q2"], "MATERIALIZED_PARTIAL")
        self.assertEqual(status["ACC_Q3"], "MATERIALIZED_PARTIAL")


if __name__ == "__main__":
    unittest.main()
