import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "config" / "education_assignment_2026_authority.v1.json"
COVERAGE = ROOT / "config" / "normative_sme_legal_coverage.v1.json"


class TestTask234EducationAssignment2026(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(ASSIGNMENT.read_text(encoding="utf-8"))
        cls.coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
        cls.coverage_items = {x["id"]: x for x in cls.coverage["items"]}
        cls.sources = cls.obj["sources"]
        cls.d_rules = {x["rule_id"]: x for x in cls.obj["decree_259_rules"]}
        cls.op_rules = {x["rule_id"]: x for x in cls.obj["sme_operational_rules"]}

    def test_canonical_target_is_task222_pending_item(self):
        target = self.obj["target"]
        self.assertEqual(target["sme_legal_id"], "SMELEGAL-018")
        self.assertEqual(target["sme_legal_item"], "Atribuição de Aula")
        self.assertEqual(target["prior_coverage_status"], "PENDENTE_CORPUS_INTEGRAL")
        self.assertEqual(self.coverage_items["SMELEGAL-018"]["status"], "PENDENTE_CORPUS_INTEGRAL")
        self.assertEqual(target["school_year_scope"], 2026)

    def test_snapshot_is_bound_to_post_task233_main(self):
        self.assertEqual(self.obj["base_main_sha"], "4eb147a448c5d390fa0675f5dbad7a28a7301315")
        self.assertEqual(self.obj["verified_at"], "2026-09-11")
        self.assertTrue(self.obj["snapshot_bound"])

    def test_decree259_identity_status_and_scope(self):
        d = self.sources["decree_259_2025"]
        self.assertEqual(d["act"], "Decreto Municipal nº 259/2025")
        self.assertEqual(d["date"], "2025-09-30")
        self.assertEqual(d["official_status_text"], "Em vigor")
        self.assertEqual(d["official_status_snapshot"], "IN_FORCE_OFFICIAL_INDEX_SNAPSHOT")
        self.assertEqual(d["administrative_process"], "34.939/2025")
        self.assertEqual(d["school_year_scope"], 2026)
        self.assertEqual(d["registration_window"], {"start": "2025-10-07", "end": "2025-10-13"})
        self.assertEqual(
            d["declared_legal_basis"],
            ["LC 461/2009 art. 31", "LC 461/2009 art. 32", "LC 461/2009 art. 33", "LC 461/2009 art. 34"],
        )

    def test_decree289_is_direct_modifier_and_in_force(self):
        d = self.sources["decree_289_2025"]
        self.assertEqual(d["act"], "Decreto Municipal nº 289/2025")
        self.assertEqual(d["date"], "2025-11-04")
        self.assertEqual(d["official_status_text"], "Em vigor")
        self.assertEqual(d["modifies"], "Decreto Municipal nº 259/2025")
        self.assertEqual(d["consolidated_trace_in_decree259"], ["Art. 1 §4", "Art. 1 §5", "Art. 1 §6", "Art. 1 §7"])

    def test_exact_assignment_fields(self):
        self.assertEqual(
            self.sources["decree_259_2025"]["fields_of_assignment"],
            ["Educação Infantil", "Ensino Fundamental", "Educação Especial", "Arte", "Educação Física"],
        )
        self.assertIn("Educação Especial, Arte, Educação Física, Ensino Fundamental, Educação Infantil", self.op_rules["SMEOP-R03"]["rule"])

    def test_decree_rule_set_is_bounded_and_article_provenanced(self):
        self.assertEqual(len(self.d_rules), 15)
        self.assertEqual(self.obj["summary"]["decree_259_rules_materialized"], 15)
        for rule in self.d_rules.values():
            self.assertTrue(rule["article"].startswith("Art"))
            self.assertIn("source", rule)
            self.assertIn("scope", rule)
        self.assertEqual(self.d_rules["D259-R09"]["article"], "Art. 6")
        self.assertIn("minutes book", self.d_rules["D259-R09"]["rule"])

    def test_scoring_exact_values_and_limits(self):
        service = self.obj["scoring"]["service_time"]
        self.assertEqual([x["points_per_day"] for x in service], [0.002, 0.001])
        titles = {x["title"]: x for x in self.obj["scoring"]["titles"]}
        self.assertEqual(titles["Concurso Público de Provas e Títulos"]["points"], 1)
        self.assertEqual(titles["Concurso Público de Provas e Títulos"]["limit"], "NO_LIMIT_PER_ELIGIBLE_CERTIFICATE")
        self.assertEqual(titles["Doutorado em Educação"]["points"], 15)
        self.assertEqual(titles["Mestrado em Educação"]["points"], 10)
        self.assertEqual(titles["Pós-graduação lato sensu em Educação"]["limit_points"], 3)
        self.assertEqual(titles["Licenciatura adicional"]["points"], 2)
        self.assertEqual(titles["Licenciatura adicional"]["limit_points"], 10)
        self.assertEqual(titles["Habilitação Específica em nível médio - Modalidade Normal"]["points"], 2)
        self.assertEqual(titles["Certidão de Frequência Docente 01/07/2024-30/06/2025"]["points"], 4)
        self.assertEqual(
            self.obj["scoring"]["tie_breakers"],
            ["Maior idade", "Maior tempo de serviço no Magistério Público Oficial", "Maior número de filhos dependentes"],
        )

    def test_classification_calendar_is_not_silently_generalized(self):
        rule = self.d_rules["D259-R14"]["rule"]
        for token in ("14 October 2025", "16 October", "17 October", "20 October", "22 October", "24 October"):
            self.assertIn(token, rule)
        self.assertEqual(self.d_rules["D259-R14"]["scope"], "classification_2026")

    def test_operational_page_cites_exact_resolution_and_publication(self):
        page = self.sources["sme_operational_page"]
        r = page["resolution_citation"]
        self.assertEqual(r["act"], "Resolução SME nº 08")
        self.assertEqual(r["date"], "2025-12-09")
        self.assertEqual(r["publication_stated_by_sme"], "Jornal Oficial de Limeira em 16/12/2025")
        self.assertEqual(r["full_original_custody"], "NOT_ACQUIRED")
        self.assertEqual(r["formal_vigency_claim"], "NOT_INFERRED_FROM_OPERATIONAL_PAGE_ALONE")

    def test_operational_rules_are_bounded_to_visible_page_content(self):
        self.assertEqual(len(self.op_rules), 11)
        self.assertEqual(self.obj["summary"]["sme_operational_rules_materialized"], 11)
        self.assertIn("art. 30", self.op_rules["SMEOP-R02"]["source_article_citation"])
        self.assertIn("art. 23 caput and §1", self.op_rules["SMEOP-R06"]["source_article_citation"])
        self.assertIn("art. 23 §2", self.op_rules["SMEOP-R07"]["source_article_citation"])
        self.assertIn("art. 11 §5(b)", self.op_rules["SMEOP-R10"]["source_article_citation"])
        self.assertIn("45 days", self.op_rules["SMEOP-R07"]["rule"])
        self.assertIn("first semester of 2026", self.op_rules["SMEOP-R10"]["rule"])

    def test_resolution_full_text_is_not_invented(self):
        limits = self.obj["source_limitations"]
        self.assertFalse(limits["resolution_08_full_original_acquired"])
        self.assertFalse(limits["resolution_08_unseen_articles_materialized"])
        self.assertFalse(limits["operational_page_is_full_norm_text"])
        self.assertFalse(limits["formal_resolution_vigency_inferred_from_page"])
        self.assertEqual(self.obj["summary"]["resolution_08_full_original_custody"], "NOT_ACQUIRED")

    def test_temporal_scope_is_2026_only(self):
        self.assertFalse(self.obj["source_limitations"]["other_school_years_authorized"])
        for rule in self.op_rules.values():
            self.assertIn("2026", rule["scope"])
        self.assertIn("NO_APPLY_2026_RULE_TO_OTHER_SCHOOL_YEARS", self.obj["global_guards"])

    def test_privacy_fields_are_explicitly_excluded(self):
        privacy = self.obj["privacy"]
        self.assertFalse(privacy["personal_data_materialized"])
        self.assertFalse(privacy["login_credentials_or_identifiers_materialized"])
        self.assertFalse(privacy["geolocation_materialized"])
        excluded = set(self.sources["sme_operational_page"]["personal_login_fields_not_materialized"])
        self.assertIn("CPF", excluded)
        self.assertIn("data de nascimento", excluded)

    def test_authority_precedence_is_official_first(self):
        self.assertEqual(self.obj["authority_precedence"][0], "PRIMARY_NORMATIVE_OFFICIAL_CONSOLIDATED")
        self.assertEqual(self.obj["authority_precedence"][-1], "DERIVED_SME_LEGAL_COVERAGE_MAP")

    def test_required_fail_closed_guards(self):
        required = {
            "CURRENT_SME_OPERATIONAL_PAGE_NE_FULL_RESOLUTION_TEXT",
            "DECREE259_CURRENT_STATUS_EM_VIGOR",
            "DECREE289_MODIFIES_DECREE259",
            "OPERATIONAL_PAGE_EXACT_ACT_CITATION_NE_BINARY_CUSTODY",
            "NO_INFERENCE_BEYOND_VISIBLE_ARTICLES",
            "NO_APPLY_2026_RULE_TO_OTHER_SCHOOL_YEARS",
            "NO_PERSONAL_DATA_MATERIALIZATION",
            "OLD_2025_ATTRIBUTION_NE_2026_RULE",
            "OFFICIAL_PRIMARY_GT_DERIVED_SME_LEGAL_FOR_CURRENT_RULE",
            "CONSOLIDATED_EXPORT_NE_OFFICIAL_GAZETTE_REPLACEMENT",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(set(self.obj["global_guards"])))

    def test_remote_effects_and_contextual_coverage_unchanged(self):
        effects = self.obj["remote_effects"]
        self.assertTrue(effects["source_network_read_only"])
        for key in ("drive_write", "serving", "publication", "schedule", "recurrence"):
            self.assertFalse(effects[key])
        self.assertEqual(self.obj["summary"]["contextual_coverage"], "38/38_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
