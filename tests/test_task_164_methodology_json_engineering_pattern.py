from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.methodology_json_engineering_pattern import validate

P = ROOT / "config/methodology_json_engineering_pattern.v1.json"
R = ROOT / "config/methodology_domain_registry.v1.json"


class TestTask164MethodologyJsonPattern(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads(P.read_text(encoding="utf-8"))
        cls.r = json.loads(R.read_text(encoding="utf-8"))

    def test_validator(self):
        out = validate()
        self.assertEqual("VALID", out["status"])
        self.assertEqual("PUBLIC_BUDGET", out["first_reference_implementation"])

    def test_json_engineering_is_default_when_method_has_decision_semantics(self):
        triggers = set(self.p["default_decision_rule"]["use_json_engineering_when_any"])
        self.assertIn("domain_requires_allowed_or_forbidden_inferences", triggers)
        self.assertIn("domain_requires_question_to_source_routing", triggers)
        self.assertIn("domain_requires_repeatable_observation_normalization", triggers)

    def test_required_architecture(self):
        ids = {x["id"] for x in self.p["required_components"]}
        self.assertEqual(
            {
                "DOMAIN_METHODOLOGY",
                "OBSERVATION_CONTRACT",
                "QUESTION_SOURCE_ROUTER",
                "VALIDATOR",
                "TESTS",
                "SANITIZED_EVIDENCE",
            },
            ids,
        )

    def test_fail_closed_general_guards(self):
        forbidden = set(self.p["inference_contract"]["general_forbidden_promotions"])
        self.assertIn("THEMATIC_SIMILARITY_TO_IDENTITY", forbidden)
        self.assertIn("CHRONOLOGY_TO_IDENTITY", forbidden)
        self.assertIn("TRANSPORT_FAILURE_TO_SOURCE_NO_MATCH", forbidden)
        self.assertIn("MISSING_FIELD_TO_GUESSED_VALUE", forbidden)

    def test_public_budget_registered_as_first_conforming_domain(self):
        domains = {x["domain_id"]: x for x in self.r["domains"]}
        self.assertEqual("CONFORMING", domains["PUBLIC_BUDGET"]["status"])
        self.assertEqual(1, domains["PUBLIC_BUDGET"]["conformance_version"])


if __name__ == "__main__":
    unittest.main()
