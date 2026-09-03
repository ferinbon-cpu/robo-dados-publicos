from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "docs/evidence/DEEPSEEK_V4_PRO_OWNER_AUTHORIZATION_0.8.0.json"


class DeepSeekV4ProOwnerAuthorizationTests(unittest.TestCase):
    def test_authorization_resolves_unambiguously_to_only_non_flash_allowlisted_model(self):
        payload = json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "DEEPSEEK_V4_PRO_OWNER_AUTHORIZATION_V2")
        intent = payload["owner_intent_normalized"]
        self.assertEqual(intent["action"], "ENABLE_STRONGEST_ALREADY_ALLOWLISTED_NON_FLASH_DEEPSEEK_MODEL")
        self.assertEqual(intent["repository_allowed_models"], ["deepseek-v4-flash", "deepseek-v4-pro"])
        self.assertEqual(intent["non_flash_candidates"], ["deepseek-v4-pro"])
        self.assertEqual(intent["resolved_target"], "deepseek-v4-pro")
        self.assertTrue(payload["evidence_semantics"]["prospective_current_owner_instruction"])
        self.assertTrue(payload["evidence_semantics"]["normalized_intent_is_resolved_only_against_existing_repository_allowlist"])
        self.assertTrue(payload["evidence_semantics"]["not_a_retroactive_signature"])
        self.assertTrue(payload["evidence_semantics"]["not_a_blanket_future_authorization"])

    def test_model_promotion_authorization_does_not_open_remote_product_effects(self):
        blocked = set(json.loads(AUTH.read_text(encoding="utf-8"))["bounded_scope"]["effects_not_authorized"])
        for effect in (
            "DIRECT_MAIN_WRITE", "SELF_MERGE", "DRIVE_WRITE_FOR_MODEL_PROMOTION",
            "SERVING_WRITE", "PUBLICATION", "SITE_MUTATION", "SCHEDULE", "RECURRENCE",
            "SECRET_READBACK", "SECRET_EXPOSURE",
        ):
            self.assertIn(effect, blocked)

    def test_evidence_contains_no_common_secret_literal_patterns(self):
        text = AUTH.read_text(encoding="utf-8")
        for marker in ("sk-", "ghp_", "github_pat_", "AIza", "ya29."):
            self.assertNotIn(marker, text)
        self.assertTrue(json.loads(text)["owner_instruction_verbatim"].strip())


if __name__ == "__main__":
    unittest.main()
