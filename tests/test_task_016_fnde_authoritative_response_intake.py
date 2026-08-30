import copy
import importlib.util
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

    def real_intake(self):
        data = copy.deepcopy(self.fixture("b1_complete.json"))
        data.update(source_class="OFFICIAL_RESPONSE_USER_MEDIATED", authority_provenance_status="AUTHORITATIVE_PROVEN", fixture_disclaimer=[])
        data["provenance_basis"] = "Human reviewer matched the externally held artifact to the official handoff."
        data["provenance_checks"] = {"handoff_mode":"USER_MEDIATED_OFFICIAL_RESPONSE","authority_label_observed":True,"protocol_observed":data["protocol"],"raw_artifact_hash_verified":True,"human_offline_review_completed":True}
        return data

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

    def test_response_received_requires_a_json_boolean(self):
        for invalid in ("false", "true", 0, 1, None, [], {}):
            with self.subTest(value=invalid):
                self.assertEqual(self.status_of_mutation(lambda d, value=invalid: d.update(response_received=value)), "STOP_INVALID_INTAKE_METADATA")
        self.assertEqual(self.status_of_mutation(lambda d: d.update(response_received=False, received_date=None)), "STOP_NO_RESPONSE")

    def test_received_date_requires_an_exact_real_iso_date(self):
        for invalid in ("2026-99-99", "2026/09/10", "banana", "", None):
            with self.subTest(value=invalid):
                self.assertEqual(self.status_of_mutation(lambda d, value=invalid: d.update(received_date=value)), "STOP_INVALID_INTAKE_METADATA")

    def test_authoritative_proven_requires_exact_structured_checks(self):
        data = self.real_intake()
        self.assertEqual(GATE.status_for(data, self.contract), "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW")
        for field, invalid in (("handoff_mode", "OTHER"),("authority_label_observed",False),("protocol_observed","23546.000000/2026-00"),("raw_artifact_hash_verified",False),("human_offline_review_completed",False)):
            changed = copy.deepcopy(data); changed["provenance_checks"][field] = invalid
            with self.subTest(field=field): self.assertEqual(GATE.status_for(changed, self.contract), "STOP_PROVENANCE_INCOMPLETE")

    def test_non_synthetic_disclaimer_must_be_empty_and_cannot_hide_private_text(self):
        for hidden in (["person@example.test"], ["access_token=synthetic-secret"]):
            data = self.real_intake(); data["fixture_disclaimer"] = hidden
            with self.subTest(hidden=hidden): self.assertEqual(GATE.status_for(data, self.contract), "STOP_UNSAFE_PUBLIC_EVIDENCE")

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
