from __future__ import annotations

import copy
import unittest

from robo_dados_publicos.productization.proven_cross_product_execution import (
    execute_contextual_query_v6,
)
from robo_dados_publicos.productization.school_infrastructure_context_execution import (
    execute_contextual_query_v7,
    load_contract,
    render_contextual_answer_v7,
    validate_contract,
)

GENERATED_AT = "2026-09-09T02:10:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask218InfraQ2ContextualExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v7(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_promotes_exactly_infra_q2_to_34_of_38(self):
        cfg = load_contract()
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(cfg["promoted_questions"], ["INFRA_Q2"])
        self.assertEqual(got["contextual_paths_before"], 33)
        self.assertEqual(got["contextual_paths_after"], 34)
        self.assertEqual(
            set(cfg["retained_semantic_blockers"]),
            {"CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"},
        )
        self.assertEqual(got["bounded_jom_document_count"], 99)
        self.assertTrue(got["bounded_jom_content_scope_complete"])
        self.assertEqual(got["proven_named_school_event_count"], 1)
        self.assertEqual(cfg["execution"]["policy_service_facets_supported"], ["INFRAESTRUTURA"])
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])

    def test_municipal_question_returns_only_proven_named_school_event(self):
        got = self.execute("quais escolas receberam obras reformas ou equipamentos em 2026")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "INFRA_Q2")
        events = [row for row in got["NUMBER_OR_FACT"] if row["kind"] == "PROVEN_NAMED_SCHOOL_INFRASTRUCTURE_EVENT"]
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["school_code"], "35295061")
        self.assertEqual(event["school_name"], "CEIEF Arlindo de Salvo, Prof.")
        self.assertEqual(event["contract_number"], "42/2026")
        self.assertEqual(event["process_number"], "22.687/2024")
        self.assertEqual(event["published_value_brl"], "71000.00")
        self.assertIn("não a conclusão física", event["text"])
        self.assertEqual(got["TIME_REFERENCE"], ["JOM 2026-01-01..2026-09-08"])
        self.assertEqual(
            got["filter_accounting"]["POLICY_SERVICE_FACETS"]["status"],
            "APPLIED_INTRINSIC_INFRASTRUCTURE_SCOPE",
        )
        self.assertIn("CONTRACT_NE_COMPLETED_WORK", got["CAUTION_OR_LIMIT"])
        self.assertIn("PROVEN_NAMED_SCHOOL_SET_NE_ALL_REAL_WORLD_INFRASTRUCTURE", got["CAUTION_OR_LIMIT"])

    def test_exact_other_school_is_scoped_gap_not_absence_claim(self):
        got = self.execute(
            "minha escola recebeu obras reformas ou equipamentos em 2026",
            context_school_code="35470600",
        )
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        self.assertEqual(got["question_id"], "INFRA_Q2")
        fact = got["NUMBER_OR_FACT"][0]
        self.assertEqual(fact["kind"], "SCOPED_JOM_SCHOOL_INFRASTRUCTURE_GAP")
        self.assertEqual(fact["school_code"], "35470600")
        self.assertIn("não prova", fact["text"])
        self.assertIn("SCOPED_JOM_ZERO_MATCH_NE_REAL_WORLD_ABSENCE", got["CAUTION_OR_LIMIT"])

    def test_exact_arlindo_school_filter_returns_positive_event(self):
        got = self.execute(
            "minha escola recebeu obras reformas ou equipamentos em 2026",
            context_school_code="35295061",
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        event = next(row for row in got["NUMBER_OR_FACT"] if row["kind"] == "PROVEN_NAMED_SCHOOL_INFRASTRUCTURE_EVENT")
        self.assertEqual(event["school_code"], "35295061")
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "APPLIED_EXACT_SCHOOL_CODE")

    def test_explicit_school_name_in_text_resolves_without_personal_context(self):
        got = self.execute("CEIEF Arlindo de Salvo recebeu obras reformas ou equipamentos em 2026")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        event = next(row for row in got["NUMBER_OR_FACT"] if row["kind"] == "PROVEN_NAMED_SCHOOL_INFRASTRUCTURE_EVENT")
        self.assertEqual(event["school_code"], "35295061")
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "APPLIED_EXACT_SCHOOL_CODE")

    def test_other_year_is_not_substituted(self):
        got = self.execute("quais escolas receberam obras reformas ou equipamentos em 2025")
        self.assertEqual(got["question_id"], "INFRA_Q2")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "UNSUPPORTED")

    def test_plan_q3_delegates_exactly_to_v6(self):
        text = "planejamento e execução estão coerentes em 2026 na alimentação"
        a = self.execute(text)
        b = execute_contextual_query_v6(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "PLAN_Q3")

    def test_renderer_is_deterministic(self):
        answer = self.execute("quais escolas receberam obras reformas ou equipamentos em 2026")
        a = render_contextual_answer_v7(answer)
        b = render_contextual_answer_v7(copy.deepcopy(answer))
        self.assertEqual(a, b)
        self.assertEqual(len(a["markdown_sha256"]), 64)
        self.assertIn("Arlindo de Salvo", a["markdown"])


if __name__ == "__main__":
    unittest.main()
