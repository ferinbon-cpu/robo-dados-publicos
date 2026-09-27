import unittest

from robo_dados_publicos.automation.deepseek_review import (
    DeepSeekReviewError,
    build_review_payload,
    ContextPack,
    load_policy,
    validate_review,
)


class TestDeepSeekReviewNullNormalization(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy()
        self.base = {
            "verdict": "PASS",
            "summary": "No blockers.",
            "blocking_findings": [],
            "non_blocking_findings": [],
            "security_findings": [],
            "governance_findings": [],
            "missing_tests": [],
            "suggested_changes": [],
        }

    def test_null_list_fields_normalize_to_empty_arrays_only(self):
        review = dict(self.base)
        review["blocking_findings"] = None
        review["missing_tests"] = None
        normalized = validate_review(review, self.policy)
        self.assertEqual([], normalized["blocking_findings"])
        self.assertEqual([], normalized["missing_tests"])

    def test_non_list_non_null_still_fails_closed(self):
        review = dict(self.base)
        review["blocking_findings"] = "none"
        with self.assertRaisesRegex(DeepSeekReviewError, "STOP_DEEPSEEK_INVALID_REVIEW_JSON"):
            validate_review(review, self.policy)

    def test_prompt_requires_arrays_and_forbids_null(self):
        payload = build_review_payload(
            ContextPack("ctx", "a" * 64, 3, False), policy=self.policy
        )
        system = payload["messages"][0]["content"]
        self.assertIn("JSON array", system)
        self.assertIn("never null", system)
        self.assertIn("Return one JSON object only", system)


if __name__ == "__main__":
    unittest.main()
