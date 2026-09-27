from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "config/task162_pncp_modality9_stable_id_recovery_guard.v1.json"
E = ROOT / "docs/evidence/TASK_162_PNCP_MODALITY9_STABLE_ID_RECOVERY_GUARD_0.8.0.json"


class TestTask162(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))
        cls.e = json.loads(E.read_text(encoding="utf-8"))

    def test_candidate_593_is_not_promoted(self):
        x = self.c["candidate_i00084"]
        self.assertEqual(593, x["chronological_sequence_candidate"])
        self.assertEqual("UNCONFIRMED_CHRONOLOGICAL_CANDIDATE", x["candidate_status"])
        self.assertFalse(x["numeroControlePNCP_confirmed"])
        self.assertFalse(self.e["epistemic_closure"]["sequence_593_promoted_to_numeroControlePNCP"])

    def test_chronology_and_gap_are_insufficient(self):
        g = self.c["guard"]
        self.assertTrue(g["chronology_alone_cannot_confirm_stable_id"])
        self.assertTrue(g["adjacent_sequence_gap_cannot_confirm_stable_id"])
        self.assertTrue(g["search_index_snippet_cannot_confirm_stable_id"])
        self.assertTrue(g["stable_id_requires_direct_source_or_exact_cross_source_identity"])

    def test_dns_failure_is_transport_unavailable(self):
        t = self.c["transport_attempt"]
        self.assertEqual("DNS_RESOLUTION_FAILURE_PRE_SOURCE", t["result"])
        self.assertFalse(t["source_reached"])
        self.assertFalse(t["source_data_observed"])
        self.assertEqual("SOURCE_TRANSPORT_UNAVAILABLE", t["required_semantics"])
        self.assertFalse(t["no_match_allowed"])
        self.assertFalse(self.e["epistemic_closure"]["pncp_no_match_created"])

    def test_school_pass_stays_education_relevant_only(self):
        p = self.c["school_pass_lead"]
        self.assertEqual("EDUCATION_RELEVANT", p["tier"])
        self.assertFalse(p["stable_pncp_purchase_id_recovered"])
        self.assertFalse(p["eiti_proven"])
        self.assertFalse(p["financial_identity_proven"])
        self.assertFalse(p["transaction_identity_proven"])

    def test_no_downstream_identity_promotions(self):
        s = self.e["epistemic_closure"]
        self.assertFalse(s["contract_linkage_created"])
        self.assertFalse(s["supplier_linkage_created"])
        self.assertFalse(s["financial_identity_created"])
        self.assertFalse(s["transaction_identity_created"])
        self.assertFalse(s["eiti_promotion_created"])


if __name__ == "__main__":
    unittest.main()
