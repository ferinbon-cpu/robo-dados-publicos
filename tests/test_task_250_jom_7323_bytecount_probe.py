from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from robo_dados_publicos.research.task250_jom_7323_bytecount_probe import (
    PASS_STATUS,
    execute,
    load_config,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeProbeSource:
    network_capable = False

    def __init__(self, payload: bytes, *, reported_bytes: int | None = None) -> None:
        self.payload = payload
        self.reported_bytes = len(payload) if reported_bytes is None else reported_bytes
        self.calls = 0

    def fetch(self, *, url: str, destination: Path) -> dict[str, object]:
        self.calls += 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.payload)
        return {
            "http_status": 200,
            "requested_url": url,
            "final_url": url,
            "content_type": "application/pdf",
            "transport_bytes": self.reported_bytes,
            "transport_sha256": hashlib.sha256(self.payload).hexdigest(),
            "path": str(destination),
        }


class Task250Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "config/task250_jom_7323_bytecount_probe.v1.json")
        self.auth = {"synthetic_test_only": True}

    def run_probe(self, source: FakeProbeSource, config=None):
        return execute(
            config or self.config,
            source=source,
            authorization=self.auth,
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )

    def test_valid_byte_count(self) -> None:
        result = self.run_probe(FakeProbeSource(b"%PDF-test"))
        self.assertEqual(result["status"], PASS_STATUS)
        self.assertEqual(result["source_gets"], 1)
        self.assertEqual(result["diagnostic"]["byte_count_outcome"], "BYTE_COUNT_VALID")
        self.assertEqual(result["diagnostic"]["transport_bytes"], 9)
        self.assertEqual(result["diagnostic"]["temporary_stat_bytes"], 9)
        self.assertFalse(result["raw_pdf_persisted"])
        self.assertEqual(result["drive_write_count"], 0)

    def test_empty_file_is_distinguished(self) -> None:
        result = self.run_probe(FakeProbeSource(b""))
        self.assertEqual(result["diagnostic"]["byte_count_outcome"], "EMPTY_FILE")

    def test_oversize_is_distinguished(self) -> None:
        config = dict(self.config)
        config["limits"] = dict(self.config["limits"])
        config["limits"]["max_pdf_bytes"] = 5
        result = self.run_probe(FakeProbeSource(b"123456"), config=config)
        self.assertEqual(result["diagnostic"]["byte_count_outcome"], "OVER_MAX_BYTES")
        self.assertEqual(result["diagnostic"]["configured_max_bytes"], 5)

    def test_transport_counter_mismatch_is_distinguished(self) -> None:
        result = self.run_probe(FakeProbeSource(b"123456", reported_bytes=5))
        self.assertEqual(result["diagnostic"]["byte_count_outcome"], "TRANSPORT_COUNTER_MISMATCH")
        self.assertEqual(result["diagnostic"]["transport_bytes"], 5)
        self.assertEqual(result["diagnostic"]["temporary_stat_bytes"], 6)

    def test_network_source_blocked_offline(self) -> None:
        source = FakeProbeSource(b"123")
        source.network_capable = True
        result = self.run_probe(source)
        self.assertEqual(result["status"], "STOP_TASK250_OFFLINE_NETWORK_CAPABLE_SOURCE")
        self.assertEqual(source.calls, 0)

    def test_live_without_exact_authorization_stops_before_get(self) -> None:
        source = FakeProbeSource(b"123")
        source.network_capable = True
        result = execute(
            self.config,
            source=source,
            authorization=None,
            expected_implementation_sha="1" * 40,
            offline_test_mode=False,
        )
        self.assertEqual(result["status"], "STOP_TASK250_LIVE_NOT_AUTHORIZED")
        self.assertEqual(source.calls, 0)


if __name__ == "__main__":
    unittest.main()
