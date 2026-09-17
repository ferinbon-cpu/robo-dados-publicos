from __future__ import annotations

import copy
import hashlib
import io
import unittest
from pathlib import Path

from pypdf import PdfWriter

from robo_dados_publicos.research.task251_jom_7323_7324_oversized_recovery import (
    Task251Stop,
    execute,
    load_canonical_evidence,
    load_config,
    validate_canonical_evidence,
    validate_config,
    validate_live_authorization,
    validate_offline_carrier,
)


def _pdf_bytes() -> bytes:
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)
    return buffer.getvalue()


class FakePdfSource:
    network_capable = False

    def __init__(self, *, mismatch: bool = False, fail_first: bool = False) -> None:
        self.calls: list[str] = []
        self.mismatch = mismatch
        self.fail_first = fail_first

    def fetch(self, *, url: str, destination: Path, max_bytes: int) -> dict:
        self.calls.append(url)
        if self.fail_first and len(self.calls) == 1:
            raise Task251Stop("SOURCE_STREAM_BYTE_CAP_EXCEEDED")
        payload = _pdf_bytes()
        if len(payload) > max_bytes:
            raise AssertionError("synthetic PDF unexpectedly exceeds cap")
        destination.write_bytes(payload)
        return {
            "http_status": 200,
            "requested_url": url,
            "final_url": url,
            "content_type": "application/pdf",
            "bytes": len(payload) + (1 if self.mismatch else 0),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "path": str(destination),
        }


class TestTask251(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config()
        self.evidence = load_canonical_evidence()

    def test_canonical_evidence_recomputes(self) -> None:
        result = validate_canonical_evidence(self.evidence)
        self.assertEqual(result["status"], "PASS_TASK251_CANONICAL_EVIDENCE")
        self.assertEqual(result["result_sha256"], "70e0de78992bc555cac65a6e5fec0096aa20d98364d06a4c30e1f59c0e560065")

    def test_evidence_mutation_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.evidence)
        mutated["sanitized_result"]["diagnostic"]["transport_bytes"] += 1
        with self.assertRaises(Task251Stop):
            validate_canonical_evidence(mutated)

    def test_config_exact_remainder_and_precedent_cap(self) -> None:
        result = validate_config(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_TASK251_CONFIG")
        self.assertEqual([x["edition"] for x in self.config["targets"]], [7323, 7324])
        self.assertEqual(self.config["limits"]["max_source_gets"], 2)
        self.assertEqual(self.config["limits"]["max_pdf_bytes_each"], 262144000)
        self.assertEqual(self.config["limits"]["max_aggregate_pdf_bytes"], 524288000)

    def test_config_cannot_redownload_proven_edition(self) -> None:
        mutated = copy.deepcopy(self.config)
        mutated["targets"][0]["edition"] = 7322
        with self.assertRaises(Task251Stop):
            validate_config(mutated, self.evidence)

    def test_config_cannot_expand_live_effects(self) -> None:
        mutated = copy.deepcopy(self.config)
        mutated["authorization"]["drive_write_authorized"] = True
        with self.assertRaises(Task251Stop):
            validate_config(mutated, self.evidence)

    def test_offline_carrier_is_inert(self) -> None:
        result = validate_offline_carrier()
        self.assertEqual(result["status"], "PASS_TASK251_OFFLINE_CARRIER")
        self.assertFalse(result["live_authorized"])
        self.assertFalse(result["network_performed"])
        self.assertFalse(result["drive_write"])
        self.assertFalse(result["schedule"])
        self.assertFalse(result["recurrence"])

    def test_offline_success_two_documents(self) -> None:
        source = FakePdfSource()
        result = execute(self.config, self.evidence, source=source, authorization={"synthetic_test_only": True}, expected_implementation_sha="0" * 40, offline_test_mode=True)
        self.assertEqual(result["status"], "PASS_TASK251_BOUNDED_OVERSIZED_RECOVERY")
        self.assertEqual(result["source_gets"], 2)
        self.assertEqual([x["edition"] for x in result["documents"]], [7323, 7324])
        self.assertEqual(len(source.calls), 2)
        self.assertFalse(result["raw_pdf_persisted"])
        self.assertEqual(result["drive_write_count"], 0)

    def test_stream_cap_stop_counts_attempt_and_does_not_request_7324(self) -> None:
        source = FakePdfSource(fail_first=True)
        result = execute(self.config, self.evidence, source=source, authorization={"synthetic_test_only": True}, expected_implementation_sha="0" * 40, offline_test_mode=True)
        self.assertEqual(result["status"], "STOP_TASK251_SOURCE_STREAM_BYTE_CAP_EXCEEDED")
        self.assertEqual(result["source_gets"], 1)
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(result["documents"], [])

    def test_transport_stat_mismatch_fails_closed(self) -> None:
        source = FakePdfSource(mismatch=True)
        result = execute(self.config, self.evidence, source=source, authorization={"synthetic_test_only": True}, expected_implementation_sha="0" * 40, offline_test_mode=True)
        self.assertEqual(result["status"], "STOP_TASK251_SOURCE_TRANSPORT_STAT_MISMATCH")
        self.assertEqual(result["source_gets"], 1)

    def test_offline_rejects_network_capable_source(self) -> None:
        source = FakePdfSource()
        source.network_capable = True
        result = execute(self.config, self.evidence, source=source, authorization={"synthetic_test_only": True}, expected_implementation_sha="0" * 40, offline_test_mode=True)
        self.assertEqual(result["status"], "STOP_TASK251_OFFLINE_NETWORK_CAPABLE_SOURCE")
        self.assertEqual(source.calls, [])

    def test_live_authorization_is_exact_and_not_reusable(self) -> None:
        sha = "a" * 40
        auth = {
            "task": "TASK_251_LIVE_AUTHORIZATION",
            "repository": "ferinbon-cpu/robo-dados-publicos",
            "branch": "main",
            "runtime_branch": "task-251-jom-7323-7324-oversized-recovery-runtime",
            "implementation_sha": sha,
            "source": "LIMEIRA_JORNAL_OFICIAL",
            "operation": "EXACT_2_JOM_7323_7324_OVERSIZED_PDF_GETS_SANITIZED_METADATA_ONLY",
            "editions": [7323, 7324],
            "max_source_gets": 2,
            "max_pdf_bytes_each": 262144000,
            "max_aggregate_pdf_bytes": 524288000,
            "attempt_count": 1,
            "automatic_retry": False,
            "redirects": False,
            "alternate_url_discovery": False,
            "drive_write": False,
            "bronze": False,
            "silver": False,
            "gold": False,
            "ocr": False,
            "semantic_parser": False,
            "serving": False,
            "publication": False,
            "promotion": False,
            "schedule": False,
            "recurrence": False,
            "task249_authorization_reused": False,
            "task250_authorization_reused": False,
            "owner_authorized": True,
            "consumed": False,
        }
        self.assertEqual(validate_live_authorization(auth, expected_sha=sha, config=self.config)["status"], "PASS_TASK251_LIVE_AUTHORIZATION")
        mutated = copy.deepcopy(auth)
        mutated["task250_authorization_reused"] = True
        self.assertNotEqual(validate_live_authorization(mutated, expected_sha=sha, config=self.config)["status"], "PASS_TASK251_LIVE_AUTHORIZATION")

    def test_workflow_has_no_schedule_or_manual_dispatch(self) -> None:
        text = Path(".github/workflows/task251_jom_7323_7324_oversized_recovery.yml").read_text(encoding="utf-8")
        self.assertIn("task-251-jom-7323-7324-oversized-recovery-runtime", text)
        self.assertIn("runtime_triggers/task251_jom_7323_7324_oversized_recovery.run", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertIn('test "${GITHUB_RUN_ATTEMPT}" = "1"', text)


if __name__ == "__main__":
    unittest.main()
