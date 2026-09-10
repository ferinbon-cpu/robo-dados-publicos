from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_M6_SIOPE_NUM_POPU_FNDE_DISPOSITION_0.8.0.json"


class TestTask010NREM6SiopeNumPopuFndeDisposition(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_primary_document_identity_and_hash(self) -> None:
        doc = self.obj["primary_document"]
        self.assertEqual(self.obj["evidence_schema"], "TASK_010N_R_E_M6_SIOPE_NUM_POPU_FNDE_DISPOSITION_V1")
        self.assertEqual(self.obj["issue"], 748)
        self.assertEqual(doc["authority"], "FNDE")
        self.assertEqual(doc["fala_br_nup"], "23546.111503/2026-95")
        self.assertEqual(doc["sei_document_number"], "5787039")
        self.assertEqual(doc["sha256"], "9efac0ca3167ac9b7fab01b05b9f2f31822b069d75d9c41c3242458740e04183")
        self.assertEqual(doc["bytes"], 68996)
        self.assertFalse(doc["raw_pdf_committed"])

    def test_source_statements_preserve_fnde_boundaries(self) -> None:
        src = self.obj["source_statements"]
        self.assertEqual(src["field_classification"], "LEGACY_FIELD")
        self.assertEqual(src["original_load_reference"], "IBGE_DATA")
        self.assertFalse(src["used_in_siope_calculations"])
        self.assertFalse(src["used_in_siope_reports_general"])
        self.assertEqual(src["display_exception"], "MUNICIPIOS_TRANSMITIDOS_POR_UF")
        self.assertFalse(src["2025_value_matches_2025_population_estimate_assurable"])
        self.assertFalse(src["2025_value_matches_census_assurable"])
        self.assertFalse(src["2025_value_matches_any_specific_temporal_cut_assurable"])
        self.assertEqual(src["recommended_population_source"], "OFFICIAL_IBGE_BASES_DIRECTLY")
        self.assertEqual(src["recommended_treatment_of_num_popu_for_population_analysis"], "DISREGARD")

    def test_canonical_disposition_closes_use_question_not_vintage(self) -> None:
        state = self.obj["canonical_disposition"]
        self.assertEqual(state["S1_NUM_POPU"], "PROVEN_LEGACY_NON_ANALYTIC_FIELD_DO_NOT_USE_FOR_POPULATION_ANALYSIS")
        self.assertEqual(state["exact_2025_source_vintage"], "UNDETERMINED")
        self.assertEqual(state["exact_2025_reference_date_or_year"], "UNDETERMINED")
        self.assertEqual(state["population_analysis_route"], "USE_OFFICIAL_IBGE_SOURCE_AND_EXPLICIT_REFERENCE_PERIOD")
        self.assertEqual(state["value_reconciliation_against_ibge_2025"], "FORBIDDEN_BY_SOURCE_DISPOSITION")

    def test_release_gate_effect_is_fail_closed(self) -> None:
        effect = self.obj["release_gate_effect"]
        self.assertEqual(effect["B1_new_state"], "RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS")
        self.assertTrue(effect["B1_does_not_authorize_gold_2025_by_itself"])
        self.assertTrue(effect["B2_financial_alias_bridge_unchanged"])
        self.assertTrue(effect["B3_annual_finality_unchanged"])
        self.assertTrue(effect["comparability_unchanged"])
        self.assertFalse(effect["automatic_release_promotion"])

    def test_guards(self) -> None:
        guards = self.obj["guards"]
        self.assertFalse(guards["ibge_reference_inferred_as_2025_vintage"])
        self.assertFalse(guards["num_popu_treated_as_2025_population"])
        self.assertFalse(guards["num_popu_used_as_population_denominator"])
        self.assertFalse(guards["historical_values_rewritten"])
        self.assertFalse(guards["gold_2025_computed"])
        self.assertFalse(guards["release_promoted"])
        self.assertEqual(guards["remote_writes"], 0)
        self.assertFalse(guards["source_acquisition_by_robot"])


if __name__ == "__main__":
    unittest.main()
