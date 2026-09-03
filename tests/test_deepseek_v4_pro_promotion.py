from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT / "config/deepseek_auto_review_policy.v1.json"
AGENT = ROOT / "config/deepseek_agent_policy.v1.json"
WORKFLOW = ROOT / ".github/workflows/deepseek-pr-review-auto.yml"


class DeepSeekV4ProPromotionTests(unittest.TestCase):
    def test_pro_is_default_in_both_policies(self):
        for path in (AUTO, AGENT):
            policy = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(policy["api"]["default_model"], "deepseek-v4-pro")
            self.assertIn("deepseek-v4-pro", policy["api"]["allowed_models"])
            self.assertIn("deepseek-v4-flash", policy["api"]["allowed_models"])

    def test_automatic_workflow_explicitly_uses_pro(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('--model "deepseek-v4-pro"', workflow)
        self.assertNotIn('--model "deepseek-v4-flash"', workflow)

    def test_safety_boundary_is_unchanged(self):
        policy = json.loads(AUTO.read_text(encoding="utf-8"))
        self.assertEqual(policy["github_permissions"], {"contents": "read", "pull_requests": "read"})
        self.assertFalse(policy["trigger_contract"]["execute_pull_request_code"])
        self.assertFalse(policy["trigger_contract"]["pull_request_target"])
        self.assertFalse(policy["trigger_contract"]["schedule"])
        self.assertFalse(policy["trigger_contract"]["recurrence"])
        blocked = set(policy["blocked_capabilities"])
        for capability in (
            "direct_main_write", "branch_write", "github_code_write", "self_merge",
            "drive_read", "drive_write", "publication", "schedule", "recurrence",
        ):
            self.assertIn(capability, blocked)


if __name__ == "__main__":
    unittest.main()
