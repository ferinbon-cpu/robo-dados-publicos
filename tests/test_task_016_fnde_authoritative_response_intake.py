import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/github_task_016_fnde_authoritative_response_intake_gate.py"
SPEC = importlib.util.spec_from_file_location("task016_gate", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)
FIXTURES = ROOT / "tests/fixtures/task_016_fnde_response_intake"

class Task016IntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = GATE.load(GATE.CONTRACT_PATH)
        cls.pending = GATE.load(GATE.PENDING_PATH)

    def fixture(self, name):
        return GATE.load(FIXTURES / name)

    def assert_fixture(self, name, status):
        self.assertEqual(GATE.validate(FIXTURES / name), status)

    def status_of_mutation(self, mutate):
        data = copy.deepcopy(self.fixture("b1_complete.json")); mutate(data)
        return GATE.status_for(data, self.contract)

    def test_contract_preserves_exact_request_mapping_and_order(self):
        expected = [
            ("B3_EFFECTIVE_DECLARATION", "23546.111502/2026-41", 4),
            ("B1_NUM_POPU", "23546.111503/2026-95", 4),
            ("B2_DOTACAO_EDU", "23546.111504/2026-30", 5),]
        self.assertEqual([(r["blocker_id"], r["protocol"], len(r["target_propositions"])) for r in self.contract["requests"]], expected)
        GATE.validate_pending(self.contract, self.pending)

    def test_task_011_stays_pending_and_canonical_state_is_frozen(self):
        self.assertTrue(all(r["response_status"] == "PENDING" for r in self.pending["requests"]))
        self.assertEqual(self.pending["decision"], "KEEP_B1_B2_B3_PENDING_NO_PROMOTION")
        state = self.contract["canonical_no_promotion_state"]
        self.assertEqual((state["release_0_8_0"], state["closed_annual_series"], state["gold_2025"]), ("CANDIDATE", "2016-2024", "UNKNOWN/BLOCKED"))
        self.assertFalse(state["future_batch_execution_authorized"])

    def test_complete_is_review_ready_without_promotion(self):
        self.assert_fixture("b1_complete.json", "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW")
        self.assertFalse(self.fixture("b1_complete.json")["promotion_performed"])

    def test_incomplete_ambiguous_and_contradictory_results(self):
        for name, status in (("b1_missing_vintage.json","INTAKE_RECEIVED_INCOMPLETE"),("b2_partial.json","INTAKE_RECEIVED_INCOMPLETE"),("b3_ambiguous.json","INTAKE_RECEIVED_AMBIGUOUS"),("contradictory.json","INTAKE_RECEIVED_CONTRADICTORY")):
            self.assert_fixture(name, status)

    def test_fail_closed_fixtures(self):
        cases = {"wrong_protocol.json":"STOP_PROTOCOL_MISMATCH","wrong_blocker.json":"STOP_BLOCKER_MISMATCH","wrong_proposition_order.json":"STOP_PROPOSITION_MAPPING_DRIFT","provenance_incomplete.json":"STOP_PROVENANCE_INCOMPLETE","unsafe_public_evidence.json":"STOP_UNSAFE_PUBLIC_EVIDENCE","no_response.json":"STOP_NO_RESPONSE"}
        for name, status in cases.items(): self.assert_fixture(name, status)

    def test_invalid_artifact_metadata_fails_closed(self):
        self.assertEqual(self.status_of_mutation(lambda d: d.update(raw_artifact_sha256="bad")), "STOP_INVALID_ARTIFACT_METADATA")
        self.assertEqual(self.status_of_mutation(lambda d: d.update(raw_artifact_bytes=0)), "STOP_INVALID_ARTIFACT_METADATA")
        self.assertEqual(self.status_of_mutation(lambda d: d.update(raw_artifact_mime="pdf")), "STOP_INVALID_ARTIFACT_METADATA")

    def test_raw_commit_and_promotion_are_rejected(self):
        self.assertEqual(self.status_of_mutation(lambda d: d.update(raw_artifact_committed=True)), "STOP_UNSAFE_PUBLIC_EVIDENCE")
        self.assertEqual(self.status_of_mutation(lambda d: d.update(promotion_performed=True)), "STOP_FORBIDDEN_PROMOTION")

    def test_gate_has_no_network_or_remote_mutation_capability(self):
        source = GATE_PATH.read_text(encoding="utf-8")
        for forbidden in ("requests", "urllib", "http.client", "socket", "subprocess", "drive_rest", "googleapiclient"):
            self.assertNotIn(f"import {forbidden}", source)
        self.assertNotIn("from requests", source)

if __name__ == "__main__":
    unittest.main()
