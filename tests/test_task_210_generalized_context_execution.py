from __future__ import annotations

import copy
import unittest

from robo_dados_publicos.productization.context_aware_execution import (
    execute_contextual_query as execute_task209,
)
from robo_dados_publicos.productization.generalized_context_execution import (
    build_context_capability_matrix,
    execute_contextual_query_v2,
    generic_school_metric_question_ids,
    render_contextual_answer_v2,
    validate_contract,
)


GENERATED_AT = "2026-09-08T02:05:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask210GeneralizedContextExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v2(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_and_matrix_cover_all_38_questions(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["question_count"], 38)
        self.assertEqual(got["generic_school_metric_recipe_count"], 9)
        self.assertEqual(got["new_generic_execution_class_count"], 8)
        self.assertEqual(got["task209_special_count"], 3)
        self.assertEqual(got["not_yet_context_executable_count"], 27)
        self.assertEqual(len(got["matrix_sha256"]), 64)
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_read"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])

    def test_generic_recipe_class_is_derived_from_current_recipe_structure(self):
        self.assertEqual(
            generic_school_metric_question_ids(),
            [
                "EQUITY_Q2",
                "INFRA_Q1",
                "LEARN_Q1",
                "LEARN_Q2",
                "LEARN_Q3",
                "NETWORK_Q1",
                "NETWORK_Q2",
                "NETWORK_Q3",
                "TEACH_Q1",
            ],
        )

    def test_execution_class_counts_separate_special_generic_and_not_yet(self):
        matrix = build_context_capability_matrix()
        self.assertEqual(
            matrix["execution_class_counts"],
            {
                "GENERIC_LOCAL_SCHOOL_METRIC": 8,
                "NOT_YET_CONTEXT_EXECUTABLE": 27,
                "TASK209_SPECIAL": 3,
            },
        )
        self.assertFalse(
            matrix["semantic_answerability_equals_contextual_executability"]
        )
        rows = {row["question_id"]: row for row in matrix["questions"]}
        self.assertEqual(rows["FIN_Q1"]["execution_class"], "TASK209_SPECIAL")
        self.assertEqual(rows["NETWORK_Q3"]["execution_class"], "TASK209_SPECIAL")
        self.assertTrue(rows["NETWORK_Q3"]["generic_school_metric_recipe"])
        self.assertEqual(
            rows["INFRA_Q1"]["execution_class"],
            "GENERIC_LOCAL_SCHOOL_METRIC",
        )
        self.assertEqual(
            rows["PLAN_Q3"]["execution_class"],
            "NOT_YET_CONTEXT_EXECUTABLE",
        )
        self.assertEqual(
            rows["INFRA_Q1"]["filters"]["SCHOOL"],
            "EXACT_LOCAL_SUPPORTED",
        )
        self.assertEqual(
            rows["INFRA_Q1"]["filters"]["POLICY_SERVICE_FACETS"],
            "APPLIED_BY_RECIPE_SCOPE",
        )

    def test_network_q2_school_year_uses_generic_kernel(self):
        got = self.execute("tempo integral do Rafael Affonso Leite em 2025")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "NETWORK_Q2")
        self.assertEqual(got["context"]["school"]["school_code"], "35470600")
        self.assertEqual(got["TIME_REFERENCE"], ["2025"])
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "APPLIED")
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "APPLIED")
        self.assertEqual(
            got["filter_accounting"]["POLICY_SERVICE_FACETS"]["status"],
            "APPLIED_BY_RECIPE_SCOPE",
        )
        by_id = {row["metric_id"]: row for row in got["NUMBER_OR_FACT"]}
        self.assertEqual(set(by_id), {"FULL_TIME_SHARE"})
        self.assertEqual(by_id["FULL_TIME_SHARE"]["value"], 18.5)
        self.assertEqual(by_id["FULL_TIME_SHARE"]["unit"], "PERCENT")
        self.assertIn(
            "CONTEXTUAL_SINGLE_YEAR_SNAPSHOT_NE_HISTORICAL_TREND",
            got["CAUTION_OR_LIMIT"],
        )

    def test_infra_q1_school_year_uses_all_recipe_metrics(self):
        got = self.execute(
            "infraestrutura da escola Rafael Affonso Leite em 2025"
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "INFRA_Q1")
        by_id = {row["metric_id"]: row for row in got["NUMBER_OR_FACT"]}
        self.assertEqual(
            set(by_id),
            {
                "INFRASTRUCTURE_SCORE_0_8",
                "ACCESSIBILITY_SCORE_0_8",
                "DEVICE_COUNT",
            },
        )
        self.assertEqual(by_id["INFRASTRUCTURE_SCORE_0_8"]["value"], 8)
        self.assertEqual(by_id["ACCESSIBILITY_SCORE_0_8"]["value"], 3)
        self.assertEqual(by_id["DEVICE_COUNT"]["value"], 74)
        self.assertTrue(
            all(
                ref.get("scope_id") == "35470600"
                for ref in got["SOURCE_AND_PROVENANCE"]
            )
        )

    def test_teach_q1_school_year_uses_recipe_consumed_docentes_facet(self):
        got = self.execute(
            "formação e esforço dos professores do Rafael Affonso Leite em 2025"
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "TEACH_Q1")
        self.assertEqual(
            got["filter_accounting"]["POLICY_SERVICE_FACETS"]["status"],
            "APPLIED_BY_RECIPE_SCOPE",
        )
        by_id = {row["metric_id"]: row for row in got["NUMBER_OR_FACT"]}
        self.assertEqual(
            set(by_id),
            {"AFD", "IED_LEVEL_5_6_SHARE", "IRD"},
        )
        self.assertEqual(by_id["AFD"]["value"], 86.4)
        self.assertEqual(by_id["IED_LEVEL_5_6_SHARE"]["value"], 0)
        self.assertEqual(by_id["IRD"]["value"], 2.34)

    def test_exact_year_recipe_shortfall_returns_context_gap_not_partial_answer(self):
        got = self.execute(
            "infraestrutura da escola Rafael Affonso Leite em 2024"
        )
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        self.assertEqual(got["question_id"], "INFRA_Q1")
        self.assertEqual(
            got["gap_scope"],
            "CURRENT_LOCAL_SCHOOL_INDICATOR_SERIES_EXACT_CONTEXT",
        )
        text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("Evidência parcial não foi promovida", text)
        self.assertIn(
            "INCOMPLETE_CONTEXT_RECIPE_NE_FULL_ANSWER",
            got["CAUTION_OR_LIMIT"],
        )
        self.assertEqual(
            got["filter_accounting"]["PERIOD"]["status"],
            "APPLIED_TO_INCOMPLETE_RECIPE",
        )

    def test_month_context_is_not_coerced_to_year(self):
        got = self.execute(
            "infraestrutura da escola Rafael Affonso Leite em maio de 2025"
        )
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["question_id"], "INFRA_Q1")
        text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("month and year-to-month are not snapped", text)
        self.assertEqual(
            got["filter_accounting"]["PERIOD"]["status"],
            "UNSUPPORTED",
        )

    def test_task209_special_fin_q1_is_delegated_exactly(self):
        text = "Quanto a Educação gastou até julho deste ano?"
        kwargs = {"reference_date": "2026-09-08"}
        a = self.execute(text, **kwargs)
        b = execute_task209(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "FIN_Q1")
        self.assertEqual(a["NUMBER_OR_FACT"][0]["value_brl"], "262452288.06")

    def test_task209_special_network_q3_remains_special_not_generic(self):
        a = self.execute("Como está o Rafael Affonso Leite?")
        b = execute_task209(
            "Como está o Rafael Affonso Leite?",
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "NETWORK_Q3")
        self.assertTrue(
            any(
                row.get("kind") == "SCHOOL_VS_NETWORK"
                for row in a["NUMBER_OR_FACT"]
            )
        )

    def test_mixed_product_question_is_not_auto_promoted(self):
        got = self.execute("quanto por aluno em 2025")
        self.assertEqual(got["question_id"], "FIN_Q2")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        matrix = {
            row["question_id"]: row
            for row in build_context_capability_matrix()["questions"]
        }
        self.assertEqual(
            matrix["FIN_Q2"]["execution_class"],
            "NOT_YET_CONTEXT_EXECUTABLE",
        )
        self.assertEqual(
            set(matrix["FIN_Q2"]["recipe_products"]),
            {"FISCAL_SERIES", "SCHOOL_INDICATOR_SERIES"},
        )

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

    def test_renderer_remains_task209_compatible_for_generic_answer(self):
        answer = self.execute(
            "infraestrutura da escola Rafael Affonso Leite em 2025"
        )
        rendered = render_contextual_answer_v2(answer)
        self.assertEqual(rendered["question_id"], "INFRA_Q1")
        md = rendered["markdown"]
        self.assertIn("INFRASTRUCTURE_SCORE_0_8", str(answer))
        self.assertIn("## Filtros contextuais", md)
        self.assertIn("APPLIED_BY_RECIPE_SCOPE", md)
        self.assertIn("CEIEF Rafael Affonso Leite", md)

    def test_generic_execution_is_deterministic(self):
        text = "tempo integral do Rafael Affonso Leite em 2025"
        a = self.execute(text)
        b = self.execute(text)
        self.assertEqual(a, b)
        self.assertEqual(len(a["answer_sha256"]), 64)
        ra = render_contextual_answer_v2(a)
        rb = render_contextual_answer_v2(copy.deepcopy(b))
        self.assertEqual(ra, rb)
        self.assertEqual(len(ra["markdown_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
