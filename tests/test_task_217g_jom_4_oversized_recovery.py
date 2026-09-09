from __future__ import annotations

import unittest

from robo_dados_publicos.research.task217g_jom_4_oversized_recovery import (
    load_config,
    validate_live_authorization,
    validate_offline_carrier,
)


class TestTask217GJom4OversizedRecovery(unittest.TestCase):
    def test_exact_four_targets_and_safe_budget(self):
        cfg = load_config()
        self.assertEqual([row["edition"] for row in cfg["targets"]], [7243,7253,7270,7287])
        self.assertEqual(cfg["network"]["max_total_remote_get_count"], 4)
        self.assertEqual(cfg["network"]["max_bytes_per_document"], 262144000)
        self.assertLessEqual(
            cfg["network"]["max_bytes_per_document"] * 4,
            cfg["network"]["max_aggregate_document_bytes"],
        )
        self.assertFalse(cfg["network"]["automatic_retry"])
        self.assertFalse(cfg["network"]["rediscovery_authorized"])

    def test_offline_carrier_is_inert(self):
        got = validate_offline_carrier()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["target_count"], 4)
        self.assertTrue(got["budget_math_safe"])
        self.assertFalse(got["live_authorized"])
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["promotion"])

    def test_consumed_authorizations_are_rejected(self):
        sha = "a" * 40
        self.assertEqual(
            validate_live_authorization({"task018_authorization_reused": True}, expected_implementation_sha=sha)["status"],
            "STOP_TASK018_AUTHORIZATION_REUSE",
        )
        self.assertEqual(
            validate_live_authorization({"task217d_authorization_reused": True}, expected_implementation_sha=sha)["status"],
            "STOP_TASK217D_AUTHORIZATION_REUSE",
        )
        self.assertEqual(
            validate_live_authorization({"task217f_authorization_reused": True}, expected_implementation_sha=sha)["status"],
            "STOP_TASK217F_AUTHORIZATION_REUSE",
        )

    def test_exact_live_authorization_shape(self):
        cfg = load_config()
        sha = "b" * 40
        auth = {
            "task": cfg["authorization"]["required_task"],
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "implementation_branch": "main",
            "runtime_branch": cfg["runtime"]["branch"],
            "implementation_sha": sha,
            "source": "LIMEIRA_JORNAL_OFICIAL",
            "operation": cfg["authorization"]["required_operation"],
            "task217f_embedded_result_sha256": cfg["source"]["task217f_embedded_result_sha256"],
            "max_document_get_attempt_count": 4,
            "max_total_remote_get_count": 4,
            "max_bytes_per_document": 262144000,
            "max_aggregate_document_bytes": 1073741824,
            "attempt_count": 1,
            "owner_authorized": True,
            "task018_authorization_reused": False,
            "task217d_authorization_reused": False,
            "task217f_authorization_reused": False,
            "document_downloads_authorized": True,
            "rediscovery_authorized": False,
            "drive_write_authorized": False,
            "serving_authorized": False,
            "publication_authorized": False,
            "promotion_authorized": False,
            "recurrence_authorized": False,
            "schedule_authorized": False,
        }
        self.assertEqual(
            validate_live_authorization(auth, expected_implementation_sha=sha)["status"],
            "PASS_LIVE_AUTHORIZATION",
        )


if __name__ == "__main__":
    unittest.main()
