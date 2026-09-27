from __future__ import annotations

from decimal import Decimal
import unittest

from robo_dados_publicos.productization.proven_cross_product_execution import (
    execute_contextual_query_v6,
    load_contract,
    render_contextual_answer_v6,
    validate_contract,
)
from robo_dados_publicos.productization.custody_ledger_projection_execution import (
    execute_contextual_query_v5,
)


GENERATED_AT = "2026-09-08T18:40:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask215ProvenCrossProductExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v6(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def execute_v5(self, text: str, **kwargs):
        return execute_contextual_query_v5(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_validates_one_promotion_and_five_retained_blockers(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["promoted_question_count"], 1)
        self.assertEqual(got["retained_semantic_blocker_count"], 5)
        self.assertEqual(got["planning_accounting_crosswalk_rows"], 2)
        self.assertEqual(got["procurement_shaped_jom_events"], 138)
        self.assertEqual(got["procurement_cnpj_overlap_suppliers"], 31)
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_read"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])

        contract = load_contract()
        self.assertEqual(contract["promoted_questions"], ["PLAN_Q3"])
        self.assertEqual(
            contract["join_strength"]["PLAN_Q3"],
            "AUTHORITATIVE_STRUCTURED_DIMENSIONAL_CROSSWALK",
        )
        self.assertFalse(contract["join_strength"]["transaction_identity_claim"])
        self.assertFalse(contract["join_strength"]["fuzzy_text_match_used"])
        self.assertFalse(contract["join_strength"]["amount_match_used"])
        self.assertFalse(contract["join_strength"]["date_proximity_match_used"])

    def test_generic_plan_q3_2026_returns_exactly_two_scoped_segments(self):
        got = self.execute("planejamento e execucao estao coerentes em 2026?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "PLAN_Q3")
        rows = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "SCOPED_PLANNING_EXECUTION_CROSSWALK"
        ]
        self.assertEqual(len(rows), 2)
        by_action = {row["planning_action_code"]: row for row in rows}
        self.assertEqual(set(by_action), {"2720", "2690"})
        self.assertFalse(by_action["2720"]["transaction_identity_claim"])
        self.assertFalse(by_action["2690"]["whole_plan_coherence_claim"])
        self.assertIn("SCOPED_TWO_SEGMENTS_NE_WHOLE_PLAN_COHERENCE", got["CAUTION_OR_LIMIT"])
        self.assertEqual(set(got["TIME_REFERENCE"]), {"LOA 2026", "TCE 2026-01..2026-07"})

    def test_food_crosswalk_recomputes_exact_authorization_execution_relation(self):
        got = self.execute(
            "planejamento e execucao estao coerentes na alimentacao em 2026?"
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "PLAN_Q3")
        rows = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "SCOPED_PLANNING_EXECUTION_CROSSWALK"
        ]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["planning_action_code"], "2720")
        self.assertEqual(row["planning_label"], "ALIMENTACAO ESCOLAR")
        self.assertEqual(Decimal(row["appropriation_brl"]), Decimal("28000000.00"))
        self.assertEqual(row["accounting_source_rows"], 434)
        self.assertEqual(
            row["accounting_filter"],
            {
                "fiscal_year": 2026,
                "function": "EDUCAÇÃO",
                "subfunction": "ALIMENTAÇÃO E NUTRIÇÃO",
                "program_code": "2001",
                "action_code": "2720",
            },
        )
        self.assertEqual(Decimal(row["commitment_arithmetic_brl"]), Decimal("26225933.51"))
        self.assertEqual(
            Decimal(row["source_stage_amounts_brl"]["Valor Liquidado"]),
            Decimal("14756899.27"),
        )
        self.assertEqual(
            Decimal(row["source_stage_amounts_brl"]["Valor Pago"]),
            Decimal("14756899.27"),
        )
        self.assertEqual(row["appropriation_relative_pct"]["commitment_arithmetic"], "93.66")
        self.assertEqual(row["appropriation_relative_pct"]["liquidated"], "52.70")
        self.assertEqual(row["appropriation_relative_pct"]["paid"], "52.70")
        self.assertEqual(
            got["filter_accounting"]["POLICY_SERVICE_FACETS"]["status"],
            "APPLIED_BY_CROSSWALK_SCOPE",
        )

    def test_transport_crosswalk_requires_ensino_medio_subfunction(self):
        got = self.execute(
            "planejamento e execucao estao coerentes no transporte escolar em 2026?"
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        rows = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "SCOPED_PLANNING_EXECUTION_CROSSWALK"
        ]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["planning_action_code"], "2690")
        self.assertEqual(row["planning_label"], "TRANSPORTE ESCOLAR")
        self.assertEqual(row["accounting_source_rows"], 20)
        self.assertEqual(row["accounting_filter"]["subfunction"], "ENSINO MÉDIO")
        self.assertEqual(Decimal(row["appropriation_brl"]), Decimal("6152000.00"))
        self.assertEqual(Decimal(row["commitment_arithmetic_brl"]), Decimal("2393081.04"))
        self.assertEqual(
            Decimal(row["source_stage_amounts_brl"]["Valor Liquidado"]),
            Decimal("209450.16"),
        )
        self.assertEqual(row["appropriation_relative_pct"]["commitment_arithmetic"], "38.90")
        self.assertEqual(row["appropriation_relative_pct"]["liquidated"], "3.40")
        self.assertEqual(row["appropriation_relative_pct"]["paid"], "3.40")

    def test_transport_unrestricted_action_is_proven_unsafe_for_scoped_loa_segment(self):
        contract = load_contract()
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        fixture = json.loads((root / contract["crosswalk_fixture"]).read_text(encoding="utf-8"))
        transport = next(
            row for row in fixture["rows"]
            if row["planning"]["action_code"] == "2690"
        )
        self.assertEqual(transport["accounting_action_unrestricted_rows"], 78)
        self.assertEqual(
            transport["accounting_subfunction_row_counts"],
            {
                "ENSINO FUNDAMENTAL": 39,
                "EDUCAÇÃO INFANTIL": 19,
                "ENSINO MÉDIO": 20,
            },
        )
        self.assertTrue(transport["subfunction_restriction_required"])
        self.assertEqual(transport["accounting_source_rows"], 20)

    def test_both_supported_facets_return_both_segments(self):
        got = self.execute(
            "planejamento e execucao estao coerentes na alimentacao e transporte escolar em 2026?"
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        rows = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "SCOPED_PLANNING_EXECUTION_CROSSWALK"
        ]
        self.assertEqual(
            {row["planning_action_code"] for row in rows},
            {"2690", "2720"},
        )

    def test_other_year_is_not_relabelled_to_2026(self):
        for year in (2025, 2027):
            with self.subTest(year=year):
                got = self.execute(
                    f"planejamento e execucao estao coerentes em {year}?"
                )
                self.assertEqual(got["question_id"], "PLAN_Q3")
                self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
                self.assertNotIn("SCOPED_PLANNING_EXECUTION_CROSSWALK", str(got))
                self.assertNotIn("26225933.51", str(got))

    def test_unsupported_facet_is_explicit_crosswalk_gap(self):
        got = self.execute(
            "planejamento e execucao estao coerentes na infraestrutura em 2026?"
        )
        self.assertEqual(got["question_id"], "PLAN_Q3")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        gap = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "SCOPED_CROSSWALK_FACET_GAP"
        )
        self.assertEqual(gap["unsupported_facets"], ["INFRAESTRUTURA"])
        self.assertEqual(set(gap["supported_facets"]), {"ALIMENTACAO", "TRANSPORTE"})
        self.assertEqual(
            got["gap_scope"],
            "TASK215_SCOPED_PLANNING_ACCOUNTING_CROSSWALK",
        )

    def test_school_context_is_never_invented_for_plan_execution_crosswalk(self):
        got = self.execute(
            "planejamento e execucao estao coerentes no Rafael Affonso Leite em 2026?"
        )
        self.assertEqual(got["question_id"], "PLAN_Q3")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "UNSUPPORTED")

    def test_five_remaining_blockers_delegate_exactly_to_v5(self):
        cases = (
            "o que TCE e demais controles corroboram em 2026?",
            "quais escolas receberam obras reformas ou equipamentos em 2026?",
            "o que a prefeitura esta comprando em 2026?",
            "quem fornece por quanto e por quanto tempo em 2026?",
            "houve aditivo apostilamento ou nova licitacao em 2026?",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(self.execute(text), self.execute_v5(text))

    def test_prior_task209_210_211_213_214_paths_delegate_exactly(self):
        cases = [
            ("Quanto a Educação gastou até julho deste ano?", {"reference_date": "2026-09-08"}),
            ("infraestrutura da escola Rafael Affonso Leite em 2025", {}),
            ("nomeações e exonerações em 2026", {}),
            ("quanto por aluno em 2025?", {}),
            ("ha restos a pagar em abril de 2026?", {}),
        ]
        for text, kwargs in cases:
            with self.subTest(text=text):
                self.assertEqual(self.execute(text, **kwargs), self.execute_v5(text, **kwargs))

    def test_renderer_preserves_scoped_claim_boundaries(self):
        answer = self.execute("planejamento e execucao estao coerentes em 2026?")
        rendered = render_contextual_answer_v6(answer)
        self.assertEqual(rendered["question_id"], "PLAN_Q3")
        self.assertIn("ALIMENTACAO ESCOLAR", rendered["markdown"])
        self.assertIn("TRANSPORTE ESCOLAR", rendered["markdown"])
        self.assertIn("SCOPED_TWO_SEGMENTS_NE_WHOLE_PLAN_COHERENCE", rendered["markdown"])

    def test_outputs_are_deterministic_and_runtime_offline(self):
        for text in (
            "planejamento e execucao estao coerentes em 2026?",
            "planejamento e execucao estao coerentes na alimentacao em 2026?",
            "planejamento e execucao estao coerentes no transporte escolar em 2026?",
        ):
            with self.subTest(text=text):
                a = self.execute(text)
                b = self.execute(text)
                self.assertEqual(a, b)
                self.assertEqual(len(a["answer_sha256"]), 64)
                self.assertFalse(a["llm_used"])
                self.assertTrue(all(v is False for v in a["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
