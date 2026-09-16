from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.research.task247_jom_rolling_discovery import (
    build_delta,
    execute,
    load_config,
    validate_live_authorization,
    validate_offline_carrier,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task247_jom_rolling_discovery.v1.json"


def row(edition: int, publication_date: str) -> dict:
    return {
        "edition": edition,
        "publication_date": publication_date,
        "document_url": f"https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_{edition}.pdf",
        "source_id": f"LIMEIRA_JO_{edition:05d}",
        "logical_key": f"limeira/jornal_oficial/edicao/{edition}",
    }


BASELINE = [
    row(7316, "2026-09-01"),
    row(7317, "2026-09-02"),
    row(7318, "2026-09-03"),
    row(7319, "2026-09-04"),
    row(7320, "2026-09-08"),
]


def report(extra: list[dict] | None = None, *, status: str = "PASS_DISCOVERY", pages: int = 1) -> dict:
    editions = BASELINE + list(extra or [])
    return {
        "status": status,
        "year": 2026,
        "month": 9,
        "pages_fetched": pages,
        "reported_total_items": len(editions),
        "count": len(editions),
        "editions": editions,
    }


class FakeSource:
    network_capable = False

    def __init__(self, payload: dict):
        self.payload = payload

    def discover_month(self, year: int, month: int, *, max_pages: int) -> dict:
        return copy.deepcopy(self.payload)


class TestTask247RollingDiscovery(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(CONFIG)

    def test_offline_contract_is_bounded_and_non_recurring(self):
        result = validate_offline_carrier(CONFIG)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["baseline_total"], 99)
        self.assertEqual(result["delta_start"], "2026-09-09")
        self.assertEqual(result["delta_end"], "2026-09-16")
        self.assertEqual(result["max_remote_get_count"], 10)
        self.assertFalse(result["recurrence"])
        self.assertFalse(result["schedule"])
        self.assertEqual(result["document_downloads"], 0)

    def test_builds_exact_delta_after_canonical_baseline(self):
        result = build_delta(
            report([row(7321, "2026-09-09"), row(7322, "2026-09-10")]),
            self.cfg,
        )
        self.assertEqual(result["baseline_ids"], [7316, 7317, 7318, 7319, 7320])
        self.assertEqual([x["edition"] for x in result["delta"]], [7321, 7322])

    def test_offline_executor_emits_sanitized_delta_only(self):
        result = execute(
            self.cfg,
            source=FakeSource(report([row(7321, "2026-09-09")])),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "PASS_JOM_ROLLING_DELTA_DISCOVERY")
        self.assertEqual(result["delta_count"], 1)
        self.assertEqual(result["delta_editions"][0]["edition"], 7321)
        self.assertEqual(result["document_download_count"], 0)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertEqual(result["serving_write_count"], 0)
        self.assertFalse(result["promotion_performed"])
        self.assertFalse(result["recurrence_performed"])
        self.assertFalse(result["schedule_performed"])
        self.assertFalse(result["absence_inference_allowed"])

    def test_zero_delta_is_not_future_absence(self):
        result = execute(
            self.cfg,
            source=FakeSource(report()),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "PASS_JOM_ROLLING_DELTA_DISCOVERY")
        self.assertEqual(result["delta_count"], 0)
        self.assertFalse(result["future_editions_inference_allowed"])

    def test_partial_month_stops(self):
        result = execute(
            self.cfg,
            source=FakeSource(report(status="PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED")),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "TASK247_DISCOVERY_NOT_COMPLETE")

    def test_missing_baseline_edition_stops(self):
        payload = report()
        payload["editions"] = payload["editions"][1:]
        payload["count"] = len(payload["editions"])
        result = execute(
            self.cfg,
            source=FakeSource(payload),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "TASK247_BASELINE_HISTORY_DRIFT")

    def test_backfilled_pre_delta_edition_stops(self):
        result = execute(
            self.cfg,
            source=FakeSource(report([row(7300, "2026-09-07")])),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "TASK247_BASELINE_HISTORY_DRIFT")

    def test_duplicate_edition_stops(self):
        payload = report([copy.deepcopy(BASELINE[-1])])
        result = execute(
            self.cfg,
            source=FakeSource(payload),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "TASK247_DUPLICATE_EDITION")

    def test_future_row_beyond_authorized_end_stops(self):
        result = execute(
            self.cfg,
            source=FakeSource(report([row(7330, "2026-09-17")])),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "TASK247_AFTER_AUTHORIZED_END")

    def test_non_https_or_wrong_host_stops(self):
        bad = row(7321, "2026-09-09")
        bad["document_url"] = "http://ecrie.com.br/file.pdf"
        result = execute(
            self.cfg,
            source=FakeSource(report([bad])),
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "TASK247_DOCUMENT_HTTPS")

    def test_live_authorization_is_exact_and_keeps_recurrence_false(self):
        sha = "a" * 40
        auth = {
            "task": "TASK_247_LIVE_AUTHORIZATION",
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "implementation_branch": "main",
            "runtime_branch": "task-247-jom-rolling-discovery-runtime",
            "implementation_sha": sha,
            "source": "LIMEIRA_JORNAL_OFICIAL",
            "operation": "BOUNDED_JOM_ROLLING_DELTA_DISCOVERY_READ_ONLY",
            "start_date": "2026-09-09",
            "end_date": "2026-09-16",
            "max_remote_get_count": 10,
            "attempt_count": 1,
            "owner_authorized": True,
            "document_downloads_authorized": False,
            "drive_write_authorized": False,
            "serving_authorized": False,
            "publication_authorized": False,
            "promotion_authorized": False,
            "recurrence_authorized": False,
            "schedule_authorized": False,
        }
        self.assertEqual(validate_live_authorization(auth, expected_implementation_sha=sha)["status"], "PASS_LIVE_AUTHORIZATION")
        mutated = dict(auth)
        mutated["recurrence_authorized"] = True
        self.assertEqual(validate_live_authorization(mutated, expected_implementation_sha=sha)["status"], "STOP_LIVE_AUTHORIZATION_CONTRACT_MISMATCH")

    def test_config_mutation_cannot_enable_schedule(self):
        raw = json.loads(CONFIG.read_text(encoding="utf-8"))
        raw["authorization"]["schedule_authorized"] = True
        temp = ROOT / "tests/.task247_bad_config.json"
        try:
            temp.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(Exception, "TASK247_AUTH_SCHEDULE_AUTHORIZED"):
                load_config(temp)
        finally:
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
