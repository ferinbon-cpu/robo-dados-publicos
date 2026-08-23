import unittest

from robo_dados_publicos.qa.github_gate import evaluate_live_payload


class TestM4DGitHubGate(unittest.TestCase):
    def valid_payload(self):
        return {
            "status": "PASS",
            "software_version": "0.5.9",
            "release_status": "CANDIDATE",
            "state_source": "REMOTE_EXISTING",
            "state_remote": {"mode": "REPLACED", "id": "state-id"},
            "log_remote": {"id": "log-id", "name": "ROBO_RUN_20260823.json"},
        }

    def test_complete_live_evidence_passes(self):
        out = evaluate_live_payload(self.valid_payload())
        self.assertEqual("PASS_GITHUB_LIVE_GATE", out["status"])
        self.assertTrue(all(out["checks"].values()))

    def test_missing_remote_state_replacement_stops(self):
        payload = self.valid_payload()
        payload["state_remote"] = None
        out = evaluate_live_payload(payload)
        self.assertEqual("STOP_GITHUB_LIVE_GATE", out["status"])
        self.assertFalse(out["checks"]["state_remote_replaced"])

    def test_wrong_release_identity_stops(self):
        payload = self.valid_payload()
        payload["software_version"] = "0.5.8"
        out = evaluate_live_payload(payload)
        self.assertEqual("STOP_GITHUB_LIVE_GATE", out["status"])
        self.assertFalse(out["checks"]["candidate_version_0_5_9"])
