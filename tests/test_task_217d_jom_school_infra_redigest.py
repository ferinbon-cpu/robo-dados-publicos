from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.research.task217d_jom_school_infra_redigest import (
    load_config,
    partition_id_for_edition,
    screen_derived_rows,
    select_new_documents,
    validate_live_authorization,
    validate_offline_carrier,
)


class TestTask217DJomSchoolInfraRedigest(unittest.TestCase):
    def test_contract_partitions_exactly_87_and_exclude_existing_august(self):
        cfg = load_config()
        editions = [e for rows in cfg["partitions"].values() for e in rows]
        self.assertEqual(len(editions), 87)
        self.assertEqual(len(set(editions)), 87)
        self.assertFalse(set(editions).intersection(range(7304, 7316)))
        self.assertEqual(partition_id_for_edition(7161), "2026-01")
        self.assertEqual(partition_id_for_edition(7294), "2026-07")
        self.assertEqual(partition_id_for_edition(7320), "2026-09")

    def test_offline_carrier_has_zero_remote_effects(self):
        got = validate_offline_carrier()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["new_document_count"], 87)
        self.assertEqual(got["partition_count"], 8)
        self.assertEqual(got["partition_document_count"], 87)
        self.assertFalse(got["live_authorized"])
        self.assertFalse(got["document_downloads_authorized_by_default"])
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["promotion"])

    def test_select_new_documents_requires_exact_partition_identity_set(self):
        cfg = load_config()
        all_editions = sorted(
            set(cfg["canonical_discovery"]["existing_editions"])
            | {e for rows in cfg["partitions"].values() for e in rows}
        )
        docs = [
            {
                "edition": e,
                "publication_date": "2026-01-01",
                "document_url": f"https://ecrie.com.br/{e}.pdf",
                "source_id": f"LIMEIRA_JO_{e:05d}",
                "logical_key": f"limeira/jornal_oficial/edicao/{e}",
            }
            for e in all_editions
        ]
        got = select_new_documents({"documents": docs})
        self.assertEqual(len(got), 87)
        self.assertFalse({row["edition"] for row in got}.intersection(range(7304, 7316)))

    def test_page_screening_and_structured_event_identity_are_separate(self):
        pages = [
            {
                "source_id": "LIMEIRA_JO_07161",
                "edition": 7161,
                "publication_date": "2026-01-17",
                "page_number": 10,
                "source_sha256": "a" * 64,
                "organ_hint": "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
                "text_redacted": "Aviso de reforma no CEIEF Rafael Affonso Leite.",
            },
            {
                "source_id": "LIMEIRA_JO_07161",
                "edition": 7161,
                "publication_date": "2026-01-17",
                "page_number": 11,
                "source_sha256": "a" * 64,
                "organ_hint": "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
                "text_redacted": "Aquisição de playground para unidades escolares da rede municipal.",
            },
        ]
        events = [
            {
                "event_id": "E1",
                "source_id": "LIMEIRA_JO_07161",
                "edition": 7161,
                "publication_date": "2026-01-17",
                "page_number": 10,
                "source_sha256": "a" * 64,
                "event_type": "CONTRATO",
                "object_text": "Reforma do CEIEF Rafael Affonso Leite",
                "excerpt_redacted": "Reforma do CEIEF Rafael Affonso Leite",
            },
            {
                "event_id": "E2",
                "source_id": "LIMEIRA_JO_07161",
                "edition": 7161,
                "publication_date": "2026-01-17",
                "page_number": 11,
                "source_sha256": "a" * 64,
                "event_type": "EDITAL",
                "object_text": "Aquisição de playground para unidades escolares da rede municipal",
                "excerpt_redacted": "Aquisição de playground para unidades escolares da rede municipal",
            },
        ]
        got = screen_derived_rows(pages, events)
        self.assertEqual(got["counts"]["page_candidate_count"], 2)
        self.assertEqual(got["counts"]["resolved_exact_school_infrastructure_count"], 1)
        exact = got["resolved_exact_school_infrastructure_events"][0]
        self.assertEqual(exact["resolved_school"]["school_code"], "35470600")
        self.assertEqual(exact["event_type"], "CONTRATO")
        self.assertIn("Rafael Affonso Leite", exact["evidence_excerpt_redacted"])
        self.assertFalse(exact["raw_object_text_persisted"])
        self.assertEqual(got["counts"]["generic_unassigned_school_infrastructure_count"], 1)
        generic = got["generic_unassigned_school_infrastructure_events"][0]
        self.assertEqual(generic["event_type"], "EDITAL")
        self.assertFalse(generic["raw_object_text_persisted"])
        self.assertTrue(all(row["page_screening_created_school_identity"] is False for row in got["page_candidates"]))

    def test_task018_authorization_is_rejected_and_exact_live_contract_is_required(self):
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
            "runtime_branch": cfg["runtime"]["branch"],
            "implementation_sha": sha,
            "source": "LIMEIRA_JORNAL_OFICIAL",
            "operation": cfg["authorization"]["required_operation"],
            "canonical_discovery_result_sha256": cfg["canonical_discovery"]["result_sha256"],
            "max_index_remote_get_count": 18,
            "max_document_download_count": 87,
            "max_total_remote_get_count": 105,
            "max_bytes_per_document": 52428800,
            "max_aggregate_document_bytes": 1073741824,
            "attempt_count": 1,
            "owner_authorized": True,
            "task018_authorization_reused": False,
            "document_downloads_authorized": True,
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
