from __future__ import annotations

import copy
import unittest

from robo_dados_publicos.productization.document_event_context_execution import (
    build_extended_context_capability_matrix,
    document_event_recipe_question_ids,
    execute_contextual_query_v3,
    render_contextual_answer_v3,
    validate_contract,
)
from robo_dados_publicos.productization.generalized_context_execution import (
    execute_contextual_query_v2,
)


GENERATED_AT = "2026-09-08T02:05:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask211DocumentEventContextExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v3(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_and_extended_matrix_cover_all_38_questions(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["question_count"], 38)
        self.assertEqual(got["document_event_recipe_question_count"], 10)
        self.assertEqual(got["new_generic_document_event_count"], 9)
        self.assertEqual(
            got["execution_class_counts"],
            {
                "GENERIC_LOCAL_DOCUMENT_EVENT": 9,
                "GENERIC_LOCAL_SCHOOL_METRIC": 8,
                "NOT_YET_CONTEXT_EXECUTABLE": 18,
                "TASK209_SPECIAL": 3,
            },
        )
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_read"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])

    def test_document_event_recipe_class_is_derived_not_hand_routed(self):
        self.assertEqual(
            document_event_recipe_question_ids(),
            [
                "JOM_Q1",
                "JOM_Q2",
                "NORMS_Q1",
                "NORMS_Q2",
                "PERS_Q1",
                "PERS_Q2",
                "PLAN_Q1",
                "PLAN_Q2",
                "POLICY_Q1",
                "POLICY_Q2",
            ],
        )

    def test_extended_matrix_preserves_special_and_metric_classes(self):
        matrix = build_extended_context_capability_matrix()
        rows = {row["question_id"]: row for row in matrix["questions"]}
        self.assertEqual(rows["NORMS_Q2"]["execution_class"], "TASK209_SPECIAL")
        self.assertEqual(
            rows["INFRA_Q1"]["execution_class"],
            "GENERIC_LOCAL_SCHOOL_METRIC",
        )
        self.assertEqual(
            rows["NORMS_Q1"]["execution_class"],
            "GENERIC_LOCAL_DOCUMENT_EVENT",
        )
        self.assertEqual(
            rows["PLAN_Q1"]["execution_class"],
            "GENERIC_LOCAL_DOCUMENT_EVENT",
        )
        self.assertEqual(
            rows["PROC_Q1"]["execution_class"],
            "NOT_YET_CONTEXT_EXECUTABLE",
        )
        self.assertEqual(
            rows["PLAN_Q3"]["execution_class"],
            "NOT_YET_CONTEXT_EXECUTABLE",
        )

    def test_personnel_events_2026_are_exact_structured_jom_slice(self):
        got = self.execute("nomeações e exonerações em 2026")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "PERS_Q1")
        self.assertEqual(got["TIME_REFERENCE"], ["2026"])
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "APPLIED")
        summaries = [
            row for row in got["NUMBER_OR_FACT"]
            if row.get("kind") == "DOCUMENT_EVENT_SUMMARY"
            and row.get("product") == "JOM_EVENT_INDEX"
        ]
        self.assertEqual(len(summaries), 1)
        self.assertGreaterEqual(summaries[0]["matched_row_count"], 10)
        self.assertLessEqual(summaries[0]["displayed_row_count"], 12)
        events = [
            row for row in got["NUMBER_OR_FACT"]
            if row.get("kind") == "JOM_EVENT"
        ]
        self.assertTrue(events)
        self.assertTrue(
            any(
                "Secretaria Municipal de Educação" in str(row.get("text") or "")
                or "Secretaria Municipal de Educacao" in str(row.get("text") or "")
                for row in events
            )
        )
        self.assertIn("PUBLICATION_NE_IMPLEMENTATION", got["CAUTION_OR_LIMIT"])
        self.assertIn(
            "CURRENT_MATERIALIZED_JOM_CORPUS_NE_COMPLETE_YEAR",
            got["CAUTION_OR_LIMIT"],
        )

    def test_norms_2024_returns_decree_without_invented_same_year_cme(self):
        got = self.execute("decreto sobre escola em 2024")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "NORMS_Q1")
        docs = [
            row for row in got["NUMBER_OR_FACT"]
            if row.get("kind") == "PLANNING_DOCUMENT"
        ]
        ids = {row.get("document_id") for row in docs}
        self.assertIn("DECRETO_118_2024_EITI_LIMEIRA", ids)
        self.assertNotIn("CME_02_2021_EDUCACAO_TEMPO_INTEGRAL", ids)
        decree = next(
            row for row in docs
            if row.get("document_id") == "DECRETO_118_2024_EITI_LIMEIRA"
        )
        self.assertEqual(decree["evidence_role"], "PRIMARY_NORMATIVE")
        self.assertEqual(decree["quality_status"], "VALIDATED")
        self.assertIn("NORMATIVE_ACT_NE_IMPLEMENTATION", got["CAUTION_OR_LIMIT"])

    def test_plan_q1_2026_requires_and_returns_ppa_ldo_loa(self):
        got = self.execute("o que PPA LDO e LOA prometeram e autorizaram em 2026")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "PLAN_Q1")
        docs = [
            row for row in got["NUMBER_OR_FACT"]
            if row.get("kind") == "PLANNING_DOCUMENT"
        ]
        types = {row.get("document_type") for row in docs}
        self.assertEqual(types, {"PPA", "LDO", "LOA"})
        loa = [row for row in docs if row.get("document_type") == "LOA"]
        self.assertEqual(len(loa), 2)
        self.assertTrue(
            all(row.get("evidence_role") == "PRIMARY_SUBSTANTIVE" for row in loa)
        )
        self.assertTrue(
            any("2026-2029" == row.get("period") for row in docs)
        )
        self.assertIn("PLANNING_NE_ACCOUNTING_EXECUTION", got["CAUTION_OR_LIMIT"])

    def test_jom_q1_2026_is_bounded_summary_not_fake_complete_year(self):
        got = self.execute("o que saiu no jornal oficial em 2026")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "JOM_Q1")
        summary = next(
            row for row in got["NUMBER_OR_FACT"]
            if row.get("kind") == "DOCUMENT_EVENT_SUMMARY"
            and row.get("product") == "JOM_EVENT_INDEX"
        )
        self.assertGreater(summary["matched_row_count"], 0)
        self.assertLessEqual(summary["displayed_row_count"], 12)
        self.assertEqual(len(summary["matched_identity_sha256"]), 64)
        self.assertIn(
            "CURRENT_MATERIALIZED_JOM_CORPUS_NE_COMPLETE_YEAR",
            got["CAUTION_OR_LIMIT"],
        )
        if summary["matched_row_count"] > summary["displayed_row_count"]:
            self.assertIn(
                "DISPLAY_SAMPLE_NE_ALL_MATCHING_EVENTS",
                got["CAUTION_OR_LIMIT"],
            )

    def test_plan_q1_2024_does_not_substitute_2026_documents(self):
        got = self.execute("o que PPA LDO e LOA prometeram e autorizaram em 2024")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        self.assertEqual(got["question_id"], "PLAN_Q1")
        self.assertEqual(
            got["gap_scope"],
            "CURRENT_LOCAL_DOCUMENT_EVENT_PRODUCTS_EXACT_CONTEXT",
        )
        text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("não prova ausência global", text)
        encoded = str(got)
        self.assertNotIn("LOA 2026: ação", encoded)
        self.assertIn(
            "NO_NEAREST_PERIOD_SUBSTITUTION",
            got["CAUTION_OR_LIMIT"],
        )

    def test_document_event_school_filter_stops_without_text_identity_inference(self):
        got = self.execute(
            "o que saiu no jornal oficial da escola Rafael Affonso Leite em 2026"
        )
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["question_id"], "JOM_Q1")
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "UNSUPPORTED")
        text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("school identity was not inferred from object_text", text)

    def test_month_context_is_not_coerced_to_year(self):
        got = self.execute("o que saiu no jornal oficial em agosto de 2026")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["question_id"], "JOM_Q1")
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "UNSUPPORTED")
        text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("month and year-to-month are not coerced", text)

    def test_policy_2026_gap_does_not_promote_only_one_recipe_signal(self):
        got = self.execute("nova política pública em 2026")
        self.assertEqual(got["question_id"], "POLICY_Q1")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        signal = got["SOURCE_AND_PROVENANCE"][-1]["context_recipe_signal_status"]
        self.assertEqual(len(signal), 2)
        self.assertTrue(any(row["satisfied"] for row in signal))
        self.assertTrue(any(not row["satisfied"] for row in signal))
        self.assertIn(
            "PARTIAL_RECIPE_SIGNAL_NE_FULL_ANSWER",
            got["CAUTION_OR_LIMIT"],
        )

    def test_metadata_only_mixed_recipes_remain_not_yet_context_executable(self):
        rows = {
            row["question_id"]: row
            for row in build_extended_context_capability_matrix()["questions"]
        }
        for qid in ("PROC_Q1", "INFRA_Q2", "CTRL_Q2", "PLAN_Q3"):
            self.assertEqual(
                rows[qid]["execution_class"],
                "NOT_YET_CONTEXT_EXECUTABLE",
            )

    def test_task209_special_norms_q2_is_delegated_exactly(self):
        text = "Quais normas de matrícula mudaram em 2026?"
        a = self.execute(text)
        b = execute_contextual_query_v2(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "NORMS_Q2")
        self.assertEqual(a["state"], "EXPLICIT_CONTEXT_GAP")

    def test_task210_metric_executor_is_delegated_exactly(self):
        text = "infraestrutura da escola Rafael Affonso Leite em 2025"
        a = self.execute(text)
        b = execute_contextual_query_v2(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "INFRA_Q1")

    def test_no_context_question_preserves_legacy_path(self):
        got = self.execute("quanto foi empenhado liquidado e pago")
        self.assertEqual(
            got["state"],
            "LEGACY_UNCONTEXTUALIZED_PASSTHROUGH",
        )
        self.assertEqual(
            got["legacy_task207_result"]["answers"][0]["question_id"],
            "ACC_Q1",
        )

    def test_renderer_and_execution_are_deterministic(self):
        text = "decreto sobre escola em 2024"
        a = self.execute(text)
        b = self.execute(text)
        self.assertEqual(a, b)
        self.assertEqual(len(a["answer_sha256"]), 64)
        ra = render_contextual_answer_v3(a)
        rb = render_contextual_answer_v3(copy.deepcopy(b))
        self.assertEqual(ra, rb)
        self.assertEqual(len(ra["markdown_sha256"]), 64)
        self.assertIn("## Filtros contextuais", ra["markdown"])


if __name__ == "__main__":
    unittest.main()
