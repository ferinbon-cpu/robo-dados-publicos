from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.github_codex_engineer_policy_gate import (
    CodexEngineerPolicyError,
    POLICY,
    validate_policy,
)


class TestCodexEngineerPolicy(unittest.TestCase):
    def _policy(self) -> dict:
        return json.loads(POLICY.read_text(encoding="utf-8"))

    def _validate_mutation(self, mutate) -> None:
        policy = self._policy()
        mutate(policy)
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "policy.json"
            path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaises(CodexEngineerPolicyError):
                validate_policy(path)

    def test_canonical_policy_passes(self):
        out = validate_policy()
        self.assertEqual(out["status"], "PASS_CODEX_ENGINEER_POLICY")
        self.assertEqual(out["mode"], "PR_ENGINEER")
        self.assertEqual(out["backend"], "CODEX_CLOUD_CHATGPT_ACCOUNT")
        self.assertEqual(out["github_secrets_required"], 0)
        self.assertFalse(out["remote_data_credentials_exposed_to_agent"])
        self.assertFalse(out["drive_credentials_exposed_to_agent"])

    def test_direct_main_write_fails_closed(self):
        self._validate_mutation(lambda p: p.__setitem__("direct_main_write_allowed", True))

    def test_self_merge_fails_closed(self):
        self._validate_mutation(lambda p: p.__setitem__("self_merge_allowed", True))

    def test_api_key_requirement_fails_closed(self):
        self._validate_mutation(lambda p: p.__setitem__("openai_api_key_required", True))

    def test_drive_credentials_exposure_fails_closed(self):
        self._validate_mutation(lambda p: p.__setitem__("drive_credentials_exposed_to_agent", True))

    def test_secret_capability_cannot_be_removed(self):
        def mutate(policy):
            policy["blocked_capabilities"].remove("secret_read")
        self._validate_mutation(mutate)

    def test_t3_self_authorization_cannot_be_removed(self):
        def mutate(policy):
            policy["blocked_capabilities"].remove("self_authorize_t3")
        self._validate_mutation(mutate)

    def test_minimum_validation_commands_cannot_be_removed(self):
        def mutate(policy):
            policy["required_before_pr_ready"].remove("run_python_main.py_selftest")
        self._validate_mutation(mutate)

    def test_first_mission_exists(self):
        out = validate_policy()
        self.assertEqual(out["first_mission"], "docs/tasks/CODEX_TASK_001_SIOPE_REGIME_DISCOVERY.md")


if __name__ == "__main__":
    unittest.main()
