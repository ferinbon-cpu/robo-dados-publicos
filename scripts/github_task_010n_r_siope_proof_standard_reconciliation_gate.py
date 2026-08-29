#!/usr/bin/env python3
"""Fail-closed T0 gate for the revised TASK 010N-R reconciliation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_SIOPE_PROOF_STANDARD_RECONCILIATION_0.8.0.json"
TASK_007 = ROOT / "docs/evidence/TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_EVIDENCE_0.8.0.json"
EXPECTED_BASE = "d0e75e1dc47de6157e49864ca97bbcb640ba65df"
EXPECTED_DECISION = "STANDARD_NOT_YET_DETERMINABLE"
EXPECTED_YEARS = ["2016", "2017-2024", "2025"]
EXPECTED_P1_FIELDS = ["exact_odata_alias", "official_operational_concept", "definition", "unit", "scope", "aggregation", "accounting_stage", "NUM_POPU_source_and_vintage", "temporal_regime_applicability", "arithmetic_formula_compatibility"]
EXPECTED_STATE = {
    "release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE",
    "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN",
    "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "annual_closure_status": "UNKNOWN",
    "semantic_comparability_status": "UNKNOWN", "gold_2025": "UNKNOWN/BLOCKED",
    "closed_annual_series": "2016-2024", "historical_2016_2024": "NO_AUTOMATIC_DOWNGRADE",
    "year_2026": "UNPROVEN_CURRENT_YEAR",
}


def validate(data, task_007):
    if data.get("base_sha") != EXPECTED_BASE or data.get("tier") != "T0_OFFLINE":
        raise ValueError("base and T0 tier must remain pinned")
    if data.get("decision") != EXPECTED_DECISION:
        raise ValueError("revised decision must remain STANDARD_NOT_YET_DETERMINABLE")
    propositions = data.get("propositions", {})
    if propositions.get("P1") != "UNIFORM_PUBLIC_CONTRACT_STANDARD_JUSTIFIED" or propositions.get("P2") != "INTERNAL_BRIDGE_STANDARD_REQUIRED":
        raise ValueError("P1 and P2 must remain explicit")
    if propositions.get("P2_status") != "NOT_DEMONSTRATED_NECESSARY":
        raise ValueError("gate must not prematurely fix P2")
    if [row.get("years") for row in data.get("comparison", [])] != EXPECTED_YEARS:
        raise ValueError("comparison must contain exactly 2016, 2017-2024, and 2025")
    if data.get("p1_minimum_public_contract_evidence") != EXPECTED_P1_FIELDS:
        raise ValueError("P1 public-contract evidence criteria drifted")
    if data.get("years_satisfying_complete_p1_standard_in_repo") != []:
        raise ValueError("no year may be claimed to satisfy complete P1 evidence")
    documentary = task_007.get("field_definition_summary", {})
    if documentary != {
        "required_gold_input_count": 11,
        "historical_financial_concepts_with_official_dictionary_counterparts": 10,
        "official_primary_definition_missing_for": ["NUM_POPU"],
        "2025_odata_alias_identity_proven_count": 0,
        "semantic_bridge_result": "PARTIAL_NOT_PROVEN",
    }:
        raise ValueError("TASK 007 documentary evidence drifted")
    pinned = data.get("task_007_evidence", {})
    if (pinned.get("financial_concepts_defined"), pinned.get("current_odata_aliases_defined"), pinned.get("NUM_POPU_defined"), pinned.get("result")) != (10, 0, False, "PARTIAL_NOT_PROVEN"):
        raise ValueError("TASK 007 finding is not represented exactly")
    discriminator = data.get("smallest_discriminating_evidence_class", {})
    if discriminator.get("class") != "PRIMARY_OFFICIAL_PUBLIC_CONTRACT_ALIAS_TO_CONCEPT_EVIDENCE" or discriminator.get("reverse_engineering_default") is not False:
        raise ValueError("smallest evidence class must prioritize official public contract evidence")
    if data.get("canonical_state") != EXPECTED_STATE:
        raise ValueError("canonical state was promoted, downgraded, or drifted")
    if data.get("scope") != {"network_requests": 0, "drive_reads": 0, "drive_writes": 0, "gold_2025_computed": False}:
        raise ValueError("offline/Drive/Gold scope was widened")
    guards = data.get("guards", {})
    if len(guards) != 10 or any(value is not False for value in guards.values()):
        raise ValueError("all ten fail-closed guards must exist and remain false")
    if data.get("next_gate_recommended") != "TASK_010N_R_PUBLIC_CONTRACT_SEMANTIC_EVIDENCE_GATE":
        raise ValueError("next gate must seek public-contract evidence, not open TASK 010O")


def main():
    validate(json.loads(EVIDENCE.read_text(encoding="utf-8")), json.loads(TASK_007.read_text(encoding="utf-8")))
    print("PASS_TASK_010N_R_SIOPE_PROOF_STANDARD_RECONCILIATION_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
