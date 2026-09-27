from __future__ import annotations

import copy
import hashlib
import io
import unittest

from pypdf import PdfWriter

from robo_dados_publicos.research.task252_jom_7321_7324_general_event_redigest import (
    Task252Stop,
    _validate_download,
    execute_general_redigest,
    load_canonical_evidence,
    load_config,
    validate_canonical_evidence,
    validate_config,
    validate_live_authorization,
)


def _valid_auth(config: dict, sha: str = "a" * 40) -> dict:
    return {
        "task": "TASK_252_LIVE_AUTHORIZATION",
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "implementation_branch": "main",
        "runtime_branch": config["runtime"]["branch"],
        "implementation_sha": sha,
        "source": "LIMEIRA_JORNAL_OFICIAL",
        "operation": "EXACT_4_HASH_PINNED_JOM_7321_7324_GENERAL_EVENT_REDIGEST",
        "editions": [7321, 7322, 7323, 7324],
        "expected_aggregate_bytes": 230331629,
        "max_index_remote_get_count": 0,
        "max_document_get_attempt_count": 4,
        "max_total_remote_get_count": 4,
        "max_bytes_per_document": 262144000,
        "max_aggregate_document_bytes": 230331629,
        "attempt_count": 1,
        "owner_authorized": True,
        "document_downloads_authorized": True,
        "rediscovery_authorized": False,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
        "task249_authorization_reused": False,
        "task250_authorization_reused": False,
        "task251_authorization_reused": False,
        "drive_write_authorized": False,
        "bronze_authorized": False,
        "silver_authorized": False,
        "gold_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
        "consumed": False,
    }


class _FakeSource:
    network_capable = False

    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, maximum_bytes: int):
        self.calls.append(url)
        return b"synthetic", {"url": url, "max": maximum_bytes}


def _bypass_validator(item, data, meta, *, maximum_bytes):
    return {
        "edition": item["edition"],
        "bytes": item["bytes"],
        "pages": item["pages"],
        "sha256": item["sha256"],
        "content_type": "application/pdf",
        "document_url": item["document_url"],
        "source_id": item["source_id"],
        "logical_key": item["logical_key"],
        "publication_date": item["publication_date"],
    }


def _fake_processor(item, data):
    edition = int(item["edition"])
    event_id = f"E{edition}"
    return {
        "status": "PASS_DOCUMENT",
        "summary": {
            "processing_status": "PASS_DOCUMENT_PROCESSING",
            "source_sha256": None,
            "text_extraction": "synthetic",
            "silver_pages": item["pages"],
            "gold_events": 1,
        },
        "events": [{"event_id": event_id, "edition": edition, "page_number": 1}],
        "semantics": [{"semantic_id": f"S{edition}", "event_id": event_id}],
        "strong_anchors": [],
    }


class Task252Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config()
        self.evidence = load_canonical_evidence()

    def test_canonical_evidence_and_config_pass(self):
        self.assertEqual(validate_canonical_evidence(self.evidence)["status"], "PASS_TASK252_CANONICAL_EVIDENCE")
        self.assertEqual(validate_config(self.config, self.evidence), {"status": "PASS_TASK252_CONFIG", "targets": 4})

    def test_evidence_result_hash_mutation_fails_closed(self):
        broken = copy.deepcopy(self.evidence)
        broken["task251_sanitized_result"]["aggregate_pdf_bytes"] += 1
        with self.assertRaisesRegex(Task252Stop, "EVIDENCE_RESULT_HASH_RECOMPUTE"):
            validate_canonical_evidence(broken)

    def test_binary_scope_mutation_fails_closed(self):
        broken = copy.deepcopy(self.evidence)
        broken["binary_scope"]["documents"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(Task252Stop, "EVIDENCE_DOCUMENT_7321"):
            validate_canonical_evidence(broken)

    def test_config_target_must_equal_canonical_scope(self):
        broken = copy.deepcopy(self.config)
        broken["targets"][0]["pages"] = 12
        with self.assertRaisesRegex(Task252Stop, "CONFIG_TARGETS_NE_CANONICAL_SCOPE"):
            validate_config(broken, self.evidence)

    def test_live_authorization_is_exact_and_non_reusable(self):
        sha = "a" * 40
        valid = _valid_auth(self.config, sha)
        self.assertEqual(
            validate_live_authorization(valid, expected_implementation_sha=sha, config=self.config)["status"],
            "PASS_TASK252_LIVE_AUTHORIZATION",
        )
        reused = dict(valid)
        reused["task251_authorization_reused"] = True
        self.assertEqual(
            validate_live_authorization(reused, expected_implementation_sha=sha, config=self.config)["status"],
            "STOP_TASK252_PRIOR_AUTHORIZATION_REUSE",
        )
        self.assertEqual(
            validate_live_authorization(None, expected_implementation_sha=sha, config=self.config)["status"],
            "STOP_TASK252_LIVE_NOT_AUTHORIZED",
        )

    def test_download_validator_checks_exact_hash_bytes_pages_and_url(self):
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        buffer = io.BytesIO()
        writer.write(buffer)
        data = buffer.getvalue()
        digest = hashlib.sha256(data).hexdigest()
        url = "https://ecrie.com.br/test.pdf"
        item = {
            "edition": 9999,
            "bytes": len(data),
            "pages": 1,
            "sha256": digest,
            "document_url": url,
            "source_id": "LIMEIRA_JO_09999",
            "logical_key": "limeira/jornal_oficial/edicao/9999",
            "publication_date": "2026-09-17",
        }
        meta = {
            "http_status": 200,
            "requested_url": url,
            "final_url": url,
            "https": True,
            "final_host": "ecrie.com.br",
            "content_type": "application/pdf",
            "remote_get_count": 1,
            "sha256": digest,
        }
        out = _validate_download(item, data, meta, maximum_bytes=262144000)
        self.assertEqual(out["pages"], 1)
        self.assertEqual(out["sha256"], digest)

        wrong = dict(meta)
        wrong["final_url"] = "https://ecrie.com.br/other.pdf"
        with self.assertRaisesRegex(Task252Stop, "DOWNLOAD_REDIRECT_OR_URL_DRIFT_9999"):
            _validate_download(item, data, wrong, maximum_bytes=262144000)

        bad_item = dict(item)
        bad_item["sha256"] = "0" * 64
        with self.assertRaisesRegex(Task252Stop, "DOWNLOAD_EXPECTED_SHA256_9999"):
            _validate_download(bad_item, data, meta, maximum_bytes=262144000)

    def test_offline_execute_exercises_four_document_control_flow_without_network(self):
        source = _FakeSource()
        result = execute_general_redigest(
            self.config,
            self.evidence,
            document_source=source,
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="a" * 40,
            offline_test_mode=True,
            document_processor=_fake_processor,
            download_validator=_bypass_validator,
        )
        self.assertEqual(result["status"], "PASS_COMPLETE_4_DOCUMENT_GENERAL_EVENT_REDIGEST")
        self.assertEqual(result["source_gets"], 4)
        self.assertEqual(result["aggregate_document_bytes"], 230331629)
        self.assertEqual(result["counts"]["event_count"], 4)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["raw_pdf_persisted"])
        self.assertFalse(result["absence_inference_allowed"])
        self.assertEqual(len(source.calls), 4)

    def test_offline_execute_stops_before_any_real_network(self):
        source = _FakeSource()
        source.network_capable = True
        result = execute_general_redigest(
            self.config,
            self.evidence,
            document_source=source,
            authorization={"synthetic_test_only": True},
            expected_implementation_sha="a" * 40,
            offline_test_mode=True,
            document_processor=_fake_processor,
            download_validator=_bypass_validator,
        )
        self.assertEqual(result["status"], "STOP_TASK252_OFFLINE_SOURCE_NETWORK_CAPABLE")
        self.assertEqual(source.calls, [])


if __name__ == "__main__":
    unittest.main()
