from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.drive_ingestion_controller import (
    DriveIngestionStop,
    classify_metadata,
    load_controller_contract,
    route_inventory,
    summarize_routes,
)

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "config/drive_ingestion_controller.v1.json"
V2_PATH = ROOT / "config/drive_ingestion_controller.v2.json"
FIXTURE_PATH = ROOT / "tests/fixtures/task_059a_observatory_ingestion_catalog.json"
EVIDENCE_PATH = ROOT / "docs/evidence/TASK_059A_OBSERVATORY_INGESTION_CATALOG_0.8.0.json"


class Task059AObservatoryIngestionCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v1 = load_controller_contract(V1_PATH)
        cls.v2 = load_controller_contract(V2_PATH)
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    def test_v1_preserved_and_backward_compatible(self) -> None:
        self.assertEqual(self.v1["version"], 1)
        decision = classify_metadata(
            {"id": "legacy", "title": "FUNDEB_LIMEIRA_2026_01.pdf", "mime_type": "application/pdf"},
            self.v1,
        )
        self.assertEqual(decision.route, "AUTO_INGEST")
        self.assertEqual(decision.family, "FUNDEB")

    def test_v2_is_general_observatory_not_eiti_filter(self) -> None:
        self.assertEqual(self.v2["system_scope"], "GENERAL_MUNICIPAL_PUBLIC_DATA_OBSERVATORY")
        self.assertEqual(self.v2["eiti_role"], "ANALYTIC_USE_CASE_NOT_GLOBAL_INGESTION_FILTER")
        self.assertEqual(len(self.v2["known_document_families"]), 21)
        self.assertEqual(set(self.v2["family_match_order"]), set(self.v2["known_document_families"]))

    def test_all_observatory_fixtures_route_fail_closed(self) -> None:
        for item in self.fixtures:
            decision = classify_metadata(item, self.v2)
            self.assertEqual(decision.route, item["expected_route"], item["title"])
            self.assertEqual(decision.family, item["expected_family"], item["title"])

    def test_journal_is_auto_ingest_eligible_only(self) -> None:
        decision = classify_metadata(
            {"id": "j1", "title": "limeira_jornal_oficial_edicao_7314.pdf", "mime_type": "application/pdf"},
            self.v2,
        )
        self.assertEqual(decision.family, "JORNAL_OFICIAL")
        self.assertEqual(decision.route, "AUTO_INGEST")
        self.assertIn("EXECUTION_AUTH_REQUIRED", decision.reasons)
        self.assertFalse(self.v2["content_read_authorized"])
        self.assertFalse(self.v2["bronze_write_authorized"])

    def test_contracts_tce_tda_and_ppa_require_review(self) -> None:
        examples = [
            ("Contrato 51-2025.pdf", "application/pdf", "MUNICIPAL_CONTRACTS"),
            ("TCE_SP_DESPESAS_2026.zip", "application/zip", "TCE_SP_EXPENSES"),
            ("TDA_LIMEIRA_export.csv", "text/csv", "TDA_LIMEIRA"),
            ("PPA 2026-2029.pdf", "application/pdf", "PPA"),
        ]
        for title, mime, family in examples:
            decision = classify_metadata({"id": title, "title": title, "mime_type": mime}, self.v2)
            self.assertEqual(decision.family, family)
            self.assertEqual(decision.route, "REVIEW")
            self.assertIn("KNOWN_FAMILY_REQUIRES_SUPERVISED_REVIEW", decision.reasons)

    def test_multi_role_artifact_is_not_silently_collapsed(self) -> None:
        decision = classify_metadata(
            {"id": "multi", "title": "SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf", "mime_type": "application/pdf"},
            self.v2,
        )
        self.assertEqual(decision.route, "REVIEW")
        self.assertIsNone(decision.family)
        self.assertEqual(decision.reasons, ("MULTIPLE_FAMILY_MATCHES",))

    def test_known_archive_with_explicit_family_policy_is_review_not_quarantine(self) -> None:
        decision = classify_metadata(
            {"id": "zip", "title": "TCE_SP_DESPESAS_2026.zip", "mime_type": "application/zip"},
            self.v2,
        )
        self.assertEqual(decision.route, "REVIEW")
        self.assertEqual(decision.family, "TCE_SP_EXPENSES")

    def test_unknown_and_hydrated_inputs_quarantine(self) -> None:
        unknown = classify_metadata({"id": "u", "title": "imagem_sem_contexto.pdf", "mime_type": "application/pdf"}, self.v2)
        hydrated = classify_metadata({"id": "h", "title": "Jornal Oficial 7315.pdf", "mime_type": "application/pdf", "content_hydrated": True}, self.v2)
        self.assertEqual(unknown.route, "QUARANTINE")
        self.assertEqual(hydrated.route, "QUARANTINE")
        self.assertIn("CONTENT_HYDRATED_DURING_METADATA_PHASE", hydrated.reasons)

    def test_duplicate_auto_ingest_title_still_requires_hash_review(self) -> None:
        decisions = route_inventory(
            [
                {"id": "one", "title": "Jornal Oficial 7314.pdf", "mime_type": "application/pdf"},
                {"id": "two", "title": "Jornal_Oficial_7314.pdf", "mime_type": "application/pdf"},
            ],
            self.v2,
        )
        self.assertEqual(decisions[0].route, "AUTO_INGEST")
        self.assertEqual(decisions[1].route, "REVIEW")
        self.assertIn("POSSIBLE_DUPLICATE_WITHOUT_HASH", decisions[1].reasons)

    def test_summary_exercises_all_routes(self) -> None:
        summary = summarize_routes(route_inventory(self.fixtures, self.v2))
        self.assertEqual(sum(summary.values()), len(self.fixtures))
        self.assertGreater(summary["AUTO_INGEST"], 0)
        self.assertGreater(summary["REVIEW"], 0)
        self.assertGreater(summary["QUARANTINE"], 0)

    def test_contract_fails_closed_on_family_route_drift(self) -> None:
        raw = json.loads(V2_PATH.read_text(encoding="utf-8"))
        raw["family_default_routes"].pop("JORNAL_OFICIAL")
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.json"
            bad.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(DriveIngestionStop, "DEFAULT_ROUTE_FAMILY_DRIFT"):
                load_controller_contract(bad)

    def test_evidence_keeps_remote_effects_zero_and_f01_unchanged(self) -> None:
        self.assertEqual(self.evidence["base_sha"], "ab36f9c4324fda389178c97566f9a8bed485ee80")
        self.assertTrue(all(value == 0 for value in self.evidence["hard_boundaries"].values()))
        self.assertFalse(self.evidence["f01_eiti_state"]["changed_by_task_059a"])
        self.assertEqual(self.evidence["next_gate"]["task"], "TASK_060_DRIVE_INGESTION_CONTROLLER_METADATA_PILOT")
        self.assertEqual(self.evidence["result"], "PASS_TASK059A_OBSERVATORY_WIDE_INGESTION_CATALOG_OFFLINE_READY")


if __name__ == "__main__":
    unittest.main()
