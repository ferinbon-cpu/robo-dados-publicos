import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "lt_formation_timing_jom_direct_discovery.v2.json"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "TASK_238_JOM_DIRECT_DISCOVERY_CANONICAL_0.8.0.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


class Task238JomDirectDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_json(CONFIG_PATH)
        cls.evidence = load_json(EVIDENCE_PATH)

    def test_exact_post_inventory_gate_base(self):
        expected = "96f4a0c81b6b358b9c57019b27bd2e4cc7706efd"
        self.assertEqual(self.cfg["base_main_sha"], expected)
        self.assertEqual(self.evidence["canonical_base_sha"], expected)
        self.assertEqual(self.cfg["issue"], 794)

    def test_exact_bounded_manifest_is_7140_through_7172(self):
        inv = self.cfg["bounded_identity_inventory"]
        self.assertEqual(inv["first_edition"], 7140)
        self.assertEqual(inv["last_edition"], 7172)
        self.assertEqual(inv["edition_count"], 33)
        self.assertTrue(inv["sequence_contiguous"])
        manifest = inv["manifest"]
        self.assertEqual(len(manifest), 33)
        self.assertEqual([row["edition"] for row in manifest], list(range(7140, 7173)))
        self.assertEqual(manifest[0]["publication_date"], "2025-12-17")
        self.assertEqual(manifest[1]["publication_date"], "2025-12-17")
        self.assertEqual(manifest[-1]["publication_date"], "2026-01-31")

    def test_index_triage_never_becomes_primary_content_proof(self):
        correction = self.cfg["methodological_correction"]
        self.assertEqual(
            correction["search_semantics"],
            "DISCOVERY_TRIAGE_ONLY_NOT_PRIMARY_CONTENT_PROOF",
        )
        self.assertFalse(self.cfg["official_archive_triage"]["absence_inference_allowed"])
        self.assertFalse(self.cfg["bounded_identity_inventory"]["content_inspection_complete"])
        self.assertFalse(
            self.cfg["bounded_identity_inventory"]["terminal_bounded_negative_result_allowed"]
        )
        self.assertIn("INDEX_SEARCH_NE_PRIMARY_CONTENT_INSPECTION", self.cfg["global_guards"])
        self.assertIn("ZERO_HIT_NE_PRIMARY_CONTENT_ABSENCE", self.cfg["global_guards"])

    def test_broad_hit_matrix_is_preserved_as_triage(self):
        hits = {
            row["term"]: row["editions"]
            for row in self.cfg["official_archive_triage"]["broad_hits"]
        }
        self.assertEqual(hits["08/2025"], [7151, 7142])
        self.assertEqual(hits["formação"], [7168, 7163])
        self.assertEqual(hits["artigo 11"], [7146])
        self.assertEqual(hits["Diretor de Escola"], [7172, 7150])

    def test_only_five_primary_candidates_remain_pending(self):
        ledger = self.cfg["candidate_ledger"]
        pending = sorted(
            row["edition"] for row in ledger if row["status"] == "PRIMARY_CONTENT_PENDING"
        )
        self.assertEqual(pending, [7142, 7150, 7151, 7163, 7168])
        self.assertEqual(
            self.cfg["result"]["pending_primary_editions"],
            [7142, 7150, 7151, 7163, 7168],
        )

    def test_7146_and_7172_have_explicit_non_index_clearance_basis(self):
        ledger = {row["edition"]: row for row in self.cfg["candidate_ledger"]}
        self.assertEqual(
            ledger[7146]["status"],
            "CLEARED_BY_TASK237_DIRECT_PRIMARY_NO_TARGET_HIT",
        )
        self.assertEqual(
            ledger[7172]["status"],
            "CLEARED_BY_INDEPENDENT_PRIMARY_CONTEXT",
        )
        self.assertTrue(ledger[7172]["source_url"].startswith("https://www.ipml.com.br/"))

    def test_divergence_and_bounded_negative_remain_fail_closed(self):
        result = self.cfg["result"]
        self.assertTrue(result["inventory_closed"])
        self.assertTrue(result["discovery_triage_complete"])
        self.assertFalse(result["primary_content_closed"])
        self.assertFalse(result["modifier_candidate_established"])
        self.assertFalse(result["bounded_negative_result"])
        self.assertEqual(
            result["audit_state"],
            "COMPLETE_BOUNDED_INVENTORY_CONTENT_INSPECTION_PENDING",
        )
        self.assertEqual(result["divergence_status"], "OPEN_UNRESOLVED")
        self.assertFalse(self.evidence["conclusion"]["bounded_negative"])

    def test_coverage_remains_unchanged(self):
        self.assertEqual(self.cfg["target"]["contextual_coverage"], "38/38_UNCHANGED")
        self.assertEqual(self.evidence["contextual_coverage"], "38/38_UNCHANGED")


if __name__ == "__main__":
    unittest.main()
