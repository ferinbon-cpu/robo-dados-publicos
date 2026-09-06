import unittest

from robo_dados_publicos.router.observatory import (
    Task175Stop,
    coverage_summary,
    route_observatory_question,
    validate_contracts,
)


class TestTask175UnifiedObservatoryQueryLayer(unittest.TestCase):
    def test_contracts_pass_and_cover_all_domains(self):
        got = validate_contracts()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["domain_count"], 15)
        self.assertGreaterEqual(got["scenario_count"], 5)
        self.assertFalse(got["network"])

    def test_learning_question_routes_to_school_numeric_sources_with_causal_guard(self):
        got = route_observatory_question(
            "LEARNING_FLOW",
            question_text="Como está o IDEB e o SAEB da minha escola nos últimos anos?",
            school_or_unit="CEIEF EXEMPLO",
        )
        self.assertEqual(got["route_mode"], "NUMERIC")
        self.assertIn("IDEB", got["deterministic_number_candidates"])
        self.assertIn("SAEB", got["deterministic_number_candidates"])
        self.assertIn("CENSO_ESCOLAR", got["deterministic_number_candidates"])
        self.assertFalse(got["guards"]["statistical_association_proves_causality"])
        self.assertTrue(got["guards"]["ranking_without_context_requires_caution"])
        self.assertFalse(got["question_text_is_truth_source"])

    def test_school_reform_becomes_hybrid_cross_layer_plan(self):
        got = route_observatory_question(
            "SCHOOLS_INFRASTRUCTURE",
            question_text="Quais reformas e obras aconteceram nas escolas e quanto foi gasto?",
            timeframe="2026",
        )
        self.assertEqual(got["route_mode"], "HYBRID")
        scenario_ids = [x["id"] for x in got["matched_scenarios"]]
        self.assertIn("SCHOOL_REFORM", scenario_ids)
        families = [x["source_family"] for x in got["source_plan"]]
        self.assertIn("JORNAL_OFICIAL", families)
        self.assertIn("PROCUREMENT", families)
        self.assertIn("MUNICIPAL_CONTRACTS", families)
        self.assertIn("TCE_SP_EXPENSES", families)
        self.assertIn("CENSO_ESCOLAR", families)
        self.assertIn("TCE_SP_EXPENSES", got["query_ready_numeric_sources"])
        self.assertIn("JORNAL_OFICIAL", got["query_ready_document_sources"])
        self.assertFalse(got["joins"]["weak_can_create_identity"])

    def test_school_transport_uses_procurement_accounting_finance_and_denominator_sources(self):
        got = route_observatory_question(
            "PROCUREMENT_CONTRACTS",
            question_text="Quanto custa o transporte escolar, quais contratos existem e quantos alunos são atendidos?",
        )
        self.assertEqual(got["route_mode"], "HYBRID")
        scenario_ids = [x["id"] for x in got["matched_scenarios"]]
        self.assertIn("SCHOOL_TRANSPORT", scenario_ids)
        families = [x["source_family"] for x in got["source_plan"]]
        for family in ("JORNAL_OFICIAL", "PROCUREMENT", "PNCP", "TCE_SP_EXPENSES", "SIOPE", "CENSO_ESCOLAR"):
            self.assertIn(family, families)
        self.assertIn("PNCP", got["query_ready_numeric_sources"])
        self.assertIn("TCE_SP_EXPENSES", got["query_ready_numeric_sources"])

    def test_financing_question_prefers_proven_current_fiscal_surfaces(self):
        got = route_observatory_question(
            "FINANCING",
            question_text="Quanto Limeira gastou com educação e quanto veio do Fundeb?",
            timeframe="2026",
        )
        self.assertEqual(got["route_mode"], "NUMERIC")
        self.assertIn("TCE_SP_EXPENSES", got["query_ready_numeric_sources"])
        self.assertIn("SIOPE", got["query_ready_numeric_sources"])
        self.assertIn("SICONFI_STN", got["query_ready_numeric_sources"])
        self.assertIn("FUNDEB", got["query_ready_numeric_sources"])
        tda = next(x for x in got["source_plan"] if x["source_family"] == "TDA_LIMEIRA")
        self.assertEqual(tda["readiness_score"], 0)
        self.assertTrue(any(x["source_family"] == "TDA_LIMEIRA" for x in got["evidence_gaps"]))

    def test_norm_question_routes_to_documents_and_does_not_infer_execution(self):
        got = route_observatory_question(
            "NORMS_SCHOOL_FUNCTIONING",
            question_text="Que norma mudou o calendário escolar e a atribuição de aulas?",
        )
        self.assertIn(got["route_mode"], {"DOCUMENT", "HYBRID"})
        self.assertIn("JORNAL_OFICIAL", got["query_ready_document_sources"])
        self.assertFalse(got["guards"]["jom_publication_proves_accounting_execution"])
        self.assertFalse(got["guards"]["semantic_similarity_creates_identity"])

    def test_personnel_question_is_hybrid_and_preserves_source_gaps(self):
        got = route_observatory_question(
            "TEACHERS_WORKFORCE",
            question_text="Quantos professores há e quais nomeações ou concursos saíram?",
        )
        self.assertEqual(got["route_mode"], "HYBRID")
        scenario_ids = [x["id"] for x in got["matched_scenarios"]]
        self.assertIn("PERSONNEL", scenario_ids)
        self.assertIn("JORNAL_OFICIAL", got["query_ready_document_sources"])
        self.assertTrue(any(x["source_family"] == "PERSONNEL_TRANSPARENCY" for x in got["evidence_gaps"]))

    def test_unknown_domain_fails_closed(self):
        with self.assertRaisesRegex(Task175Stop, "TASK175_UNKNOWN_DOMAIN"):
            route_observatory_question("UNKNOWN_DOMAIN")

    def test_answer_contract_is_complete_and_stable(self):
        got = route_observatory_question("TRANSPARENCY_CONTROL")
        self.assertEqual(
            got["answer_contract"],
            [
                "NUMBER_OR_FACT",
                "TIME_REFERENCE",
                "COMPARISON_OR_TREND",
                "PLAIN_LANGUAGE_EXPLANATION",
                "SOURCE_AND_PROVENANCE",
                "CAUTION_OR_LIMIT",
            ],
        )

    def test_coverage_summary_has_all_fifteen_domains(self):
        got = coverage_summary()
        self.assertEqual(got["domain_count"], 15)
        self.assertTrue(got["all_domains_have_explicit_plan"])
        self.assertEqual(sum(got["counts"].values()), 15)
        self.assertEqual(len(got["domains"]), 15)
        self.assertTrue(all(x["coverage_status"] in {"READY_CORE", "PARTIAL", "BLOCKED_OR_UNREGISTERED"} for x in got["domains"]))


if __name__ == "__main__":
    unittest.main()
