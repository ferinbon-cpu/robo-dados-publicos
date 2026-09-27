from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.manual_ingest.official_equivalence import (
    OfficialEquivalenceStop,
    build_probe_plan,
    classify_official_observations,
    evaluate_candidate_proof,
    load_official_equivalence_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/loa_official_equivalence_probe.v1.json"
FIXTURE = ROOT / "tests/fixtures/task_028_loa_official_equivalence_probe.json"


class TestTask028LoaOfficialEquivalenceProbe(unittest.TestCase):
    def setUp(self):
        self.contract = load_official_equivalence_contract(CONTRACT)
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_plan_is_offline_and_not_authorized(self):
        plan = build_probe_plan(self.contract)
        self.assertEqual(plan["status"], "PLANNED_NOT_AUTHORIZED")
        self.assertEqual(len(plan["requests"]), 3)
        self.assertFalse(plan["network_called"])
        self.assertEqual(plan["downloads"], 0)

    def test_pdf_only_does_not_prove_absence(self):
        result = classify_official_observations(
            self.contract, self.fixture["pdf_only_observations"]
        )
        self.assertEqual(
            result["status"],
            "NO_MACHINE_READABLE_EQUIVALENT_CANDIDATE_OBSERVED_BOUNDED_PROBE",
        )
        self.assertFalse(result["absence_proven"])
        self.assertFalse(result["equivalence_proven"])
        self.assertEqual(result["downloads"], 0)

    def test_machine_readable_link_is_candidate_not_equivalence(self):
        result = classify_official_observations(
            self.contract, self.fixture["machine_candidate_observations"]
        )
        self.assertEqual(result["status"], "MACHINE_READABLE_CANDIDATE_DETECTED_REVIEW_REQUIRED")
        self.assertEqual(len(result["machine_candidates"]), 1)
        self.assertFalse(result["machine_candidates"][0]["equivalence_proven"])
        self.assertFalse(result["followup_authorized"])

    def test_generic_execution_data_is_not_loa_equivalence(self):
        result = classify_official_observations(
            self.contract, self.fixture["generic_execution_observations"]
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(
            result["candidates"][0]["classification"],
            "EXECUTION_DATA_NOT_ENACTED_LOA_EQUIVALENCE",
        )

    def test_off_host_candidate_is_rejected(self):
        result = classify_official_observations(
            self.contract, self.fixture["off_host_observations"]
        )
        self.assertEqual(result["machine_candidates"], [])
        self.assertEqual(result["rejected"][0]["reason"], "HOST_NOT_ALLOWED")

    def test_off_host_observation_fails_closed(self):
        obs = deepcopy(self.fixture["pdf_only_observations"])
        obs[0]["url"] = "https://example.com/orcamentos"
        with self.assertRaisesRegex(OfficialEquivalenceStop, "STOP_LOA_OFFICIAL_EQUIVALENCE_OBSERVATION_HOST"):
            classify_official_observations(self.contract, obs)

    def test_request_budget_fails_closed(self):
        observations = self.fixture["pdf_only_observations"] * 7
        with self.assertRaisesRegex(OfficialEquivalenceStop, "STOP_LOA_OFFICIAL_EQUIVALENCE_REQUEST_BUDGET"):
            classify_official_observations(self.contract, observations)

    def test_incomplete_proofs_do_not_establish_equivalence(self):
        candidate = {"url": "https://www.limeira.sp.gov.br/documentos/loa-7223-2026.csv"}
        result = evaluate_candidate_proof(
            self.contract, candidate, self.fixture["proofs_incomplete"]
        )
        self.assertEqual(result["status"], "CANDIDATE_EQUIVALENCE_NOT_PROVEN")
        self.assertIn("ANNEX_COMPLETENESS_PROVEN", result["missing_proofs"])
        self.assertFalse(result["promotion_authorized"])

    def test_complete_synthetic_proofs_still_require_separate_authorization(self):
        candidate = {"url": "https://www.limeira.sp.gov.br/documentos/loa-7223-2026.csv"}
        result = evaluate_candidate_proof(
            self.contract, candidate, self.fixture["proofs_complete_synthetic"]
        )
        self.assertEqual(
            result["status"],
            "CANDIDATE_PROOF_COMPLETE_REQUIRES_SEPARATE_AUTHORIZATION",
        )
        self.assertFalse(result["promotion_authorized"])

    def test_contract_contains_no_embedded_authorization(self):
        self.assertTrue(all(value is False for value in self.contract["authorization"].values()))


if __name__ == "__main__":
    unittest.main()
