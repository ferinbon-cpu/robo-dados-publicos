from __future__ import annotations

import unittest

from robo_dados_publicos.productization.direct_jom_procurement_context_execution import (
    execute_contextual_query_v9,
    load_contract,
    render_contextual_answer_v9,
    validate_contract,
)


GENERATED_AT = "2026-09-10T19:00:00-03:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask220DirectJomProcurementContextExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v9(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_validation_closes_contextual_coverage(self) -> None:
        contract = load_contract()
        self.assertEqual(contract["promoted_questions"], ["PROC_Q1", "PROC_Q2", "PROC_Q3"])
        self.assertEqual(contract["contextual_coverage"]["before"], 35)
        self.assertEqual(contract["contextual_coverage"]["after"], 38)
        self.assertEqual(contract["contextual_coverage"]["remaining_semantic_blockers"], [])
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["contextual_paths_after"], 38)
        self.assertEqual(got["remaining_semantic_blockers"], [])
        self.assertFalse(got["full_calendar_year_claim"])
        self.assertFalse(got["exhaustive_purchase_inventory_claim"])

    def test_proc_q1_answers_with_bounded_examples_not_inventory(self) -> None:
        got = self.execute("O que a prefeitura esta comprando?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "PROC_Q1")
        scope = got["NUMBER_OR_FACT"][0]
        self.assertEqual(scope["official_document_count"], 99)
        self.assertEqual(scope["parsed_event_rows"], 2711)
        self.assertEqual(scope["procurement_shaped_event_rows"], 1078)
        self.assertFalse(scope["unique_purchase_count_claim"])
        self.assertFalse(scope["exhaustive_object_inventory_claim"])
        objects = [row.get("object_text") for row in got["NUMBER_OR_FACT"] if row.get("kind") == "DIRECT_JOM_PROCUREMENT_OBJECT_EXAMPLE"]
        self.assertIn("Eventual aquisição de mobiliário", objects)
        self.assertIn("Contratação de empresa especializada em locação de sistema de endoscopia", objects)
        self.assertIn("DIRECT_EXAMPLES_NE_EXHAUSTIVE_INVENTORY", got["CAUTION_OR_LIMIT"])
        self.assertIn("BOUNDED_2026_THROUGH_2026_09_08_NE_FULL_CALENDAR_YEAR", got["CAUTION_OR_LIMIT"])

    def test_proc_q2_uses_same_publication_supplier_value_term_only(self) -> None:
        got = self.execute("Quem fornece, por quanto e por quanto tempo?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "PROC_Q2")
        self.assertEqual(len(got["NUMBER_OR_FACT"]), 1)
        row = got["NUMBER_OR_FACT"][0]
        self.assertEqual(row["event_id"], "JOEV_083e522d4145e4d27580")
        self.assertEqual(row["contract_number"], "45/2026")
        self.assertEqual(row["process_number"], "902.281/2025")
        self.assertEqual(row["bidding_number"], "10/2026")
        self.assertEqual(row["supplier_name"], "Med Doctor Acessórios Ltda")
        self.assertEqual(row["supplier_cnpj"], "37457979000131")
        self.assertEqual(row["published_value_brl"], "210000.00")
        self.assertEqual(row["published_term_text"], "12 meses contados a partir da data indicada na ordem de serviço")
        self.assertIn("PUBLISHED_CONTRACT_VALUE_NE_PAID_AMOUNT", got["CAUTION_OR_LIMIT"])
        self.assertIn("NO_TDA_OR_TCESP_EXECUTION_VALUES_IN_PROC_Q2", got["CAUTION_OR_LIMIT"])
        serialized = str(got["NUMBER_OR_FACT"])
        self.assertNotIn("174999.99", serialized)
        self.assertNotIn("35000.00", serialized)

    def test_proc_q3_positive_additive_and_tender_without_apostilamento_absence(self) -> None:
        got = self.execute("Houve aditivo, apostilamento ou nova licitacao?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "PROC_Q3")
        kinds = {row["kind"]: row for row in got["NUMBER_OR_FACT"]}
        self.assertEqual(kinds["DIRECT_JOM_CONTRACT_ADDITIVE_SIGNAL"]["validated_publication_event_count"], 5)
        self.assertEqual(kinds["DIRECT_JOM_NEW_TENDER_EXAMPLE"]["event_id"], "JOEV_07357f03181c3f43831c")
        self.assertEqual(kinds["DIRECT_JOM_NEW_TENDER_EXAMPLE"]["bidding_number"], "326/2026")
        self.assertFalse(kinds["APOSTILAMENTO_EVIDENCE_GAP"]["absence_claim"])
        self.assertIn("NO_APOSTILAMENTO_ABSENCE_INFERENCE", got["CAUTION_OR_LIMIT"])
        self.assertIn("NO_CROSS_EVENT_RELATIONSHIP_INFERENCE", got["CAUTION_OR_LIMIT"])

    def test_other_question_delegates_to_v8(self) -> None:
        got = self.execute("O que TCE e demais controles corroboram?")
        self.assertEqual(got["question_id"], "CTRL_Q2")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["NUMBER_OR_FACT"][0]["kind"], "PROVEN_CROSS_SOURCE_CONTROL_CORROBORATION")

    def test_other_year_is_not_substituted(self) -> None:
        got = self.execute("O que a prefeitura esta comprando em 2025?")
        if got.get("question_id") == "PROC_Q1":
            self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
            self.assertIn("UNSUPPORTED_CONTEXT_NE_NEAREST_AVAILABLE_CONTEXT", got["CAUTION_OR_LIMIT"])
        else:
            self.assertNotEqual(got.get("question_id"), "PROC_Q1")

    def test_renderer_and_remote_effects(self) -> None:
        got = self.execute("Quem fornece, por quanto e por quanto tempo?")
        rendered = render_contextual_answer_v9(got)
        self.assertIn("markdown", rendered)
        self.assertIn("Med Doctor", rendered["markdown"])
        self.assertTrue(all(value is False for value in got["remote_effects"].values()))
        self.assertFalse(got["numeric_invention_performed"])
        self.assertFalse(got["causal_effect_created"])
        self.assertFalse(got["llm_used"])


if __name__ == "__main__":
    unittest.main()
