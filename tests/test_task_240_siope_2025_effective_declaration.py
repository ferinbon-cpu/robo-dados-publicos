import copy
import json
import unittest

from scripts.github_task_240_siope_2025_effective_declaration_gate import (
    EVIDENCE,
    EXPECTED_B3,
    EXPECTED_DECISION,
    INTAKE,
    PRIOR,
    validate,
    validate_objects,
)


def load(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


class Task240EffectiveAnnualDeclarationTests(unittest.TestCase):
    def setUp(self):
        self.evidence = load(EVIDENCE)
        self.intake = load(INTAKE)
        self.prior = load(PRIOR)

    def test_gate_passes(self):
        self.assertEqual(validate(), EXPECTED_DECISION)

    def test_task016_intake_is_four_of_four_explicit(self):
        self.assertEqual(self.intake["overall_intake_status"], "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW")
        self.assertEqual(len(self.intake["proposition_assessments"]), 4)
        self.assertTrue(all(item["assessment"] == "PROVEN_EXPLICIT" for item in self.intake["proposition_assessments"]))
        self.assertFalse(self.intake["promotion_performed"])

    def test_b3_is_resolved_but_temporally_bounded(self):
        b3 = self.evidence["b3_decision"]
        app = self.evidence["deterministic_application"]
        self.assertEqual(b3["new_state"], EXPECTED_B3)
        self.assertTrue(b3["blocker_removed"])
        self.assertTrue(b3["future_state_can_change_after_successful_rectification"])
        self.assertEqual(app["temporal_boundary"], "PINNED_OBSERVATION_2026-08-30")
        self.assertEqual(app["immutable_finality"], "NOT_ASSERTED_AND_NOT_REQUIRED")
        self.assertEqual(app["future_successful_rectification_effect"], "SUPERSEDES_PRIOR_DECLARATION_AND_REQUIRES_REFRESH")

    def test_release_remains_fail_closed_after_b3(self):
        release = self.evidence["release_gate_effect"]
        self.assertEqual(release["B1_NUM_POPU"], "RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS")
        self.assertEqual(release["B2_FINANCIAL_ALIAS_BRIDGE"], "PROVEN_10_OF_10_ALIAS_TO_CONCEPT")
        self.assertEqual(release["B3_EFFECTIVE_ANNUAL_DECLARATION"], EXPECTED_B3)
        self.assertEqual(release["semantic_comparability_2016_2025"], "UNKNOWN_REQUIRES_SEPARATE_GATE")
        self.assertEqual(release["closed_annual_series"], "2016-2024")
        self.assertEqual(release["gold_2025"], "BLOCKED_NOT_CALCULATED")
        self.assertEqual(release["release_0_8_0"], "CANDIDATE")
        self.assertFalse(release["automatic_release_promotion"])

    def test_mutation_b3_promotion_fails_closed(self):
        mutated = copy.deepcopy(self.evidence)
        mutated["release_gate_effect"]["gold_2025"] = "CALCULATED"
        with self.assertRaises(ValueError):
            validate_objects(mutated, self.intake, self.prior, "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW")

    def test_mutation_immutable_finality_fails_closed(self):
        mutated = copy.deepcopy(self.evidence)
        mutated["deterministic_application"]["immutable_finality"] = "PROVEN_IMMUTABLE"
        with self.assertRaises(ValueError):
            validate_objects(mutated, self.intake, self.prior, "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW")

    def test_mutation_receipt_identity_fails_closed(self):
        mutated = copy.deepcopy(self.evidence)
        mutated["pinned_limeira_receipt_evidence"]["receipt_number"] = "999999-6"
        with self.assertRaises(ValueError):
            validate_objects(mutated, self.intake, self.prior, "INTAKE_COMPLETE_FOR_BLOCKER_DECISION_REVIEW")

    def test_incomplete_task016_intake_fails_closed(self):
        with self.assertRaises(ValueError):
            validate_objects(self.evidence, self.intake, self.prior, "INTAKE_RECEIVED_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
