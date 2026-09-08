from __future__ import annotations

import unittest

from robo_dados_publicos.research.task217c_jom_2026_discovery_runtime import (
    execute,
    load_config,
    validate_live_authorization,
    validate_offline_carrier,
)


def fake_month(month: int, *, status: str = "PASS_DISCOVERY"):
    day = "08" if month == 9 else "15"
    edition = 7500 + month
    return {
        "status": status,
        "year": 2026,
        "month": month,
        "pages_fetched": 1,
        "count": 1,
        "editions": [
            {
                "edition": edition,
                "publication_date": f"2026-{month:02d}-{day}",
                "document_url": f"https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/fake_{edition}.pdf",
                "source_id": f"LIMEIRA_JO_{edition:05d}",
                "logical_key": f"limeira/jornal_oficial/edicao/{edition}",
            }
        ],
    }


class FakeSource:
    network_capable = False

    def __init__(self, bad_month=None):
        self.bad_month = bad_month
        self.calls = []

    def discover_month(self, year, month, *, max_pages):
        self.calls.append((year, month, max_pages))
        if month == self.bad_month:
            return fake_month(month, status="PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED")
        return fake_month(month)


class TestTask217CJom2026DiscoveryRuntime(unittest.TestCase):
    def test_offline_carrier_has_zero_effects_and_no_documents(self):
        cfg = load_config()
        self.assertEqual(cfg["issue"], 680)
        self.assertEqual(cfg["discovery"]["max_remote_get_count"], 90)
        self.assertEqual(cfg["discovery"]["document_downloads"], 0)
        got = validate_offline_carrier()
        self.assertEqual(got["status"], "PASS")
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["promotion"])

    def test_fake_complete_discovery_proves_runtime_shape_without_network(self):
        cfg = load_config()
        source = FakeSource()
        got = execute(
            cfg,
            source=source,
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="a" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(got["status"], "PASS_COMPLETE_2026_JOM_DISCOVERY_READY_FOR_REDIGEST")
        self.assertTrue(got["complete_scope"])
        self.assertEqual(got["document_count"], 9)
        self.assertEqual(got["total_index_pages"], 9)
        self.assertEqual(got["estimated_remote_get_count"], 18)
        self.assertEqual(got["document_download_count"], 0)
        self.assertFalse(got["promotion_performed"])
        self.assertFalse(got["absence_inference_allowed"])
        self.assertEqual(source.calls[0], (2026, 1, 5))
        self.assertEqual(source.calls[-1], (2026, 9, 5))

    def test_partial_month_stops_and_never_claims_absence(self):
        cfg = load_config()
        got = execute(
            cfg,
            source=FakeSource(bad_month=4),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="a" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(got["status"], "STOP_MONTH_DISCOVERY_CONTRACT")
        self.assertEqual(got["failed_month"], 4)
        self.assertEqual(got["completed_months"], 3)
        self.assertFalse(got["absence_inference_allowed"])
        self.assertEqual(got["document_download_count"], 0)
        self.assertFalse(got["promotion_performed"])

    def test_live_authorization_is_exact_and_task018_is_rejected(self):
        self.assertEqual(
            validate_live_authorization(
                {"task": "TASK_018", "task018_authorization_reused": True},
                expected_implementation_sha="a" * 40,
            )["status"],
            "STOP_TASK018_AUTHORIZATION_REUSE",
        )
        cfg = load_config()
        sha = "b" * 40
        auth = {
            "task": cfg["authorization"]["required_task"],
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "implementation_branch": "main",
            "runtime_branch": cfg["runtime_branch"],
            "implementation_sha": sha,
            "source": cfg["scope"]["source"],
            "operation": cfg["authorization"]["required_operation"],
            "start_date": cfg["scope"]["start_date"],
            "end_date": cfg["scope"]["end_date"],
            "max_remote_get_count": 90,
            "attempt_count": 1,
            "owner_authorized": True,
            "task018_authorization_reused": False,
            "document_downloads_authorized": False,
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

    def test_network_capable_source_is_forbidden_in_offline_test_mode(self):
        class BadFake:
            network_capable = True
        got = execute(
            load_config(),
            source=BadFake(),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="a" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(got["status"], "STOP_OFFLINE_TEST_NETWORK_CAPABLE")


if __name__ == "__main__":
    unittest.main()
