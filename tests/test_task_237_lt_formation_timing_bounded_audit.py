import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "config" / "lt_formation_timing_modifier_bounded_audit.v1.json"
UPSTREAM = ROOT / "config" / "linguagens_tecnologias_normative_authority_chain.v1.json"


class TestTask237LTFormationTimingBoundedAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(AUDIT.read_text(encoding="utf-8"))
        cls.upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))

    def test_exact_target_and_base(self):
        self.assertEqual(self.obj["task"], "TASK_237")
        self.assertEqual(self.obj["issue"], 792)
        self.assertEqual(self.obj["base_main_sha"], "53b9f3f8140bd2136ef80bb8d9ff4916151d2175")
        self.assertEqual(self.obj["target"]["divergence_id"], "LT_FORMATION_TIMING_DIVERGENCE")
        self.assertEqual(self.obj["target"]["upstream_status_required"], "OPEN_UNRESOLVED")
        self.assertEqual(self.upstream["task235_divergence"]["status"], "OPEN_UNRESOLVED")

    def test_bounded_window_is_exact(self):
        window = self.obj["bounded_window"]
        self.assertEqual(window["start_date"], "2025-12-17")
        self.assertEqual(window["end_date"], "2026-01-31")
        self.assertEqual(window["official_index_total_items_observed"], 33)
        self.assertIn("limeira.sp.gov.br/jornaloficial", window["official_archive_url"])
        self.assertIn("dataDe=17%2F12%2F2025", window["filtered_archive_url"])
        self.assertIn("dataAte=31%2F01%2F2026", window["filtered_archive_url"])

    def test_search_is_explicitly_in_progress_not_negative(self):
        execution = self.obj["execution"]
        self.assertEqual(execution["status"], "SEARCH_IN_PROGRESS")
        self.assertFalse(execution["browser_run_terminal"])
        self.assertFalse(execution["complete_window_inspection_proven"])
        self.assertFalse(execution["candidate_ledger_final"])
        self.assertFalse(execution["bounded_negative_result_allowed"])
        self.assertEqual(self.obj["current_evidence"]["current_result"], "NO_FINAL_RESULT_WHILE_SEARCH_IN_PROGRESS")
        self.assertFalse(self.obj["summary"]["search_terminal"])
        self.assertFalse(self.obj["summary"]["bounded_negative_final"])
        self.assertIsNone(self.obj["summary"]["exact_modifier_candidates_final"])

    def test_progress_editions_are_non_exhaustive(self):
        progress = self.obj["execution"]["progress_observations_non_exhaustive"]
        editions = progress["editions_seen_during_browser_progress"]
        self.assertGreater(len(editions), 0)
        self.assertIn(7172, editions)
        self.assertIn(7166, editions)
        self.assertIn("MUST NOT", progress["meaning"])
        self.assertLess(len(editions), self.obj["bounded_window"]["official_index_total_items_observed"])

    def test_required_search_targets_are_preserved(self):
        targets = set(self.obj["search_targets"])
        required = {
            "Resolução SME nº 08/2025",
            "art. 11 §5º(b)",
            "PSS 04/2025",
            "formação em Linguagens e Tecnologias",
            "retificação",
            "ao longo do 1º semestre letivo de 2026",
        }
        self.assertTrue(required.issubset(targets))

    def test_result_semantics_are_fail_closed(self):
        semantics = self.obj["result_semantics"]
        self.assertIn("completed inspected window", semantics["bounded_negative"])
        self.assertIn("not amendment/repeal/absence proof", semantics["search_failure"])
        self.assertIn("not by itself a normative amendment instrument", semantics["operational_page"])

    def test_divergence_remains_open(self):
        self.assertTrue(self.obj["summary"]["lt_formation_timing_divergence_open"])
        self.assertEqual(
            self.upstream["task235_divergence"]["chain_effect"],
            "THE_AUTHORITY_CHAIN_DOES_NOT_RESOLVE_THE_DIVERGENCE",
        )

    def test_required_guards(self):
        required = {
            "SEARCH_IN_PROGRESS_NE_BOUNDED_NEGATIVE_RESULT",
            "PARTIAL_EDITION_PROGRESS_NE_COMPLETE_WINDOW_INSPECTION",
            "NO_CANDIDATE_LOCATED_NE_NO_MODIFIER_EXISTS",
            "SEARCH_FAILURE_NE_NO_MODIFIER_EXISTS",
            "OPERATIONAL_PAGE_NE_NORMATIVE_AMENDMENT",
            "PRIMARY_TEXT_GT_OPERATIONAL_PAGE_FOR_NORMATIVE_WORDING",
            "LT_FORMATION_TIMING_DIVERGENCE_REMAINS_OPEN_UNLESS_EXACT_MODIFIER_FOUND",
            "NO_BINARY_HASH_INVENTION",
            "NO_CONTEXTUAL_COVERAGE_CHANGE",
        }
        self.assertTrue(required.issubset(set(self.obj["global_guards"])))

    def test_no_hash_invention_and_no_remote_effects(self):
        self.assertEqual(self.obj["summary"]["binary_hashes_claimed"], 0)
        effects = self.obj["remote_effects"]
        self.assertTrue(effects["source_network_read_only"])
        for key in ("drive_write", "serving", "publication", "schedule", "recurrence"):
            self.assertFalse(effects[key])
        self.assertEqual(self.obj["summary"]["contextual_coverage"], "38/38_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
