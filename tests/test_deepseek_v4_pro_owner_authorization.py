from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "docs/evidence/DEEPSEEK_V4_PRO_OWNER_AUTHORIZATION_0.8.0.json"


class DeepSeekV4ProOwnerAuthorizationTests(unittest.TestCase):
    def test_authorization_is_current_bounded_and_non_blanket(self):
        payload = json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "DEEPSEEK_V4_PRO_OWNER_AUTHORIZATION_V1")
        self.assertEqual(payload["bounded_interpretation"]["tokens_selected_by_orchestrator"], 12)
        self.assertEqual(payload["bounded_interpretation"]["deepseek_model_target"], "deepseek-v4-pro")
        self.assertEqual(payload["bounded_interpretation"]["model_promotion_gates"], [2, 3, 4])
        self.assertTrue(payload["evidence_semantics"]["prospective_current_owner_instruction"])
        self.assertTrue(payload["evidence_semantics"]["not_a_retroactive_signature"])
        self.assertTrue(payload["evidence_semantics"]["not_a_blanket_future_authorization"])

    def test_model_promotion_authorization_does_not_open_remote_effects(self):
        scope = json.loads(AUTH.read_text(encoding="utf-8"))["bounded_interpretation"]
        for key in (
            "direct_main_write", "self_merge", "drive_write_for_model_promotion",
            "serving_write", "publication", "site_mutation", "schedule", "recurrence",
        ):
            self.assertFalse(scope[key])


if __name__ == "__main__":
    unittest.main()
