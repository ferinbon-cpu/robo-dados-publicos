from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.research.task256_task255_timeout_curl_diagnostic import (
    Task256Stop,
    build_curl_command,
    execute_diagnostic,
    load_config,
    load_evidence,
    validate_live_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config/task256_task255_timeout_curl_diagnostic.v1.json"
EV = ROOT / "docs/evidence/TASK_256_TASK255_TIMEOUT_CANONICAL_0.8.0.json"
IMPL = "72c22246edcde103c8b51dd8a959f700606315c1"


class FakeTransport:
    def __init__(self, meta):
        self.meta = meta
        self.calls = 0

    def get(self, url, *, connect_timeout, max_time):
        self.calls += 1
        return dict(self.meta)


def auth(cfg, impl=IMPL):
    return {
        "task": "TASK_256_LIVE_AUTHORIZATION",
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "implementation_branch": "main",
        "runtime_branch": cfg["runtime"]["branch"],
        "implementation_sha": impl,
        "operation": "EXACT_1_TASK255_FIRST_TARGET_CURL_NOFOLLOW_TRANSPORT_DIAGNOSTIC",
        "control": cfg["diagnostic"]["control"],
        "requested_url": cfg["diagnostic"]["requested_url"],
        "max_remote_get_count": 1,
        "attempt_count": 1,
        "owner_authorized": True,
        "source_network_authorized": True,
        "follow_redirects": False,
        "automatic_retry": False,
        "alternate_url_discovery": False,
        "response_body_persistence": False,
        "prior_authorization_reused": False,
        "drive_write_authorized": False,
        "publication_authorized": False,
        "serving_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
        "consumed": False,
    }


def base_meta(cfg, **overrides):
    meta = {
        "requested_url": cfg["diagnostic"]["requested_url"],
        "curl_exit_code": 0,
        "curl_error": None,
        "http_code": 200,
        "redirect_url": None,
        "url_effective": cfg["diagnostic"]["requested_url"],
        "remote_ip": "203.0.113.10",
        "remote_port": 443,
        "local_ip": "192.0.2.10",
        "local_port": 50000,
        "time_namelookup": 0.01,
        "time_connect": 0.02,
        "time_appconnect": 0.03,
        "time_starttransfer": 0.04,
        "time_total": 0.05,
        "content_type": "application/json",
        "size_download": 123,
        "remote_get_count": 1,
        "response_body_persisted": False,
    }
    meta.update(overrides)
    return meta


class Task256Test(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(CFG)
        self.ev = load_evidence(EV)

    def test_missing_auth_stops(self):
        self.assertEqual(
            validate_live_authorization(None, expected_implementation_sha=IMPL, config=self.cfg)["status"],
            "STOP_TASK256_LIVE_NOT_AUTHORIZED",
        )

    def test_exact_auth_passes(self):
        self.assertEqual(
            validate_live_authorization(auth(self.cfg), expected_implementation_sha=IMPL, config=self.cfg),
            {"status": "PASS_TASK256_LIVE_AUTHORIZATION"},
        )

    def test_curl_command_is_single_get_no_follow_no_retry_no_body(self):
        diag = self.cfg["diagnostic"]
        cmd = build_curl_command(
            diag["requested_url"],
            connect_timeout=diag["connect_timeout_seconds"],
            max_time=diag["max_time_seconds"],
        )
        self.assertIn("--request", cmd)
        self.assertEqual(cmd[cmd.index("--request") + 1], "GET")
        self.assertNotIn("--location", cmd)
        self.assertEqual(cmd[cmd.index("--retry") + 1], "0")
        self.assertEqual(cmd[cmd.index("--output") + 1], "/dev/null")
        self.assertEqual(cmd.count(diag["requested_url"]), 1)

    def test_timeout_is_observation_not_absence(self):
        meta = base_meta(
            self.cfg,
            curl_exit_code=28,
            curl_error="curl: (28) Operation timed out",
            http_code=0,
            redirect_url=None,
            remote_ip=None,
            remote_port=None,
            time_starttransfer=0.0,
            time_total=75.0,
            content_type=None,
            size_download=0,
        )
        result = execute_diagnostic(
            self.cfg,
            self.ev,
            transport=FakeTransport(meta),
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["outcome"], "CURL_TIMEOUT_WITH_TRANSPORT_TIMINGS")
        self.assertFalse(result["absence_inference_allowed"])
        self.assertFalse(result["remaining_seven_targets_queried"])

    def test_redirect_location_is_captured_without_following(self):
        meta = base_meta(
            self.cfg,
            http_code=302,
            redirect_url="https://pncp.gov.br/other",
            content_type="text/html",
            size_download=0,
        )
        result = execute_diagnostic(
            self.cfg,
            self.ev,
            transport=FakeTransport(meta),
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["outcome"], "REDIRECT_LOCATION_CAPTURED")
        self.assertFalse(result["redirect_followed"])
        self.assertFalse(result["remaining_target_url_inference_allowed"])

    def test_effective_url_drift_stops(self):
        meta = base_meta(self.cfg, url_effective="https://example.invalid/drift")
        with self.assertRaisesRegex(Task256Stop, "TASK256_EFFECTIVE_URL_DRIFT"):
            execute_diagnostic(
                self.cfg,
                self.ev,
                transport=FakeTransport(meta),
                authorization=None,
                expected_implementation_sha=IMPL,
                offline_test_mode=True,
            )


if __name__ == "__main__":
    unittest.main()
