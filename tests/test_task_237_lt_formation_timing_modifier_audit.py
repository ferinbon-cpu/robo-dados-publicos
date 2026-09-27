import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "lt_formation_timing_modifier_audit.v1.json"
TASK235_PATH = ROOT / "config" / "education_assignment_resolution_08_2025_primary.v1.json"
TASK236_PATH = ROOT / "config" / "linguagens_tecnologias_normative_authority_chain.v1.json"
BASE_PATH = ROOT / "docs" / "evidence" / "TASK_237_CANONICAL_BASE_AFTER_TASK236_0.8.0.json"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "TASK_237_LT_FORMATION_TIMING_MODIFIER_AUDIT_0.8.0.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class Task237LtFormationTimingModifierAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_json(CONFIG_PATH)
        cls.task235 = load_json(TASK235_PATH)
        cls.task236 = load_json(TASK236_PATH)
        cls.base = load_json(BASE_PATH)
        cls.evidence = load_json(EVIDENCE_PATH)

    def test_canonical_base_is_exact_green_task236_main(self):
        expected = "53b9f3f8140bd2136ef80bb8d9ff4916151d2175"
        self.assertEqual(self.cfg["base_main_sha"], expected)
        self.assertEqual(self.base["canonical_base"]["sha"], expected)
        validation = self.base["canonical_base"]["post_merge_validation"]
        self.assertEqual(validation["offline_ci_run_number"], 1802)
        self.assertEqual(validation["offline_ci_conclusion"], "success")
        self.assertEqual(validation["unit_tests"], "success")
        self.assertEqual(validation["historical_regression"], "success")

    def test_divergence_remains_open_in_task236_and_task237(self):
        self.assertEqual(
            self.task236["task235_divergence"]["status"],
            "OPEN_UNRESOLVED",
        )
        self.assertEqual(
            self.cfg["result"]["divergence_status"],
            "OPEN_UNRESOLVED",
        )
        self.assertEqual(
            self.evidence["primary_divergence"]["status"],
            "OPEN_UNRESOLVED",
        )

    def test_bounded_window_is_explicitly_not_closed(self):
        window = self.cfg["bounded_window"]
        self.assertEqual(window["start_date"], "2025-12-17")
        self.assertEqual(window["end_date"], "2026-01-31")
        self.assertFalse(window["full_window_closed"])
        self.assertFalse(window["terminal_negative_result_allowed"])
        self.assertFalse(self.cfg["result"]["bounded_negative_result"])
        self.assertFalse(self.evidence["search_window"]["closed"])

    def test_transport_stall_cannot_become_legal_absence(self):
        scan = self.cfg["browser_scan"]
        self.assertEqual(scan["status"], "SCAN_INCOMPLETE_TRANSPORT_STALL")
        self.assertEqual(scan["run_id"], "4fc0515a-cc80-4448-ba93-2916d8d8e910")
        self.assertEqual(scan["last_observed_step"], 81)
        self.assertEqual(scan["last_observed_edition"], 7166)
        self.assertTrue(scan["remained_running_without_progress_across_repeated_waits"])
        self.assertFalse(scan["legal_absence_inference_allowed"])
        self.assertIn(
            "SCAN_INCOMPLETE_TRANSPORT_STALL_NE_BOUNDED_NEGATIVE_RESULT",
            self.cfg["global_guards"],
        )

    def test_direct_official_subset_is_exact_and_partial(self):
        fallback = self.cfg["direct_official_fallback"]
        self.assertEqual(fallback["status"], "PARTIAL_DIRECT_PRIMARY_INSPECTION")
        self.assertFalse(fallback["full_window_closed_by_fallback"])
        expected_editions = [7141, 7143, 7144, 7145, 7146, 7148, 7149]
        self.assertEqual([item["edition"] for item in fallback["editions"]], expected_editions)
        for item in fallback["editions"]:
            self.assertTrue(item["official_pdf_url"].startswith("https://ecrie.com.br/"))
            self.assertFalse(item["target_hit"])
        self.assertEqual(fallback["binary_hashes_claimed"], 0)

    def test_indexed_discovery_is_not_a_negative_legal_conclusion(self):
        indexed = self.cfg["indexed_discovery"]
        self.assertEqual(indexed["status"], "NO_INDEXED_CANDIDATE_LOCATED")
        self.assertFalse(indexed["later_official_modifier_candidate_located"])
        self.assertFalse(indexed["legal_absence_inference_allowed"])
        self.assertIn(
            "NO_INDEXED_CANDIDATE_LOCATED_NE_NO_MODIFIER_EXISTS",
            self.cfg["global_guards"],
        )

    def test_no_candidate_established_is_not_no_modifier_exists(self):
        result = self.cfg["result"]
        self.assertFalse(result["modifier_candidate_established"])
        self.assertEqual(result["audit_state"], "OPEN_UNRESOLVED_INCOMPLETE_BOUNDED_SCAN")
        self.assertIn("No modifier exists.", result["forbidden_claims"])
        self.assertIn(
            "NO_CANDIDATE_ESTABLISHED_NE_NO_MODIFIER_EXISTS",
            self.cfg["global_guards"],
        )

    def test_operational_page_cannot_silently_amend_primary_norm(self):
        self.assertEqual(
            self.cfg["authority_baseline"]["authority_rule"],
            "CURRENT_OPERATIONAL_PAGE_DOES_NOT_BY_ITSELF_AMEND_PRIMARY_NORMATIVE_TEXT",
        )
        self.assertIn(
            "OPERATIONAL_PAGE_NE_NORMATIVE_AMENDMENT",
            self.cfg["global_guards"],
        )
        self.assertFalse(self.evidence["conclusion"]["operational_page_amends_norm_claim_allowed"])

    def test_task235_primary_source_identity_is_preserved(self):
        source = self.task235["source"]
        self.assertEqual(source["edition"], 7139)
        self.assertEqual(source["publication_date"], "2025-12-16")
        self.assertEqual(source["source_identity_status"], "PROVEN_PRIMARY_OFFICIAL_PUBLICATION")
        self.assertEqual(source["binary_custody_status"], "NOT_CUSTODIED_NO_BYTE_HASH")

    def test_coverage_and_remote_effects_do_not_change(self):
        self.assertEqual(self.cfg["target"]["contextual_coverage"], "38/38_UNCHANGED")
        self.assertEqual(self.evidence["contextual_coverage"], "38/38_UNCHANGED")
        effects = self.cfg["remote_effects"]
        self.assertTrue(effects["source_network_read_only"])
        self.assertFalse(effects["drive_write"])
        self.assertFalse(effects["serving"])
        self.assertFalse(effects["publication"])
        self.assertFalse(effects["schedule"])
        self.assertFalse(effects["recurrence"])


if __name__ == "__main__":
    unittest.main()
