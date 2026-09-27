import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "lt_formation_timing_jom_direct_discovery.v3.json"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class Task238JomPrimaryClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_json(CONFIG_PATH)
        cls.evidence = load_json(EVIDENCE_PATH)

    def test_wave3_is_bound_to_post_wave2_main(self):
        expected = "760fbaa52defbb27c2d25dfa9cc98465a1e3ca55"
        self.assertEqual(self.cfg["base_main_sha"], expected)
        self.assertEqual(self.evidence["base_main_sha"], expected)
        self.assertEqual(self.cfg["issue"], 794)
        self.assertEqual(self.cfg["schema"], "LT_FORMATION_TIMING_JOM_DIRECT_DISCOVERY_V3")
        self.assertEqual(
            self.cfg["supersedes"],
            "config/lt_formation_timing_jom_direct_discovery.v2.json",
        )

    def test_complete_bounded_identity_inventory_remains_33_editions(self):
        inv = self.cfg["bounded_identity_inventory"]
        self.assertEqual(inv["first_edition"], 7140)
        self.assertEqual(inv["last_edition"], 7172)
        self.assertEqual(inv["edition_count"], 33)
        self.assertTrue(inv["sequence_contiguous"])
        self.assertTrue(inv["content_inspection_complete"])
        self.assertTrue(inv["terminal_bounded_negative_result_allowed"])
        self.assertEqual(
            [row["edition"] for row in inv["manifest"]],
            list(range(7140, 7173)),
        )

    def test_primary_probe_is_auditable_and_did_not_use_tinyfish(self):
        probe = self.cfg["primary_probe"]
        self.assertEqual(probe["run_id"], 34651289623)
        self.assertEqual(probe["artifact_id"], 10284047484)
        self.assertEqual(probe["status"], "PASS_PROBE_ALL_TARGETS_INSPECTED")
        self.assertEqual(probe["missing_target_editions"], [])
        self.assertEqual(probe["extraction_errors_total"], 0)
        self.assertFalse(probe["tinyfish_used"])
        self.assertFalse(self.evidence["runtime"]["tinyfish_used_for_primary_closure"])

    def test_three_wave3_primary_documents_have_exact_hashes(self):
        ledger = {row["edition"]: row for row in self.cfg["candidate_ledger"]}
        expected = {
            7142: (
                "4c90b13d6ba6360a142e3c287ce45a65e2a47fa52068cad9847420baf9791ced",
                243,
                141361660,
            ),
            7151: (
                "ec298a6cff290723c97d24c291e36ef2c2044713b0fc5082b4560329e1d1dab8",
                125,
                44002985,
            ),
            7168: (
                "bb224c0c975e26989bab6932726ae6aa900d729a1a3344ecc6316ca578140d09",
                70,
                11091327,
            ),
        }
        for edition, (sha256, pages, byte_count) in expected.items():
            row = ledger[edition]
            self.assertEqual(row["status"], "CLEARED_BY_COMPLETE_PRIMARY_PDF_INSPECTION")
            self.assertEqual(row["sha256"], sha256)
            self.assertEqual(row["pdf_page_count"], pages)
            self.assertEqual(row["bytes"], byte_count)

    def test_exact_target_terms_are_absent_from_three_primary_candidates(self):
        rows = {row["edition"]: row for row in self.evidence["primary_inspections"]}
        expected_terms = {
            "Linguagens e Tecnologias",
            "PSS 04/2025",
            "Resolução SME",
            "Resolução nº 08",
            "Resolução 08/2025",
            "primeiro semestre",
        }
        for edition in (7142, 7151, 7168):
            self.assertEqual(set(rows[edition]["exact_target_hits"]), expected_terms)
            self.assertTrue(all(value == 0 for value in rows[edition]["exact_target_hits"].values()))
            self.assertEqual(rows[edition]["extraction_errors"], [])

    def test_broad_hits_are_cleared_by_context_not_by_index_silence(self):
        rows = {row["edition"]: row for row in self.evidence["primary_inspections"]}
        self.assertEqual(rows[7142]["trigger_hit_count"], 3)
        self.assertEqual(rows[7151]["trigger_hit_count"], 3)
        self.assertEqual(rows[7168]["trigger_hit_count"], 17)
        self.assertEqual(
            [item["pdf_page"] for item in rows[7142]["trigger_contexts"]],
            [73, 180, 228],
        )
        self.assertEqual(
            [item["pdf_page"] for item in rows[7151]["trigger_contexts"]],
            [76, 117, 125],
        )
        self.assertEqual(rows[7168]["related_but_non_target_hits"]["Linguagens"], [36, 37])
        self.assertEqual(rows[7168]["related_but_non_target_hits"]["Tecnologias"], [3, 6, 7])

    def test_all_candidate_editions_are_reconciled_and_none_pending(self):
        reconciled = self.evidence["reconciled_candidate_ledger"]
        self.assertEqual(
            reconciled["candidate_editions"],
            [7142, 7146, 7150, 7151, 7163, 7168, 7172],
        )
        self.assertEqual(reconciled["cleared_editions"], reconciled["candidate_editions"])
        self.assertEqual(reconciled["pending_editions"], [])
        self.assertFalse(reconciled["modifier_candidate_established"])
        pending = [
            row["edition"]
            for row in self.cfg["candidate_ledger"]
            if "PENDING" in row["status"]
        ]
        self.assertEqual(pending, [])

    def test_terminal_bounded_negative_is_allowed_but_global_nonexistence_is_not(self):
        result = self.cfg["result"]
        self.assertTrue(result["inventory_closed"])
        self.assertTrue(result["discovery_triage_complete"])
        self.assertTrue(result["primary_content_closed"])
        self.assertEqual(result["pending_primary_editions"], [])
        self.assertFalse(result["modifier_candidate_established"])
        self.assertTrue(result["bounded_negative_result"])
        self.assertEqual(
            result["audit_state"],
            "BOUNDED_WINDOW_COMPLETE_NO_MODIFIER_CANDIDATE_LOCATED",
        )
        self.assertTrue(self.evidence["conclusion"]["bounded_negative_result"])
        self.assertIn("BOUNDED_NEGATIVE_NE_GLOBAL_NONEXISTENCE", self.cfg["global_guards"])
        self.assertFalse(
            self.cfg["methodological_contract"]["global_nonexistence_inference_allowed"]
        )

    def test_divergence_stays_open_and_operational_page_does_not_amend_norm(self):
        self.assertEqual(self.cfg["result"]["divergence_status"], "OPEN_UNRESOLVED")
        self.assertEqual(self.evidence["conclusion"]["divergence_status"], "OPEN_UNRESOLVED")
        self.assertFalse(
            self.cfg["methodological_contract"][
                "operational_page_normative_amendment_inference_allowed"
            ]
        )
        forbidden = self.evidence["conclusion"]["forbidden_claims"]
        self.assertIn("No modifier exists anywhere.", forbidden)
        self.assertIn(
            "The operational SME page itself amended Resolução SME nº 08/2025.",
            forbidden,
        )

    def test_contextual_coverage_is_unchanged(self):
        self.assertEqual(self.cfg["contextual_coverage"], "38/38_UNCHANGED")
        self.assertEqual(self.cfg["target"]["contextual_coverage"], "38/38_UNCHANGED")
        self.assertEqual(self.evidence["contextual_coverage"], "38/38_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
