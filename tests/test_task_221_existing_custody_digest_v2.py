from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_V1 = ROOT / "config/existing_custody_corpus_registry.v1.json"
REGISTRY_V2 = ROOT / "config/existing_custody_corpus_registry.v2.json"
EVIDENCE = ROOT / "docs/evidence/TASK_221_EXISTING_CUSTODY_DIGEST_V2_0.8.0.json"


class TestTask221ExistingCustodyDigestV2(unittest.TestCase):
    def setUp(self) -> None:
        self.v1 = json.loads(REGISTRY_V1.read_text(encoding="utf-8"))
        self.v2 = json.loads(REGISTRY_V2.read_text(encoding="utf-8"))
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assets = {row["id"]: row for row in self.v2["assets"]}

    def test_registry_is_additive_and_pinned_to_current_base(self) -> None:
        self.assertEqual(self.v1["version"], 1)
        self.assertEqual(self.v2["version"], 2)
        self.assertEqual(self.v2["schema"], "EXISTING_CUSTODY_CORPUS_REGISTRY_V2")
        self.assertEqual(self.v2["issue"], 753)
        self.assertEqual(self.v2["base_main_sha"], "5e7bab5dae2bf7c8b64e087acb8165f67c95af62")
        self.assertEqual(self.v2["canonical_contextual_coverage"]["answerable"], 38)
        self.assertEqual(self.v2["canonical_contextual_coverage"]["total"], 38)
        self.assertFalse(self.v2["canonical_contextual_coverage"]["changed_by_this_task"])

    def test_md_01_3_handoff_gap_is_corrected_without_numeric_promotion(self) -> None:
        corpus = self.assets["MD_01_3_CORPUS"]
        self.assertEqual(corpus["custody"], "DISCOVERED_AND_READABLE_IN_USER_LIBRARY")
        self.assertEqual(corpus["robot_digest_status"], "INDEX_DISCOVERED_NOT_ROWLEVEL_INGESTED")
        self.assertEqual(corpus["inventory"]["source_files_found"], 228)
        self.assertEqual(corpus["inventory"]["unique_documents"], 194)
        self.assertEqual(corpus["inventory"]["duplicates_ignored"], 34)
        self.assertEqual(corpus["inventory"]["status_ok"], 191)
        self.assertEqual(corpus["inventory"]["status_sem_texto"], 3)
        self.assertEqual(corpus["inventory"]["document_id_range"], "DOC-001..DOC-194")
        self.assertEqual(sum(corpus["category_counts"].values()), 194)
        self.assertEqual(corpus["known_sem_texto_examples"], ["DOC-065", "DOC-100", "DOC-102"])
        self.assertIn("NO_HOLERITE_OR_PERSONNEL_ROWLEVEL_REPLICATION", corpus["privacy_boundary"])
        self.assertIn("DOES_NOT_AUTOMATICALLY_OVERRIDE", corpus["numeric_boundary"])

    def test_normative_v3_is_derived_coverage_map_not_legal_proof(self) -> None:
        brain = self.assets["CEREBRO_NORMATIVO_GESTAO_ESCOLAR_LIMEIRA_V3"]
        self.assertEqual(brain["supersedes_registry_reference"], "CEREBRO_NORMATIVO_GESTAO_ESCOLAR_LIMEIRA_V0_1")
        self.assertEqual(brain["role"], "DERIVED_RAG_GUIDE_AUDITABLE_SME_LEGAL_COVERAGE_MAP")
        self.assertEqual(
            brain["coverage_status_enum"],
            ["INTEGRADO_CORPUS", "PARCIAL", "PENDENTE_CORPUS_INTEGRAL", "LACUNA_CONFIRMADA"],
        )
        self.assertEqual(brain["confirmed_gap_example"], "RH_IS_04_VALE_ALIMENTACAO")
        self.assertIn("SYNTHESIS_NE_LEGAL_PROOF", brain["constraints"])
        self.assertIn("OFFICIAL_DOCUMENT_PRECEDENCE", brain["constraints"])
        self.assertIn("INTEGRADO_CORPUS_NE_CURRENT_VIGENCY_PROOF", brain["constraints"])
        self.assertIn("OCR_NE_NUMERIC_TRUTH", brain["constraints"])
        self.assertEqual(
            self.v2["precedence"]["normative"][0],
            "EXACT_OFFICIAL_NORMATIVE_DOCUMENT_WITH_CURRENT_VIGENCY_CHECK",
        )

    def test_closed_workbook_is_not_misrepresented_as_complete_runtime_import(self) -> None:
        v08 = self.assets["CAMADA_ANALITICA_V06_40_ESCOLAS_V08"]
        self.assertEqual(v08["robot_digest_status"], "PARTIALLY_MATERIALIZED")
        self.assertEqual(len(v08["not_fully_materialized_in_robot"]), 4)
        self.assertEqual(
            v08["transfer_guard"],
            "PARTIAL_SEARCH_SNIPPETS_MUST_NOT_RECONSTRUCT_COMPLETE_ROWSETS",
        )
        self.assertEqual(self.evidence["source_discovery"]["v08"]["robot_full_runtime_materialization"], False)

    def test_personnel_privacy_and_no_reingest_guards(self) -> None:
        self.assertIn("PERSONNEL_RAW_ROWS_NOT_INGESTED_BY_THIS_TASK", self.v2["guards"])
        self.assertIn("OCR_NE_NUMERIC_TRUTH", self.v2["guards"])
        self.assertIn("CORPUS_TRANSCRIPTION_NE_STRUCTURED_NUMERIC_SOURCE_BY_DEFAULT", self.v2["guards"])
        self.assertEqual(
            self.v2["already_processed_do_not_reingest_by_folder_name"],
            [
                "F01_PPA_LDO_LOA_2026",
                "F02_MDE_FUNDEB_2026_PILOT",
                "F02_LOCAL_MONITORING_2026_JAN_MAY",
            ],
        )
        self.assertIn("NO_PAYROLL_ROWLEVEL_REPLICATION", self.evidence["non_claims"])
        self.assertIn("NO_F01_F02_REINGEST", self.evidence["non_claims"])

    def test_next_digest_is_bounded_document_index_only(self) -> None:
        next_digest = self.evidence["next_bounded_digest"]
        self.assertEqual(next_digest["target"], "MD_01_3_DOCUMENT_INDEX_METADATA")
        self.assertFalse(next_digest["rowlevel_personnel_allowed"])
        self.assertFalse(next_digest["numeric_promotion_allowed"])
        self.assertEqual(self.v2["next_digest_queue"][0]["priority"], 1)
        self.assertEqual(self.v2["next_digest_queue"][0]["target"], "MD_01_3_DOCUMENT_INDEX_METADATA")
        self.assertTrue(all(value is False for value in self.v2["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
