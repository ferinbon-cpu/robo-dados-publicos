from __future__ import annotations

import copy
import unittest

from robo_dados_publicos.productization.context_aware_execution import (
    execute_contextual_query,
    render_contextual_answer_markdown,
    validate_answer,
    validate_contract,
)


GENERATED_AT = "2026-09-08T02:05:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask209ContextAwareExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_is_bounded_offline_and_pins_three_context_classes(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["supported_contextual_question_count"], 3)
        self.assertEqual(got["network_metrics"], ["APPROVAL_RATE", "IDEB"])
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])

    def test_fin_q1_through_july_executes_exact_materialized_projection(self):
        got = self.execute(
            "Quanto a Educação gastou até julho deste ano?",
            reference_date="2026-09-08",
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "FIN_Q1")
        self.assertFalse(got["context_dropped"])
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "APPLIED")
        headline = got["NUMBER_OR_FACT"][0]
        self.assertEqual(headline["stage_semantic"], "LIQUIDATED_TO_DATE")
        self.assertEqual(headline["value_brl"], "262452288.06")
        stages = got["NUMBER_OR_FACT"][1]
        self.assertEqual(stages["empenhado_liquido_brl"], "368762412.07")
        self.assertEqual(stages["liquidado_brl"], "262452288.06")
        self.assertEqual(stages["pago_brl"], "227797802.44")
        self.assertEqual(got["TIME_REFERENCE"], ["2026-01..2026-07"])
        self.assertTrue(
            any("138279835.79" in row for row in got["COMPARISON_OR_TREND"])
        )
        self.assertTrue(
            any(ref.get("projection_key") == "through_july" for ref in got["SOURCE_AND_PROVENANCE"])
        )
        self.assertIn("COMMITMENT_NE_LIQUIDATION_NE_PAYMENT", got["CAUTION_OR_LIMIT"])

    def test_fin_q1_through_april_is_also_exact_supported_boundary(self):
        got = self.execute("Quanto a Educação gastou até abril de 2026?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["NUMBER_OR_FACT"][0]["value_brl"], "138279835.79")
        self.assertEqual(got["NUMBER_OR_FACT"][1]["pago_brl"], "104176664.15")
        self.assertEqual(got["TIME_REFERENCE"], ["2026-01..2026-04"])

    def test_fin_q1_unsupported_month_does_not_snap_to_nearest_projection(self):
        got = self.execute("Quanto a Educação gastou até junho de 2026?")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["question_id"], "FIN_Q1")
        text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("no nearest-period substitution", text)
        self.assertNotIn("262452288.06", text)
        self.assertNotIn("138279835.79", text)
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "UNSUPPORTED")

    def test_rafael_affonso_leite_compares_exact_school_and_network_2025(self):
        got = self.execute("Como está o Rafael Affonso Leite?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "NETWORK_Q3")
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "APPLIED")
        self.assertEqual(got["filter_accounting"]["GRANULARITY"]["status"], "APPLIED")
        by_metric = {row["metric_id"]: row for row in got["NUMBER_OR_FACT"]}
        self.assertEqual(set(by_metric), {"IDEB", "APPROVAL_RATE"})
        self.assertEqual(by_metric["IDEB"]["period"], "2025")
        self.assertEqual(by_metric["IDEB"]["school_value"], 7.9)
        self.assertEqual(by_metric["IDEB"]["network_value"], 7.1)
        self.assertEqual(by_metric["APPROVAL_RATE"]["school_value"], 100)
        self.assertEqual(by_metric["APPROVAL_RATE"]["network_value"], 99.9)
        self.assertEqual(got["TIME_REFERENCE"], ["2025"])
        refs = got["SOURCE_AND_PROVENANCE"]
        self.assertTrue(any(ref.get("scope_id") == "35470600" for ref in refs))
        self.assertTrue(any(ref.get("scope_level") == "NETWORK" for ref in refs))
        self.assertIn("SCHOOL_NETWORK_COMPARISON_NE_CAUSAL_EXPLANATION", got["CAUTION_OR_LIMIT"])

    def test_personal_school_context_executes_same_canonical_identity(self):
        got = self.execute(
            "Compare minha escola com a rede.",
            context_school_code="35470600",
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "NETWORK_Q3")
        self.assertEqual(got["context"]["school"]["school_code"], "35470600")
        self.assertTrue(
            all(row["school_code"] == "35470600" for row in got["NUMBER_OR_FACT"])
        )

    def test_school_requested_year_must_exist_in_both_school_and_network(self):
        got = self.execute("Como está o Rafael Affonso Leite em 2024?")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["question_id"], "NETWORK_Q3")
        text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("no nearest-year substitution", text)

    def test_norms_matricula_2026_returns_bounded_context_gap_not_old_norms(self):
        got = self.execute("Quais normas de matrícula mudaram em 2026?")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        self.assertEqual(got["question_id"], "NORMS_Q2")
        self.assertEqual(
            got["gap_scope"],
            "CURRENT_MATERIALIZED_PLANNING_DOCUMENT_INDEX_ONLY",
        )
        self.assertEqual(
            got["filter_accounting"]["POLICY_SERVICE_FACETS"]["status"],
            "APPLIED_TO_ZERO_MATCH_QUERY",
        )
        self.assertEqual(
            got["filter_accounting"]["PERIOD"]["status"],
            "APPLIED_TO_ZERO_MATCH_QUERY",
        )
        fact_text = "\n".join(row["text"] for row in got["NUMBER_OR_FACT"])
        self.assertIn("não prova ausência global", fact_text)
        encoded = str(got)
        self.assertNotIn("CME_02_2021_EDUCACAO_TEMPO_INTEGRAL", encoded)
        self.assertNotIn("DECRETO_118_2024_EITI_LIMEIRA", encoded)
        self.assertIn(
            "CURRENT_MATERIALIZED_CORPUS_ZERO_MATCH_NE_GLOBAL_ABSENCE",
            got["CAUTION_OR_LIMIT"],
        )
        self.assertEqual(got["SOURCE_AND_PROVENANCE"][0]["matching_rows"], 0)

    def test_task208_binding_stop_is_propagated(self):
        got = self.execute("Compare minha escola com a rede.")
        self.assertEqual(got["state"], "BINDING_STOP")
        self.assertEqual(got["context"]["state"], "NEEDS_SCHOOL_CONTEXT")
        self.assertEqual(got["question_id"], None)

    def test_uncontextualized_question_preserves_legacy_task207_task205_path(self):
        got = self.execute("quanto foi empenhado liquidado e pago")
        self.assertEqual(got["state"], "LEGACY_UNCONTEXTUALIZED_PASSTHROUGH")
        legacy = got["legacy_task207_result"]
        self.assertEqual(legacy["answer_count"], 1)
        self.assertEqual(legacy["answers"][0]["question_id"], "ACC_Q1")
        self.assertFalse(got["context_dropped"])

    def test_context_on_question_outside_bounded_set_stops_instead_of_dropping(self):
        got = self.execute("Como está o AEE em 2025?")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["question_id"], "EQUITY_Q2")
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "UNSUPPORTED")

    def test_markdown_exposes_filters_gap_scope_and_guards(self):
        answer = self.execute("Quais normas de matrícula mudaram em 2026?")
        render = render_contextual_answer_markdown(answer)
        md = render["markdown"]
        self.assertIn("## Filtros contextuais", md)
        self.assertIn("APPLIED_TO_ZERO_MATCH_QUERY", md)
        self.assertIn("GAP_SCOPE=CURRENT_MATERIALIZED_PLANNING_DOCUMENT_INDEX_ONLY", md)
        self.assertIn("Nenhum filtro solicitado foi descartado silenciosamente", md)

    def test_validation_and_determinism(self):
        a = self.execute(
            "Quanto a Educação gastou até julho deste ano?",
            reference_date="2026-09-08",
        )
        b = self.execute(
            "Quanto a Educação gastou até julho deste ano?",
            reference_date="2026-09-08",
        )
        self.assertEqual(a, b)
        self.assertEqual(len(a["answer_sha256"]), 64)
        self.assertEqual(validate_answer(copy.deepcopy(a)), a)
        ra = render_contextual_answer_markdown(a)
        rb = render_contextual_answer_markdown(copy.deepcopy(b))
        self.assertEqual(ra, rb)
        self.assertEqual(len(ra["markdown_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
