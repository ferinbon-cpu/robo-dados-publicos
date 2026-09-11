import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "config" / "lt_formation_timing_modifier_audit.v1.json"
V2_PATH = ROOT / "config" / "lt_formation_timing_modifier_audit.v2.json"
TASK235_PATH = ROOT / "config" / "education_assignment_resolution_08_2025_primary.v1.json"
BASE_PATH = ROOT / "docs" / "evidence" / "TASK_238_CANONICAL_BASE_AFTER_TASK237_0.8.0.json"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "TASK_238_JOM_DIRECT_BOUNDED_CLOSE_0.8.0.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class Task238JomDirectBoundedCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v1 = load_json(V1_PATH)
        cls.v2 = load_json(V2_PATH)
        cls.task235 = load_json(TASK235_PATH)
        cls.base = load_json(BASE_PATH)
        cls.evidence = load_json(EVIDENCE_PATH)

    def test_canonical_base_is_exact_task237_main(self):
        expected = "d678e521a6a3290ea1b51163a9433954e815fa07"
        self.assertEqual(self.v2["base_main_sha"], expected)
        self.assertEqual(self.base["canonical_base"]["sha"], expected)
        validation = self.base["canonical_base"]["post_merge_validation"]
        self.assertEqual(validation["offline_ci_run_number"], 1804)
        self.assertEqual(validation["offline_ci_conclusion"], "success")
        self.assertEqual(validation["unit_tests"], "success")
        self.assertEqual(validation["historical_regression"], "success")

    def test_task237_history_remains_incomplete_and_unchanged(self):
        self.assertFalse(self.v1["bounded_window"]["full_window_closed"])
        self.assertFalse(self.v1["result"]["bounded_negative_result"])
        self.assertEqual(
            self.v1["result"]["audit_state"],
            "OPEN_UNRESOLVED_INCOMPLETE_BOUNDED_SCAN",
        )
        self.assertEqual(
            self.v2["supersedes_for_current_bounded_state"],
            "config/lt_formation_timing_modifier_audit.v1.json",
        )

    def test_official_archive_contract_is_reproducible_get(self):
        interface = self.v2["direct_archive_interface"]
        self.assertEqual(interface["official_host"], "https://limeira.sp.gov.br")
        self.assertEqual(interface["path"], "/jornaloficial/")
        self.assertEqual(interface["method"], "GET")
        self.assertEqual(
            interface["query_parameters"],
            ["dataDe", "dataAte", "numeroEdicao", "busca"],
        )
        self.assertEqual(
            interface["status"],
            "PROVEN_REPRODUCIBLE_OFFICIAL_ARCHIVE_SEARCH",
        )

    def test_bounded_window_is_closed_over_exact_contiguous_editions(self):
        window = self.v2["bounded_window"]
        self.assertEqual(window["start_date"], "2025-12-17")
        self.assertEqual(window["end_date"], "2026-01-31")
        self.assertEqual(window["first_edition"], 7140)
        self.assertEqual(window["last_edition"], 7172)
        self.assertEqual(window["edition_count"], 33)
        self.assertTrue(window["edition_sequence_contiguous"])
        self.assertTrue(window["full_window_closed"])
        self.assertTrue(window["terminal_bounded_negative_result_allowed"])

        manifest = self.v2["edition_manifest"]
        self.assertEqual(len(manifest), 33)
        self.assertEqual(
            [item["edition"] for item in manifest],
            list(range(7140, 7173)),
        )
        self.assertEqual(manifest[0]["publication_date"], "2025-12-17")
        self.assertEqual(manifest[-1]["publication_date"], "2026-01-31")
        self.assertEqual(
            [item["edition"] for item in manifest if item["publication_date"] == "2025-12-17"],
            [7140, 7141],
        )

    def test_target_searches_are_zero_hit_in_bounded_window(self):
        matrix = {row["term"]: row for row in self.v2["search_matrix"]}
        expected_zero = {
            "Linguagens e Tecnologias",
            "Linguagens",
            "Tecnologias",
            "PSS 04/2025",
            "Resolução SME",
            "Resolução nº 08",
            "Resolução 08/2025",
            "primeiro semestre",
            "parágrafo 5º",
        }
        for term in expected_zero:
            self.assertIn(term, matrix)
            self.assertEqual(matrix[term]["result_count"], 0)
            self.assertEqual(matrix[term]["candidate_editions"], [])

    def test_broad_hits_are_bounded_and_classified(self):
        matrix = {row["term"]: row for row in self.v2["search_matrix"]}
        self.assertEqual(matrix["08/2025"]["candidate_editions"], [7151, 7142])
        self.assertEqual(matrix["formação"]["candidate_editions"], [7168, 7163])
        self.assertEqual(matrix["artigo 11"]["candidate_editions"], [7146])
        self.assertEqual(matrix["Diretor de Escola"]["candidate_editions"], [7172, 7150])

        ledger = self.v2["candidate_ledger"]
        self.assertTrue(ledger)
        for item in ledger:
            self.assertFalse(item["modifier_candidate"])
            self.assertIn(item["edition"], range(7140, 7173))

    def test_article_11_hit_aligns_with_task237_direct_inspection(self):
        fallback = self.v1["direct_official_fallback"]["editions"]
        edition_7146 = next(item for item in fallback if item["edition"] == 7146)
        self.assertFalse(edition_7146["target_hit"])
        matrix = {row["term"]: row for row in self.v2["search_matrix"]}
        self.assertEqual(matrix["artigo 11"]["candidate_editions"], [7146])

    def test_bounded_negative_does_not_become_universal_absence(self):
        result = self.v2["result"]
        self.assertFalse(result["modifier_candidate_established"])
        self.assertTrue(result["bounded_negative_result"])
        self.assertEqual(
            result["bounded_result_code"],
            "NO_CANDIDATE_LOCATED_IN_BOUNDED_WINDOW",
        )
        self.assertEqual(
            result["audit_state"],
            "BOUNDED_WINDOW_COMPLETE_NO_MODIFIER_CANDIDATE_LOCATED",
        )
        self.assertEqual(result["divergence_status"], "OPEN_UNRESOLVED")
        self.assertIn("No modifier exists anywhere.", result["forbidden_claims"])
        self.assertIn(
            "NO_CANDIDATE_LOCATED_IN_BOUNDED_WINDOW_NE_NO_MODIFIER_EXISTS",
            self.v2["global_guards"],
        )
        self.assertIn(
            "BOUNDED_NEGATIVE_NE_UNIVERSAL_LEGAL_ABSENCE",
            self.v2["global_guards"],
        )

    def test_primary_authority_boundary_is_preserved(self):
        self.assertEqual(self.task235["source"]["edition"], 7139)
        self.assertEqual(self.task235["source"]["publication_date"], "2025-12-16")
        self.assertEqual(
            self.v2["authority_baseline"]["authority_rule"],
            "CURRENT_OPERATIONAL_PAGE_DOES_NOT_BY_ITSELF_AMEND_PRIMARY_NORMATIVE_TEXT",
        )
        self.assertFalse(
            self.evidence["conclusion"]["operational_page_amends_norm_claim_allowed"]
        )

    def test_transport_failure_is_not_negative_evidence(self):
        transport = self.v2["transport_notes"]
        self.assertEqual(
            transport["direct_pdf_fetch_for_new_broad_hits"],
            "target_unreachable observed",
        )
        self.assertIn(
            "TRANSPORT_FAILURE_NE_LEGAL_ABSENCE",
            self.v2["global_guards"],
        )
        self.assertFalse(
            self.evidence["transport_observation"]["used_as_negative_evidence"]
        )

    def test_coverage_and_remote_effects_remain_unchanged(self):
        self.assertEqual(self.v2["target"]["contextual_coverage"], "38/38_UNCHANGED")
        self.assertEqual(self.evidence["contextual_coverage"], "38/38_UNCHANGED")
        effects = self.v2["remote_effects"]
        self.assertTrue(effects["source_network_read_only"])
        self.assertFalse(effects["drive_write"])
        self.assertFalse(effects["serving"])
        self.assertFalse(effects["publication"])
        self.assertFalse(effects["schedule"])
        self.assertFalse(effects["recurrence"])


if __name__ == "__main__":
    unittest.main()
