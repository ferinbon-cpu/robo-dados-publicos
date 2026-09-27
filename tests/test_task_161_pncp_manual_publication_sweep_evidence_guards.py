from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.task161_pncp_manual_publication_sweep_evidence_guards import validate

C = ROOT / "config/task161_pncp_manual_publication_sweep_evidence_guards.v1.json"
E = ROOT / "docs/evidence/TASK_161_PNCP_MANUAL_PUBLICATION_SWEEP_EVIDENCE_GUARDS_0.8.0.json"


class TestTask161(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(C.read_text(encoding="utf-8"))
        cls.e = json.loads(E.read_text(encoding="utf-8"))

    def test_validator(self):
        out = validate()
        self.assertEqual([6, 8, 12], out["complete_modalities"])
        self.assertFalse(out["explicit_eiti_match"])
        self.assertFalse(out["modality_9_exhaustive"])

    def test_fresh_authorization_is_pncp_only(self):
        a = self.c["authorization"]
        self.assertEqual("Autorizado pn p irrestrito", a["owner_instruction_exact"])
        self.assertEqual("PNCP_LIVE_READ_DISCOVERY_ONLY", a["scope"])
        self.assertFalse(a["mutations_allowed"])
        self.assertFalse(a["drive_writes_allowed"])
        self.assertFalse(a["non_pncp_live_sources_allowed"])

    def test_manual_api_scopes_are_exact_not_global(self):
        scopes = {x["modality_id"]: x for x in self.c["complete_scopes"]}
        self.assertEqual((181, 4), (scopes[6]["total_records"], scopes[6]["total_pages"]))
        self.assertEqual((434, 9), (scopes[8]["total_records"], scopes[8]["total_pages"]))
        self.assertEqual((5, 1), (scopes[12]["total_records"], scopes[12]["total_pages"]))
        self.assertTrue(all(x["exhaustive_within_exact_scope"] for x in scopes.values()))
        self.assertFalse(self.c["global_epistemic_state"]["global_pncp_no_match_created"])

    def test_education_relevant_is_not_eiti(self):
        self.assertTrue(self.c["promotion_rules"]["education_relevant_is_not_eiti_proven"])
        for item in self.c["selected_evidence_ledger"]:
            self.assertFalse(item["eiti_proven"])

    def test_wrong_municipality_is_rejected(self):
        guard = self.c["identity_guard"]
        self.assertEqual("Itupeva", guard["known_rejected_example"]["actual_municipality"])
        self.assertEqual("Limeira", guard["known_rejected_example"]["expected_municipality"])
        self.assertTrue(guard["known_rejected_example"]["must_not_enter_limeira_evidence_graph"])

    def test_index_and_transport_cannot_create_no_match(self):
        self.assertTrue(self.c["pagination_guard"]["indexed_search_cannot_create_exhaustive_no_match"])
        self.assertTrue(self.c["transport_guard"]["tool_layer_failure_is_not_source_no_match"])
        self.assertTrue(self.c["transport_guard"]["dns_failure_is_not_source_no_match"])
        self.assertFalse(self.e["epistemic_closure"]["transport_failure_is_no_match"])


if __name__ == "__main__":
    unittest.main()
