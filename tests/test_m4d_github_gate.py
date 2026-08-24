import unittest

from robo_dados_publicos.qa.github_gate import evaluate_live_payload


class TestM4DGitHubGate(unittest.TestCase):
    def valid_payload(self):
        return {
            "status": "PASS",
            "software_version": "0.6.0",
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
        payload["software_version"] = "0.5.9"
        out = evaluate_live_payload(payload)
        self.assertEqual("STOP_GITHUB_LIVE_GATE", out["status"])
        self.assertFalse(out["checks"]["software_version_match"])

    def test_active_identity_can_be_required_explicitly(self):
        payload = self.valid_payload()
        payload["release_status"] = "ACTIVE"
        out = evaluate_live_payload(payload, expected_version="0.6.0", expected_status="ACTIVE")
        self.assertEqual("PASS_GITHUB_LIVE_GATE", out["status"])

    def test_complete_source_collection_evidence_passes(self):
        payload = self.valid_payload()
        payload.update({
            "mode": "SOURCE_COLLECTION_ENABLED",
            "source_collection": {
                "status": "PASS",
                "inventory": {"enabled": 1},
                "results": [{
                    "source_id": "JOURNAL_GATE",
                    "status": "DOWNLOADED_NEW",
                    "remote_id": "bronze-id",
                    "sha256": "a" * 64,
                    "bytes": 123,
                    "content_type": "application/pdf",
                }],
            },
        })
        expectation = {
            "source_id": "JOURNAL_GATE",
            "expected_sha256": "a" * 64,
            "expected_bytes": 123,
            "expected_content_types": ("application/pdf",),
        }
        out = evaluate_live_payload(payload, source_expectation=expectation)
        self.assertEqual("PASS_GITHUB_SOURCE_COLLECTION_GATE", out["status"])
        self.assertTrue(all(out["checks"].values()))

    def test_source_hash_mismatch_stops_source_gate(self):
        payload = self.valid_payload()
        payload.update({
            "mode": "SOURCE_COLLECTION_ENABLED",
            "source_collection": {
                "status": "PASS",
                "inventory": {"enabled": 1},
                "results": [{
                    "source_id": "JOURNAL_GATE",
                    "status": "DOWNLOADED_NEW",
                    "remote_id": "bronze-id",
                    "sha256": "b" * 64,
                    "bytes": 123,
                    "content_type": "application/pdf",
                }],
            },
        })
        expectation = {
            "source_id": "JOURNAL_GATE",
            "expected_sha256": "a" * 64,
            "expected_bytes": 123,
            "expected_content_types": ("application/pdf",),
        }
        out = evaluate_live_payload(payload, source_expectation=expectation)
        self.assertEqual("STOP_GITHUB_SOURCE_COLLECTION_GATE", out["status"])
        self.assertFalse(out["checks"]["source_sha256_match"])
