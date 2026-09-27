#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 010N-R-E public-contract semantic evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_SIOPE_PUBLIC_CONTRACT_SEMANTIC_EVIDENCE_GATE_0.8.0.json"
TASK_007 = ROOT / "docs/evidence/TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_EVIDENCE_0.8.0.json"
TASK_009 = ROOT / "docs/evidence/TASK_009E_L_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_RUN_1_0.8.0.json"
EXPECTED_BASE = "0665893b3ce8a6701bbe3c3e6901a7f00ef4fc7a"
EXPECTED_DECISION = "PUBLIC_CONTRACT_EVIDENCE_PARTIAL_OFFLINE"
EXPECTED_ALIASES = [
    "NUM_POPU",
    "VAL_RECE_PREV_ATUA",
    "VAL_RECE_REAL",
    "VAL_DESP_DOTA_ATUA",
    "VAL_DESP_EMPE",
    "VAL_DESP_LIQU",
    "VAL_DESP_PAGA",
    "VL_DESP_DOTA_ATUA_EDU",
    "VL_DESP_EMPE_EDU",
    "VL_DESP_LIQU_EDU",
    "VL_DESP_PAGA_EDU",
]
EXPECTED_STATE = {
    "release_0_7_0": "ACTIVE",
    "release_0_8_0": "CANDIDATE",
    "year_2025": "PROVEN_STRUCTURAL_RECENT",
    "S1_NUM_POPU": "NOT_PROVEN",
    "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
    "annual_closure_status": "UNKNOWN",
    "semantic_comparability_status": "UNKNOWN",
    "gold_metrics_status": "UNKNOWN/BLOCKED",
    "closed_annual_series": "2016-2024",
    "year_2026": "UNPROVEN_CURRENT_YEAR",
}


def validate(data, task_007, task_009):
    if data.get("base_sha") != EXPECTED_BASE or data.get("tier") != "T0_OFFLINE":
        raise ValueError("base SHA and T0 tier must remain pinned")
    if data.get("decision") != EXPECTED_DECISION:
        raise ValueError("decision must remain PUBLIC_CONTRACT_EVIDENCE_PARTIAL_OFFLINE")

    summary = data.get("summary", {})
    expected_summary = {
        "required_input_count": 11,
        "proven_count": 0,
        "partial_count": 11,
        "ambiguous_count": 0,
        "not_found_count": 0,
        "official_historical_financial_concepts_defined": 10,
        "current_2025_odata_alias_to_concept_identity_proven_count": 0,
        "num_popu_official_definition_proven": False,
        "num_popu_official_source_proven": False,
        "num_popu_vintage_rule_proven": False,
    }
    if summary != expected_summary:
        raise ValueError("summary drifted or overclaims semantic proof")

    matrix = data.get("matrix", [])
    if [row.get("alias") for row in matrix] != EXPECTED_ALIASES:
        raise ValueError("matrix must contain exactly the 11 required aliases in canonical order")
    if any(row.get("status") != "PARTIAL" for row in matrix):
        raise ValueError("all 11 inputs must remain PARTIAL in this offline evidence gate")

    documentary = task_007.get("field_definition_summary", {})
    if documentary.get("historical_financial_concepts_with_official_dictionary_counterparts") != 10:
        raise ValueError("TASK 007 no longer supports exactly ten historical financial concepts")
    if documentary.get("2025_odata_alias_identity_proven_count") != 0:
        raise ValueError("TASK 007 does not support current alias identity promotion")
    if documentary.get("official_primary_definition_missing_for") != ["NUM_POPU"]:
        raise ValueError("TASK 007 NUM_POPU limitation drifted")

    q = task_009.get("question_results", {})
    s1 = q.get("S1_NUM_POPU", {})
    s2 = q.get("S2_FINANCIAL_ALIAS_BRIDGE", {})
    if s1.get("status") != "NOT_PROVEN" or s2.get("status") != "NOT_PROVEN":
        raise ValueError("TASK 009 S1/S2 fail-closed result drifted")
    if s2.get("current_alias_identity_proven_count") != 0 or s2.get("historical_concept_definitions_reaffirmed_count") != 10:
        raise ValueError("TASK 009 alias/concept counts drifted")

    if data.get("edu_guard", {}).get("EDU_equals_MDE_authorized") is not False:
        raise ValueError("EDU=MDE must remain prohibited")

    next_class = data.get("smallest_next_remote_evidence_class", {})
    if next_class.get("class") != "PRIMARY_OFFICIAL_PUBLIC_CONTRACT_ALIAS_TO_CONCEPT_EVIDENCE":
        raise ValueError("next evidence class must remain primary official public-contract evidence")
    if next_class.get("remote_execution_authorized_here") is not False:
        raise ValueError("this T0 gate cannot authorize remote execution")
    if next_class.get("internal_reverse_engineering_default") is not False:
        raise ValueError("internal reverse engineering cannot become the default")

    if data.get("canonical_state") != EXPECTED_STATE:
        raise ValueError("canonical state was promoted, downgraded, or drifted")
    guards = data.get("guards", {})
    if len(guards) != 9 or any(value is not False for value in guards.values()):
        raise ValueError("all nine guards must exist and remain false")
    if data.get("next_gate") != "SEPARATE_OWNER_AUTHORIZED_PRIMARY_OFFICIAL_PUBLIC_CONTRACT_EVIDENCE_ACQUISITION_ONLY_IF_REVIEW_ACCEPTS_THIS_PARTIAL_RESULT":
        raise ValueError("next gate must remain a separate owner-authorized evidence acquisition")


def main():
    validate(
        json.loads(EVIDENCE.read_text(encoding="utf-8")),
        json.loads(TASK_007.read_text(encoding="utf-8")),
        json.loads(TASK_009.read_text(encoding="utf-8")),
    )
    print("PASS_TASK_010N_R_E_SIOPE_PUBLIC_CONTRACT_SEMANTIC_EVIDENCE_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
