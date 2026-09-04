import unittest

from scripts.verify_task091_live_ephemeral_digest_evidence import run


class TestTask091LiveEphemeralDigestEvidence(unittest.TestCase):
    def test_full_offline_evidence_chain(self):
        result = run()
        self.assertEqual(
            "PASS_TASK091_LIVE_EPHEMERAL_DIGEST_EVIDENCE_OFFLINE",
            result["status"],
        )
        self.assertEqual(33873064071, result["run_id"])
        self.assertEqual(2, result["request_count"])
        self.assertEqual(1, result["drive_media_gets"])
        self.assertTrue(result["digest_passed_before_historical_comparison"])
        self.assertTrue(result["candidate_file_count_gate_passed"])
        self.assertTrue(result["historical_count_drift"])
        self.assertEqual("UNRESOLVED", result["root_cause_status"])
        self.assertFalse(result["retry_authorized"])
        self.assertFalse(result["future_execution_authorized"])
        self.assertFalse(result["live_workflow_present"])


if __name__ == "__main__":
    unittest.main()
