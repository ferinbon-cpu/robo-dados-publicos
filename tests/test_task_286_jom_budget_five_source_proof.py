"""TASK286 T0 tests: fake PDF transport, no external network or mutation."""
from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from pypdf import PdfWriter

from robo_dados_publicos.research.task286_jom_budget_five_source_proof import (
    MAX_TOTAL, PILOT, REQUIRED_CONSENT, Task286Stop,
    execute_pilot, select_pinned_pilot,
)


def make_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    f = io.BytesIO()
    writer.write(f)
    return f.getvalue()


class FakeSource:
    network_capable = False

    def __init__(self, payload=None, host="ecrie.com.br", content_type="application/pdf"):
        self.pdf = make_pdf() if payload is None else payload
        self.host = host
        self.content_type = content_type
        self.urls = []

    def get(self, url, maximum_bytes):
        self.urls.append(url)
        return self.pdf, {
            "https": True,
            "final_host": self.host,
            "remote_get_count": 1,
            "content_type": self.content_type,
        }


class UnsafeNetworkSource(FakeSource):
    network_capable = True


class TestTask286Pilot(unittest.TestCase):
    def test_exact_pilot_order_and_source_integrity(self):
        docs = select_pinned_pilot()
        self.assertEqual([d["edition"] for d in docs], list(PILOT))
        self.assertEqual(len({d["document_url"] for d in docs}), 5)

    def test_offline_transport_extracts_only_pdf_integrity(self):
        src = FakeSource()
        r = execute_pilot(src, offline_test_mode=True)
        self.assertEqual(r["status"], "PASS_SOURCE_PDF_INTEGRITY_ONLY_NOT_ARCHIVED")
        self.assertEqual(r["source_get_count"], 5)
        self.assertEqual([d["edition"] for d in r["results"]], list(PILOT))
        self.assertEqual(r["pdf_persisted_count"], 0)
        self.assertEqual(r["drive_write_count"], 0)
        self.assertEqual(r["budget_lines_extracted"], 0)
        self.assertFalse(r["absence_inference_allowed"])
        self.assertEqual(len(src.urls), 5)

    def test_network_transport_is_blocked_in_offline_mode(self):
        with self.assertRaisesRegex(Task286Stop, "STOP_FAKE_SOURCE_REQUIRED"):
            execute_pilot(UnsafeNetworkSource(), offline_test_mode=True)

    def test_default_network_invocation_is_blocked(self):
        source = UnsafeNetworkSource()
        with self.assertRaisesRegex(Task286Stop, "STOP_UNAUTHORIZED_T1"):
            execute_pilot(source)
        self.assertEqual(source.urls, [])

    def test_incomplete_owner_authorization_is_blocked(self):
        src = UnsafeNetworkSource()
        auth = {
            "consent": REQUIRED_CONSENT, "owner_authorized": True,
            "implementation_sha": "a" * 40,
            "exact_editions": list(PILOT),
            "max_document_gets": 5,
            "max_aggregate_bytes": MAX_TOTAL,
            "no_retry": True,
            "drive_write_allowed": False,
            "pdf_artifact_persist_allowed": False,
            "publication_allowed": False,
        }
        r = execute_pilot(src, authorization=auth, implementation_sha="a" * 40)
        self.assertEqual(r["source_get_count"], 5)
        self.assertEqual(len(src.urls), 5)
        auth["exact_editions"] = [7211]
        with self.assertRaisesRegex(Task286Stop, "STOP_UNAUTHORIZED_T1"):
            execute_pilot(UnsafeNetworkSource(), authorization=auth, implementation_sha="a" * 40)

    def test_corrupt_pdf_fails_closed(self):
        with self.assertRaisesRegex(Task286Stop, "STOP_PDF_SIGNATURE"):
            execute_pilot(FakeSource(payload=b"not a pdf"), offline_test_mode=True)

    def test_pdf_malformed_fails_closed(self):
        with self.assertRaisesRegex(Task286Stop, "STOP_PDF_PARSE"):
            execute_pilot(FakeSource(payload=b"%PDF-BROKEN PDF bytes"), offline_test_mode=True)

    def test_source_identity_drift_fails_closed(self):
        with self.assertRaisesRegex(Task286Stop, "STOP_SOURCE_RESPONSE_IDENTITY"):
            execute_pilot(FakeSource(host="example.org"), offline_test_mode=True)

    def test_wrong_content_type_fails_closed(self):
        with self.assertRaisesRegex(Task286Stop, "STOP_SOURCE_RESPONSE_IDENTITY"):
            execute_pilot(FakeSource(content_type="text/html"), offline_test_mode=True)

    def test_no_oversized_payload(self):
        with patch("robo_dados_publicos.research.task286_jom_budget_five_source_proof.MAX_PER_PDF", 30):
            with self.assertRaisesRegex(Task286Stop, "STOP_PDF_BYTES_LIMIT"):
                execute_pilot(FakeSource(payload=make_pdf()), offline_test_mode=True)


if __name__ == "__main__":
    unittest.main()
