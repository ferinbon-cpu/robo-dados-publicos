import json
from datetime import date
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHAIN = ROOT / "config" / "linguagens_tecnologias_normative_authority_chain.v1.json"
TASK235 = ROOT / "config" / "education_assignment_resolution_08_2025_primary.v1.json"


class TestTask236LTNormativeAuthorityChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(CHAIN.read_text(encoding="utf-8"))
        cls.prior = json.loads(TASK235.read_text(encoding="utf-8"))
        cls.nodes = {row["id"]: row for row in cls.obj["nodes"]}

    def test_exact_chain_shape(self):
        self.assertEqual(self.obj["summary"]["chain_nodes"], 5)
        self.assertEqual(len(self.obj["nodes"]), 5)
        self.assertEqual(
            [row["order"] for row in self.obj["nodes"]],
            [1, 2, 3, 4, 5],
        )
        self.assertEqual(self.obj["summary"]["official_journal_primary_nodes"], 4)
        self.assertEqual(self.obj["summary"]["current_operational_nodes"], 1)

    def test_dates_are_chronological_for_primary_acts(self):
        primary = self.obj["nodes"][:4]
        dates = [date.fromisoformat(row["act_date"]) for row in primary]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(dates[0].isoformat(), "2025-09-23")
        self.assertEqual(dates[-1].isoformat(), "2025-12-09")

    def test_portaria_26_is_preparatory_not_curriculum_enactment(self):
        node = self.nodes["LT-PORTARIA-SME-26-2025"]
        self.assertEqual(node["journal_edition"], 7081)
        self.assertEqual(node["source_role"], "PRIMARY_ADMINISTRATIVE_PREPARATORY_ACT")
        self.assertEqual(node["proven_rules"][0]["article"], "Art. 1º")
        self.assertIn("Comissão Mista", node["proven_rules"][0]["rule"])
        self.assertIn("estruturar e regulamentar", node["proven_rules"][0]["rule"])
        self.assertEqual(node["guard"], "NO_UNSEEN_PORTARIA_ARTICLE_RECONSTRUCTION")

    def test_deliberation_article8_is_exactly_materialized_from_primary_pdf(self):
        node = self.nodes["LT-DELIB-CONJUNTA-001-2025"]
        self.assertEqual(node["journal_edition"], 7107)
        self.assertEqual(node["source_role"], "PRIMARY_CURRICULAR_NORMATIVE_ACT")
        self.assertIn("Institui a disciplina extracurricular", node["title_proven"])
        self.assertEqual(node["publication_start_page"], 6)
        self.assertEqual(node["publication_end_page"], 11)
        self.assertTrue(node["text_recovery"]["primary_pdf_identity_proven"])
        self.assertFalse(node["text_recovery"]["binary_bytes_custodied"])
        self.assertTrue(node["text_recovery"]["article_outline_is_not_exact_article_text"])
        art8 = node["article_8"]
        self.assertTrue(art8["existence_and_relevance_proven_by_later_decree"])
        self.assertTrue(art8["exact_text_materialized"])
        self.assertEqual(art8["page"], 9)
        self.assertEqual(art8["status"], "EXACT_ARTICLE_TEXT_RECOVERED_FROM_PRIMARY_OFFICIAL_PDF")
        self.assertTrue(art8["exact_text"].startswith("Art. 8º Em função da inclusão"))
        self.assertIn("2 (duas) horas/aula semanais", art8["exact_text"])
        self.assertIn("Cultura Corporal e Movimento", art8["exact_text"])
        self.assertIn("Arte e Educação Física", art8["exact_text"])
        self.assertTrue(self.obj["summary"]["deliberation_article_8_exact_text_materialized"])
        self.assertTrue(self.obj["summary"]["deliberation_publication_page_span_proven"])

    def test_decree_289_preserves_exact_cross_reference(self):
        node = self.nodes["LT-DECRETO-289-2025"]
        self.assertEqual(node["journal_edition"], 7111)
        cross = node["explicit_cross_reference"]
        self.assertEqual(cross["act"], "Deliberação Conjunta CME/SME nº 001, de 28 de outubro de 2025")
        self.assertEqual(cross["specific_reference"], "art. 8º")
        self.assertEqual(cross["relationship"], "EXPRESS_OFFICIAL_CROSS_REFERENCE")
        self.assertIn("6 e 7 de novembro de 2025", node["proven_rule"]["rule"])
        self.assertIn("Arte e Educação Física", node["proven_rule"]["rule"])

    def test_relationship_edges_do_not_create_fake_amendments(self):
        edges = self.obj["relationship_edges"]
        self.assertEqual(len(edges), 4)
        self.assertEqual(
            edges[0]["relationship"],
            "PREPARATORY_GOVERNANCE_TO_FORMAL_CURRICULAR_INSTITUTION",
        )
        self.assertEqual(
            edges[1]["proof_strength"],
            "EXACT_OFFICIAL_CROSS_REFERENCE_TO_ART8",
        )
        self.assertIn("No direct amendment relationship", edges[2]["not_claimed"])
        self.assertIn("not an amendment instrument", edges[3]["not_claimed"])
        self.assertEqual(
            self.obj["chain_semantics"]["type"],
            "AUTHORITY_AND_IMPLEMENTATION_CHAIN_NOT_AUTOMATIC_AMENDMENT_CHAIN",
        )

    def test_resolution_08_node_links_to_task235_primary_materialization(self):
        node = self.nodes["LT-RESOLUCAO-SME-08-2025"]
        self.assertEqual(node["journal_edition"], 7139)
        self.assertEqual(
            node["canonical_config"],
            "config/education_assignment_resolution_08_2025_primary.v1.json",
        )
        self.assertEqual(self.prior["source"]["edition"], 7139)
        self.assertEqual(self.prior["summary"]["articles_indexed"], 34)
        self.assertTrue(self.prior["summary"]["primary_text_recovered"])

    def test_current_operational_page_is_lower_authority(self):
        node = self.nodes["LT-SME-OPERATIONAL-PAGE-2026"]
        self.assertEqual(node["source_role"], "OFFICIAL_CURRENT_OPERATIONAL_WORKFLOW")
        self.assertEqual(
            node["authority_limit"],
            "PROVES_CURRENT_WEB_WORKFLOW_WHERE_OBSERVED_BUT_DOES_NOT_BY_ITSELF_AMEND_PRIMARY_NORMATIVE_TEXT",
        )
        precedence = self.obj["authority_precedence"]
        self.assertLess(
            precedence.index("EXACT_PRIMARY_NORMATIVE_TEXT_WITH_ARTICLE_PROVENANCE"),
            precedence.index("OFFICIAL_CURRENT_OPERATIONAL_PAGE_FOR_OBSERVED_WORKFLOW"),
        )

    def test_task235_divergence_remains_open(self):
        divergence = self.obj["task235_divergence"]
        self.assertEqual(divergence["id"], "LT_FORMATION_TIMING_DIVERGENCE")
        self.assertEqual(divergence["status"], "OPEN_UNRESOLVED")
        self.assertEqual(
            divergence["chain_effect"],
            "THE_AUTHORITY_CHAIN_DOES_NOT_RESOLVE_THE_DIVERGENCE",
        )
        self.assertEqual(
            divergence["search_failure_meaning"],
            "NO_REPEAL_OR_AMENDMENT_INFERENCE_ALLOWED",
        )
        self.assertTrue(self.prior["summary"]["lt_timing_divergence_open"])
        self.assertTrue(self.obj["summary"]["lt_formation_timing_divergence_open"])
        self.assertIn("Do not use art. 8º", self.nodes["LT-DELIB-CONJUNTA-001-2025"]["article_8"]["forbidden_claim"])

    def test_no_binary_hash_is_invented(self):
        self.assertEqual(self.obj["summary"]["binary_hashes_claimed"], 0)
        for node in self.obj["nodes"][:3]:
            self.assertEqual(node["binary_custody_status"], "NOT_CUSTODIED_NO_BYTE_HASH")
            self.assertNotIn("sha256", node)

    def test_required_fail_closed_guards(self):
        required = {
            "AUTHORITY_CHAIN_NE_AMENDMENT_CHAIN",
            "DELIB_ARTICLE_TEXT_NE_PROVEN_UNTIL_PRIMARY_TEXT_RECOVERED",
            "DELIB_ART8_PAGE_PROVENANCE_REQUIRED",
            "DELIB_OTHER_ARTICLES_NE_EXACT_TEXT_UNLESS_SEPARATELY_RECOVERED",
            "DECREE289_CROSS_REFERENCE_TO_DELIB_ART8_MUST_BE_PRESERVED",
            "DECREE289_CROSS_REFERENCE_NE_FULL_TEXT_OF_DELIB_ART8",
            "OPERATIONAL_PAGE_NE_NORMATIVE_AMENDMENT",
            "LT_FORMATION_TIMING_DIVERGENCE_REMAINS_OPEN_UNLESS_EXACT_MODIFIER_FOUND",
            "SEARCH_FAILURE_NE_NO_MODIFIER_EXISTS",
            "PRIMARY_TEXT_GT_DERIVED_SUMMARY",
            "NO_BINARY_HASH_INVENTION",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(set(self.obj["global_guards"])))

    def test_remote_effects_and_coverage(self):
        effects = self.obj["remote_effects"]
        self.assertTrue(effects["source_network_read_only"])
        for key in ("drive_write", "serving", "publication", "schedule", "recurrence"):
            self.assertFalse(effects[key])
        self.assertEqual(self.obj["summary"]["contextual_coverage"], "38/38_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
