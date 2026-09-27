from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.research.task219a_jom_general_event_redigest import (
    extract_strong_anchors,
    load_config,
    load_pinned_targets,
    validate_live_authorization,
    validate_offline_carrier,
    write_sanitized_bundle,
)


class TestTask219AJomGeneralEventRedigest(unittest.TestCase):
    def test_contract_scope_and_budget_are_exact(self):
        cfg = load_config()
        self.assertEqual(cfg["canonical_discovery"]["document_count"], 99)
        self.assertEqual(cfg["canonical_discovery"]["new_document_count"], 87)
        self.assertEqual(cfg["canonical_discovery"]["existing_event_rows"], 303)
        self.assertEqual(len(cfg["canonical_discovery"]["existing_editions"]), 12)
        self.assertEqual(cfg["network"]["max_index_remote_get_count"], 0)
        self.assertEqual(cfg["network"]["max_document_get_attempt_count"], 87)
        self.assertEqual(cfg["network"]["max_total_remote_get_count"], 87)
        self.assertEqual(cfg["network"]["max_bytes_per_document"], 262144000)
        self.assertEqual(cfg["network"]["max_aggregate_document_bytes"], 4294967296)
        self.assertFalse(cfg["network"]["automatic_retry"])
        self.assertFalse(cfg["processing"]["emit_semantic_facets"])
        self.assertTrue(cfg["processing"]["derive_semantic_classification_after_event_parse"])
        self.assertFalse(cfg["processing"]["raw_pdf_persisted"])
        self.assertFalse(cfg["processing"]["raw_page_text_persisted"])
        self.assertFalse(cfg["processing"]["rag_chunks_persisted"])

    def test_pinned_targets_are_exact_87_and_match_task217d_scope(self):
        rows = load_pinned_targets()
        self.assertEqual(len(rows), 87)
        self.assertEqual(len({row["edition"] for row in rows}), 87)
        self.assertTrue(all(row["document_url"].startswith("https://ecrie.com.br/") for row in rows))
        self.assertFalse(any(7304 <= row["edition"] <= 7315 for row in rows))

    def test_prior_recovery_bytes_form_conservative_bound_below_new_cap(self):
        cfg = load_config()
        prior = cfg["prior_recovery_budget_evidence"]
        observed = (
            prior["task217d_aggregate_document_bytes"]
            + prior["task217f_aggregate_document_bytes"]
            + prior["task217g_aggregate_document_bytes"]
        )
        self.assertEqual(observed, 1865479856)
        self.assertEqual(observed, prior["overlap_inclusive_upper_bound_bytes"])
        self.assertLess(observed, cfg["network"]["max_aggregate_document_bytes"])

    def test_offline_carrier_is_inert(self):
        got = validate_offline_carrier()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["target_document_count"], 87)
        self.assertEqual(got["max_total_remote_get_count"], 87)
        self.assertTrue(got["prior_upper_bound_below_cap"])
        self.assertFalse(got["live_authorized"])
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["promotion"])

    def test_complete_process_and_contract_create_strong_anchors(self):
        event = {
            "event_id": "JOEV_SYNTHETIC_STRONG",
            "event_type": "CONTRATO",
            "edition": 9999,
            "publication_date": "2026-01-01",
            "page_number": 1,
            "source_sha256": "a" * 64,
            "process_number": "22.687/2024",
            "contract_number": "42/2026",
            "cnpj": "45.492.077/0001-64",
        }
        got = extract_strong_anchors([event])
        self.assertEqual(
            [(row["anchor_type"], row["anchor_value"]) for row in got],
            [
                ("CONTRACT_IDENTITY", "42/2026"),
                ("PROCESS_IDENTITY", "22.687/2024"),
            ],
        )
        self.assertTrue(all(row["supplier_cnpj"] == "45492077000164" for row in got))

    def test_cnpj_alone_and_incomplete_identifiers_never_anchor(self):
        events = [
            {
                "event_id": "JOEV_CNPJ_ONLY",
                "event_type": "CONTRATO",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 1,
                "source_sha256": "b" * 64,
                "process_number": None,
                "contract_number": "42/",
                "cnpj": "45.492.077/0001-64",
                "value_brl": "71000.00",
            },
            {
                "event_id": "JOEV_WRONG_TYPE",
                "event_type": "DECRETO",
                "edition": 9999,
                "publication_date": "2026-01-01",
                "page_number": 2,
                "source_sha256": "c" * 64,
                "process_number": "22.687/2024",
                "contract_number": "42/2026",
                "cnpj": "45.492.077/0001-64",
            },
        ]
        self.assertEqual(extract_strong_anchors(events), [])

    def test_consumed_authorizations_are_rejected(self):
        sha = "a" * 40
        self.assertEqual(
            validate_live_authorization(
                {"task217d_authorization_reused": True},
                expected_implementation_sha=sha,
            )["status"],
            "STOP_TASK217D_AUTHORIZATION_REUSE",
        )
        self.assertEqual(
            validate_live_authorization(
                {"task217f_authorization_reused": True},
                expected_implementation_sha=sha,
            )["status"],
            "STOP_TASK217F_AUTHORIZATION_REUSE",
        )
        self.assertEqual(
            validate_live_authorization(
                {"task217g_authorization_reused": True},
                expected_implementation_sha=sha,
            )["status"],
            "STOP_TASK217G_AUTHORIZATION_REUSE",
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
            "canonical_discovery_result_sha256": cfg["canonical_discovery"]["result_sha256"],
            "max_index_remote_get_count": 0,
            "max_document_get_attempt_count": 87,
            "pinned_target_fixture_git_blob_sha": cfg["canonical_discovery"]["pinned_target_fixture_git_blob_sha"],
            "max_total_remote_get_count": 87,
            "max_bytes_per_document": 262144000,
            "max_aggregate_document_bytes": 4294967296,
            "attempt_count": 1,
            "owner_authorized": True,
            "task217d_authorization_reused": False,
            "task217f_authorization_reused": False,
            "task217g_authorization_reused": False,
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

    def test_sanitized_bundle_contains_only_expected_files(self):
        result = {
            "schema": "TASK219A_GENERAL_EVENT_REDIGEST_RESULT_V1",
            "status": "PASS_COMPLETE_87_DOCUMENT_GENERAL_EVENT_REDIGEST",
            "complete_scope": True,
            "counts": {
                "failure_count": 0,
                "new_event_count": 1,
                "semantic_row_count": 1,
                "strong_anchor_count": 1,
            },
            "failures": [],
            "events": [
                {
                    "event_id": "JOEV_SYNTHETIC",
                    "edition": 9999,
                    "page_number": 1,
                    "excerpt_redacted": "texto sanitizado",
                }
            ],
            "semantics": [
                {
                    "semantic_id": "JOSEM_SYNTHETIC",
                    "event_id": "JOEV_SYNTHETIC",
                    "policy_domains": ["EDUCATION"],
                }
            ],
            "strong_anchors": [
                {
                    "event_id": "JOEV_SYNTHETIC",
                    "anchor_type": "PROCESS_IDENTITY",
                    "anchor_value": "22.687/2024",
                }
            ],
            "raw_pdf_persisted": False,
            "raw_page_text_persisted": False,
            "rag_chunks_persisted": False,
            "accounting_query_tasks_persisted": False,
        }
        with tempfile.TemporaryDirectory() as td:
            manifest = write_sanitized_bundle(result, td)
            names = sorted(p.name for p in Path(td).iterdir())
            self.assertEqual(
                names,
                [
                    "task219a_event_semantics_sanitized.jsonl",
                    "task219a_events_gold_sanitized.jsonl",
                    "task219a_manifest.json",
                    "task219a_strong_identity_anchors.jsonl",
                ],
            )
            self.assertEqual(manifest["files"]["events"]["row_count"], 1)
            self.assertEqual(manifest["files"]["semantics"]["row_count"], 1)
            self.assertEqual(manifest["files"]["strong_anchors"]["row_count"], 1)
            stored = json.loads(
                (Path(td) / "task219a_manifest.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("events", stored)
            self.assertNotIn("semantics", stored)
            self.assertNotIn("strong_anchors", stored)
            self.assertEqual(len(stored["bundle_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
