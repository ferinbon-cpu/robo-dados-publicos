import copy
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.analytics.existing_custody import (
    Task179Stop,
    domain_coverage,
    product_readiness,
    recommended_handoffs,
    summary,
    validate_contracts,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config/existing_custody_corpus_registry.v1.json"
CROSSWALK = ROOT / "config/existing_custody_product_ingestion_crosswalk.v1.json"
ONTOLOGY = ROOT / "config/observatory_question_ontology.v1.json"


class TestTask179ExistingCustodyCrosswalk(unittest.TestCase):
    def test_contracts_pass(self):
        got = validate_contracts()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["asset_count"], 8)
        self.assertEqual(got["product_count"], 6)
        self.assertEqual(got["domain_count"], 15)
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["serving"])

    def test_indicator_collection_is_synchronized_and_not_full_row_store(self):
        obj = json.loads(REGISTRY.read_text(encoding="utf-8"))
        assets = {row["id"]: row for row in obj["assets"]}
        collection = assets["INDICATORS_COLLECTION_2026_PUBLICATION"]
        self.assertEqual(collection["version"], "SYNCHRONIZED_I_V07_II_V06_III_V07")
        self.assertEqual(collection["coverage"]["school_universe_2025"], 69)
        self.assertEqual(collection["coverage"]["primary_years_schools"], 40)
        self.assertEqual(collection["coverage"]["early_childhood_only_or_other_profiles"], 29)
        self.assertIn("READY_FOR_PARTIAL_STRUCTURED_EXTRACTION", collection["readiness"])
        self.assertIn("NEEDS_BASE_STRUCTURED_FILE_HANDOFF", collection["readiness"])
        self.assertIn(
            "VOLUME_I_NARRATIVE_MUST_NOT_OVERWRITE_CANONICAL_STRUCTURED_ROWS",
            collection["constraints"],
        )

    def test_school_numeric_precedence_puts_base_mestra_before_publication(self):
        obj = json.loads(REGISTRY.read_text(encoding="utf-8"))
        order = obj["precedence"]["school_numeric"]
        self.assertEqual(order[0], "BASE_MESTRA_LIMEIRA_V05")
        self.assertEqual(order[1], "CAMADA_ANALITICA_V06_40_ESCOLAS_V08")
        self.assertIn("VOLUME_III_V07", order[2])
        self.assertIn("VOLUME_I_V07", order[-1])

    def test_school_product_is_partial_until_base_mestra_handoff(self):
        got = product_readiness("SCHOOL_INDICATOR_SERIES")
        self.assertEqual(got["status"], "READY_PARTIAL_ONLY")
        self.assertFalse(got["full_materialization_ready"])
        self.assertIn("BASE_MESTRA_LIMEIRA_V05", got["needs_handoff"])
        self.assertIn("CAMADA_ANALITICA_V06_40_ESCOLAS_V08", got["needs_handoff"])

    def test_normative_brain_is_document_ready_but_not_legal_proof(self):
        obj = json.loads(REGISTRY.read_text(encoding="utf-8"))
        assets = {row["id"]: row for row in obj["assets"]}
        brain = assets["CEREBRO_NORMATIVO_GESTAO_ESCOLAR_LIMEIRA"]
        self.assertIn("READY_FOR_DOCUMENT_INDEX", brain["readiness"])
        self.assertIn("SYNTHESIS_NE_LEGAL_PROOF", brain["constraints"])
        self.assertEqual(obj["precedence"]["normative"][0], "EXACT_OFFICIAL_NORMATIVE_DOCUMENT")
        product = product_readiness("PLANNING_DOCUMENT_INDEX")
        self.assertEqual(product["status"], "READY_FROM_EXISTING_CUSTODY")

    def test_fiscal_md_is_partial_and_official_structured_sources_win(self):
        obj = json.loads(REGISTRY.read_text(encoding="utf-8"))
        assets = {row["id"]: row for row in obj["assets"]}
        md = assets["MD_01_2_BASE_UNIFICADA_FISCAL_ORCAMENTARIA_LIMEIRA"]
        self.assertIn("READY_FOR_PARTIAL_STRUCTURED_EXTRACTION", md["readiness"])
        self.assertIn("INTERPRETATION_NE_NUMERIC_TRUTH", md["constraints"])
        self.assertEqual(
            obj["precedence"]["fiscal"][0],
            "OFFICIAL_STRUCTURED_TCE_SIOPE_SICONFI_FUNDEB",
        )
        product = product_readiness("FISCAL_SERIES")
        self.assertEqual(product["status"], "READY_PARTIAL_ONLY")

    def test_md013b_is_referenced_but_needs_handoff(self):
        obj = json.loads(REGISTRY.read_text(encoding="utf-8"))
        assets = {row["id"]: row for row in obj["assets"]}
        corpus = assets["MD_01_3B_CORPUS"]
        self.assertEqual(
            corpus["custody"],
            "REFERENCED_BY_CORPUS_BUT_BASE_FILE_NOT_CURRENTLY_RUNTIME_ACCESSIBLE",
        )
        self.assertEqual(corpus["referenced_document_count"], 194)
        self.assertIn("NEEDS_BASE_STRUCTURED_FILE_HANDOFF", corpus["readiness"])

    def test_existing_system_products_do_not_require_new_custody_input(self):
        for product_name in ("JOM_EVENT_INDEX", "ACCOUNTING_LEDGER"):
            got = product_readiness(product_name)
            self.assertEqual(got["status"], "NO_NEW_CUSTODY_INPUT_REQUIRED")
            self.assertTrue(got["full_materialization_ready"])

    def test_coverage_is_14_of_15_with_territory_explicit_gap(self):
        got = domain_coverage()
        self.assertEqual(got["domain_count"], 15)
        self.assertTrue(got["all_domains_explicit"])
        self.assertEqual(got["covered_or_partial_count"], 14)
        self.assertEqual(got["explicit_gap_count"], 1)
        self.assertEqual(got["explicit_gaps"], ["TERRITORY_CONTEXT"])

    def test_handoff_priority_is_base_then_extension_then_document_corpus(self):
        got = recommended_handoffs()
        ids = [row["asset_id"] for row in got["priorities"]]
        self.assertEqual(ids[:3], [
            "BASE_MESTRA_LIMEIRA_V05",
            "CAMADA_ANALITICA_V06_40_ESCOLAS_V08",
            "MD_01_3B_CORPUS",
        ])
        self.assertTrue(got["remote_execution_should_wait"])

    def test_task178_remote_serving_is_noncanonical_until_custody_mapping(self):
        obj = json.loads(CROSSWALK.read_text(encoding="utf-8"))
        note = obj["noncanonical_task_note"]
        self.assertTrue(note["task_178_remote_serving_should_wait"])
        self.assertIn("MAP_AND_INGEST_EXISTING_CUSTODY", note["reason"])

    def test_mutating_precedence_fails_closed(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        registry["precedence"]["school_numeric"][0] = "INDICATORS_COLLECTION_2026_PUBLICATION:VOLUME_I_V07"
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(Task179Stop, "TASK179_SCHOOL_PRECEDENCE"):
                validate_contracts(path, CROSSWALK, ONTOLOGY)

    def test_mutating_normative_proof_guard_fails_closed(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        for asset in registry["assets"]:
            if asset["id"] == "CEREBRO_NORMATIVO_GESTAO_ESCOLAR_LIMEIRA":
                asset["constraints"].remove("SYNTHESIS_NE_LEGAL_PROOF")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(Task179Stop, "TASK179_NORMATIVE_PROOF_GUARD"):
                validate_contracts(path, CROSSWALK, ONTOLOGY)

    def test_summary_is_deterministic_shape(self):
        got = summary()
        self.assertEqual(got["schema"], "TASK179_EXISTING_CUSTODY_SUMMARY_V1")
        self.assertEqual(len(got["products"]), 6)
        self.assertEqual(got["coverage"]["covered_or_partial_count"], 14)
        self.assertEqual(got["handoffs"]["first"]["asset_id"], "BASE_MESTRA_LIMEIRA_V05")


if __name__ == "__main__":
    unittest.main()
