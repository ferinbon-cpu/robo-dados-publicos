from __future__ import annotations

import copy
import hashlib
import unittest
from pathlib import Path

from pypdf import PdfWriter

from robo_dados_publicos.research.task249_jom_bounded_pdf_acquisition import (
    PASS_STATUS,
    execute,
    load_config,
    load_queue,
)


ROOT = Path(__file__).resolve().parents[1]


class FakePdfSource:
    network_capable = False

    def __init__(self, *, redirect: bool = False, content_type: str = "application/pdf") -> None:
        self.redirect = redirect
        self.content_type = content_type
        self.calls: list[str] = []

    def fetch(self, *, url: str, destination: Path) -> dict[str, object]:
        self.calls.append(url)
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            writer.write(handle)
        data = destination.read_bytes()
        return {
            "http_status": 200,
            "requested_url": url,
            "final_url": url + "?redirected=1" if self.redirect else url,
            "content_type": self.content_type,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "path": str(destination),
        }


class NetworkMarkerSource(FakePdfSource):
    network_capable = True


class Task249Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "config/task249_jom_bounded_pdf_acquisition.v1.json")
        self.queue = load_queue(ROOT / "config/task248_jom_bounded_ingestion_queue.v1.json")
        self.synthetic_auth = {"synthetic_test_only": True}

    def test_offline_nominal_exact_four(self) -> None:
        source = FakePdfSource()
        result = execute(
            self.config,
            self.queue,
            source=source,
            authorization=self.synthetic_auth,
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], PASS_STATUS)
        self.assertEqual(result["source_gets"], 4)
        self.assertEqual([doc["edition"] for doc in result["documents"]], [7321, 7322, 7323, 7324])
        self.assertTrue(all(doc["pages"] == 1 for doc in result["documents"]))
        self.assertFalse(result["raw_pdf_persisted"])
        self.assertEqual(result["drive_write_count"], 0)

    def test_queue_mutation_fails_closed_before_get(self) -> None:
        queue = copy.deepcopy(self.queue)
        queue["items"][0]["edition"] = 9999
        source = FakePdfSource()
        result = execute(
            self.config,
            queue,
            source=source,
            authorization=self.synthetic_auth,
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertTrue(result["status"].startswith("STOP_TASK249_"))
        self.assertEqual(source.calls, [])

    def test_offline_network_source_is_blocked(self) -> None:
        result = execute(
            self.config,
            self.queue,
            source=NetworkMarkerSource(),
            authorization=self.synthetic_auth,
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "STOP_TASK249_OFFLINE_NETWORK_CAPABLE_SOURCE")

    def test_live_missing_authorization_stops_before_get(self) -> None:
        source = NetworkMarkerSource()
        result = execute(
            self.config,
            self.queue,
            source=source,
            authorization=None,
            expected_implementation_sha="1" * 40,
            offline_test_mode=False,
        )
        self.assertEqual(result["status"], "STOP_TASK249_LIVE_NOT_AUTHORIZED")
        self.assertEqual(source.calls, [])

    def test_redirect_drift_fails_closed_without_retry(self) -> None:
        source = FakePdfSource(redirect=True)
        result = execute(
            self.config,
            self.queue,
            source=source,
            authorization=self.synthetic_auth,
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "STOP_TASK249_SOURCE_URL_REDIRECT_OR_DRIFT")
        self.assertEqual(result["source_gets"], 1)
        self.assertFalse(result["retry_performed"])

    def test_unexpected_content_type_fails_closed(self) -> None:
        source = FakePdfSource(content_type="text/html")
        result = execute(
            self.config,
            self.queue,
            source=source,
            authorization=self.synthetic_auth,
            expected_implementation_sha="0" * 40,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "STOP_TASK249_SOURCE_CONTENT_TYPE_UNEXPECTED")
        self.assertEqual(result["source_gets"], 1)


if __name__ == "__main__":
    unittest.main()
