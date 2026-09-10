from __future__ import annotations

import copy
import unittest

from robo_dados_publicos.productization.school_infrastructure_context_execution import (
    execute_contextual_query_v7,
)
from robo_dados_publicos.productization.tda_control_corroboration_execution import (
    execute_contextual_query_v8,
    load_contract,
    render_contextual_answer_v8,
    validate_contract,
)

GENERATED_AT = "2026-09-10T21:00:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask219AATDAStrongProcurementBridge(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v8(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_promotes_only_ctrl_q2_to_35_of_38(self):
        cfg = load_contract()
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(cfg["promoted_questions"], ["CTRL_Q2"])
        self.assertEqual(got["contextual_paths_before"], 34)
        self.assertEqual(got["contextual_paths_after"], 35)
        self.assertEqual(set(cfg["retained_semantic_blockers"]), {"PROC_Q1", "PROC_Q2", "PROC_Q3"})
        self.assertTrue(got["strong_contract_to_commitment_identity_proven"])
        self.assertFalse(got["weak_join_used"])
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])

    def test_ctrl_q2_2026_returns_exact_strong_chain(self):
        got = self.execute("o que TCE e demais controles corroboram em 2026?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "CTRL_Q2")
        strong = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "PROVEN_CROSS_SOURCE_CONTROL_CORROBORATION"
        )
        self.assertEqual(strong["contract_number"], "45/2026")
        self.assertEqual(strong["administrative_process"], "902.281/2025")
        self.assertEqual(strong["legal_bidding_identifier"], "10/2026")
        self.assertEqual(strong["tda_procurement_process_identifier"], "E00010/2026")
        self.assertEqual(strong["tda_commitment_number"], "03286-01")
        self.assertEqual(strong["contracted_brl"], "210000.00")
        self.assertEqual(strong["committed_brl"], "174999.99")
        self.assertEqual(strong["processed_brl"], "35000.00")
        self.assertEqual(strong["paid_brl"], "35000.00")
        self.assertIn("EXACT_TYPED_PROCUREMENT_KEY_CREATES_IDENTITY_NOT_CNPJ_AMOUNT_DATE_OBJECT", got["CAUTION_OR_LIMIT"])
        self.assertIn("ONE_PROVEN_CHAIN_NE_EXHAUSTIVE_MUNICIPAL_PROCUREMENT", got["CAUTION_OR_LIMIT"])
        self.assertIn("PAID_NE_CONTRACT_COMPLETED", got["CAUTION_OR_LIMIT"])

    def test_historical_tcesp_is_preserved_with_commitment_format_guard(self):
        got = self.execute("o que TCE e demais controles corroboram em 2026?")
        hist = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "HISTORICAL_TCESP_INDEPENDENT_CORROBORATION_WITH_FORMAT_GUARD"
        )
        self.assertEqual(hist["source_scope"], "Jan-Jul 2026")
        self.assertEqual(hist["tcesp_commitment_number"], "3286-2026")
        self.assertEqual(hist["committed_brl"], "174999.99")
        self.assertEqual(hist["paid_brl"], "17500.00")
        self.assertFalse(hist["exact_tda_to_tcesp_commitment_format_identity_claim"])
        self.assertIn("CURRENT_TDA_NE_HISTORICAL_TCESP_SNAPSHOT", got["CAUTION_OR_LIMIT"])

    def test_other_year_is_not_substituted(self):
        got = self.execute("o que TCE e demais controles corroboram em 2025?")
        self.assertEqual(got["question_id"], "CTRL_Q2")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "UNSUPPORTED")

    def test_school_context_is_not_silently_dropped(self):
        got = self.execute(
            "o que TCE e demais controles corroboram em 2026 na minha escola?",
            context_school_code="35470600",
        )
        self.assertEqual(got["question_id"], "CTRL_Q2")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "UNSUPPORTED")

    def test_proc_questions_remain_exact_v7_behavior(self):
        cases = [
            "o que a prefeitura esta comprando em 2026?",
            "quem fornece por quanto e por quanto tempo em 2026?",
            "houve aditivo apostilamento ou nova licitacao em 2026?",
        ]
        for text in cases:
            with self.subTest(text=text):
                a = self.execute(text)
                b = execute_contextual_query_v7(
                    text,
                    generated_at=GENERATED_AT,
                    software_version=SOFTWARE_VERSION,
                )
                self.assertEqual(a, b)
                self.assertIn(a["question_id"], {"PROC_Q1", "PROC_Q2", "PROC_Q3"})

    def test_existing_infra_q2_delegates_exactly_to_v7(self):
        text = "quais escolas receberam obras reformas ou equipamentos em 2026"
        a = self.execute(text)
        b = execute_contextual_query_v7(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "INFRA_Q2")

    def test_renderer_and_answer_are_deterministic(self):
        answer_a = self.execute("o que TCE e demais controles corroboram em 2026?")
        answer_b = self.execute("o que TCE e demais controles corroboram em 2026?")
        self.assertEqual(answer_a, answer_b)
        self.assertEqual(len(answer_a["answer_sha256"]), 64)
        rendered_a = render_contextual_answer_v8(answer_a)
        rendered_b = render_contextual_answer_v8(copy.deepcopy(answer_a))
        self.assertEqual(rendered_a, rendered_b)
        self.assertEqual(len(rendered_a["markdown_sha256"]), 64)
        self.assertIn("45/2026", rendered_a["markdown"])
        self.assertIn("E00010/2026", rendered_a["markdown"])
        self.assertIn("03286-01", rendered_a["markdown"])


if __name__ == "__main__":
    unittest.main()
