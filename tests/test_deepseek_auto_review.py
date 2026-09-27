import unittest
from pathlib import Path

from robo_dados_publicos.automation.deepseek_review import DeepSeekReviewError
from scripts.deepseek_pr_review_auto import (
    build_comment,
    classify_review,
    comment_marker,
    load_auto_policy,
    sanitize_review,
    validate_same_repo_head,
)

ROOT = Path(__file__).resolve().parents[1]


def review_payload(*, verdict="PASS", blockers=None):
    return {
        "verdict": verdict,
        "summary": "Review summary.",
        "blocking_findings": list(blockers or []),
        "non_blocking_findings": [],
        "security_findings": [],
        "governance_findings": [],
        "missing_tests": [],
        "suggested_changes": [],
    }


class TestDeepSeekAutoReview(unittest.TestCase):
    def test_auto_policy_keeps_code_drive_and_publication_blocked(self):
        policy = load_auto_policy()
        trigger = policy["trigger_contract"]
        self.assertEqual("workflow_run", trigger["event"])
        self.assertTrue(trigger["same_repository_head_required"])
        self.assertTrue(trigger["checkout_default_branch_only"])
        self.assertFalse(trigger["execute_pull_request_code"])
        self.assertFalse(trigger["pull_request_target"])
        self.assertFalse(trigger["schedule"])
        self.assertEqual(
            {"contents": "read", "pull_requests": "read"},
            policy["github_permissions"],
        )
        gate = policy["review_gate_contract"]
        self.assertTrue(gate["model_verdict_alone_is_not_a_merge_gate"])
        self.assertEqual("NONEMPTY_BLOCKING_FINDINGS", gate["blocking_signal"])
        self.assertTrue(gate["full_sanitized_review_must_be_logged"])
        blocked = set(policy["blocked_capabilities"])
        self.assertTrue({"direct_main_write", "branch_write", "github_code_write", "self_merge"} <= blocked)
        self.assertTrue({"github_issue_write", "github_pull_request_comment_write"} <= blocked)
        self.assertTrue({"drive_read", "drive_write", "publication"} <= blocked)

    def test_workflow_uses_trusted_workflow_run_not_pr_secret_trigger(self):
        text = (ROOT / ".github/workflows/deepseek-pr-review-auto.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_run:", text)
        self.assertIn('"CI offline 0.8.0 candidate M7"', text)
        self.assertNotIn("pull_request_target:", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("pull_request:\n", text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
        self.assertIn("contents: read", text)
        self.assertIn("pull-requests: read", text)
        self.assertNotIn("issues: write", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("pull-requests: write", text)
        self.assertNotIn("secrets: inherit", text)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("uses:"):
                ref = stripped.rsplit("@", 1)[-1].split()[0]
                self.assertRegex(ref, r"^[0-9a-f]{40}$")

    def test_same_repo_and_exact_head_are_required(self):
        good = {"head": {"sha": "abc", "repo": {"full_name": "owner/repo"}}}
        validate_same_repo_head(good, repository="owner/repo", expected_head_sha="abc")

        fork = {"head": {"sha": "abc", "repo": {"full_name": "other/repo"}}}
        with self.assertRaisesRegex(DeepSeekReviewError, "FORK_OR_FOREIGN_HEAD_BLOCKED"):
            validate_same_repo_head(fork, repository="owner/repo", expected_head_sha="abc")

        moved = {"head": {"sha": "def", "repo": {"full_name": "owner/repo"}}}
        with self.assertRaisesRegex(DeepSeekReviewError, "HEAD_SHA_MISMATCH"):
            validate_same_repo_head(moved, repository="owner/repo", expected_head_sha="abc")

    def test_changes_requested_without_concrete_blocker_is_advisory(self):
        result = classify_review(review_payload(verdict="CHANGES_REQUESTED"))
        self.assertEqual("ADVISORY", result["deepseek_gate_decision"])
        self.assertEqual("REVIEW", result["effective_verdict"])
        self.assertEqual(0, result["blocking_findings_count"])

    def test_concrete_blocking_finding_is_the_only_deepseek_block_signal(self):
        result = classify_review(
            review_payload(
                verdict="CHANGES_REQUESTED",
                blockers=[{"severity": "BLOCKER", "detail": "Exact deterministic defect."}],
            )
        )
        self.assertEqual("BLOCK", result["deepseek_gate_decision"])
        self.assertEqual("CHANGES_REQUESTED", result["effective_verdict"])
        self.assertEqual(1, result["blocking_findings_count"])

    def test_blocking_finding_cannot_be_hidden_behind_pass_verdict(self):
        result = classify_review(
            review_payload(verdict="PASS", blockers=["Concrete blocker despite inconsistent verdict."])
        )
        self.assertEqual("BLOCK", result["deepseek_gate_decision"])
        self.assertEqual("CHANGES_REQUESTED", result["effective_verdict"])

    def test_review_output_is_redacted_before_log_or_summary_materialization(self):
        review = review_payload(verdict="REVIEW")
        review["summary"] = "SAMPLE_API_KEY=abcdefghijklmnop should never be logged"
        safe = sanitize_review(review)
        self.assertNotIn("abcdefghijklmnop", safe["summary"])
        self.assertIn("[REDACTED]", safe["summary"])

    def test_comment_is_bound_to_reviewed_head(self):
        body = build_comment(
            review_payload(),
            head_sha="a" * 40,
            model="deepseek-v4-flash",
            upstream_conclusion="success",
        )
        self.assertIn(comment_marker("a" * 40), body)
        self.assertIn("DeepSeek automatic review", body)
        self.assertIn("cannot write code, merge, access Drive, or publish data", body)


if __name__ == "__main__":
    unittest.main()
