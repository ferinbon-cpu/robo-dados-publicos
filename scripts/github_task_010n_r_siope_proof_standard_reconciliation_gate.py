#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 010N-R proof-standard reconciliation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_SIOPE_PROOF_STANDARD_RECONCILIATION_0.8.0.json"
EXPECTED_BASE = "d0e75e1dc47de6157e49864ca97bbcb640ba65df"
EXPECTED_DECISION = "INTERNAL_BRIDGE_STANDARD_REQUIRED"
EXPECTED_YEARS = ["2016", "2017-2024", "2025"]
EXPECTED_BRIDGE_FIELDS = ["exact_alias", "authoritative_internal_concept", "definition", "unit", "scope", "aggregation", "accounting_stage", "source", "vintage", "period", "deterministic_mapping_rule"]


def validate(data):
    if data.get("base_sha") != EXPECTED_BASE or data.get("tier") != "T0_OFFLINE":
        raise ValueError("base and T0 tier must remain pinned")
    if data.get("decision") != EXPECTED_DECISION:
        raise ValueError("decision must remain INTERNAL_BRIDGE_STANDARD_REQUIRED")
    if [row.get("years") for row in data.get("comparison", [])] != EXPECTED_YEARS:
        raise ValueError("comparison must contain exactly 2016, 2017-2024, and 2025")
    reconciliation = data.get("historical_states_requiring_future_reconciliation", [])
    if [row.get("years") for row in reconciliation] != ["2016", "2017-2024", "2016-2024"]:
        raise ValueError("historical reconciliation states drifted")
    if data.get("bridge_minimum_fields") != EXPECTED_BRIDGE_FIELDS:
        raise ValueError("minimum bridge evidence must be exact and complete")
    scope = data.get("scope", {})
    if scope != {"network_requests": 0, "drive_reads": 0, "drive_writes": 0, "gold_2025_computed": False}:
        raise ValueError("offline/Drive/Gold scope was widened")
    guards = data.get("guards", {})
    if len(guards) != 9 or any(value is not False for value in guards.values()):
        raise ValueError("all nine fail-closed guards must exist and remain false")
    state = data.get("canonical_state", {})
    expected = {"release_0_8_0": "CANDIDATE", "year_2025": "PROVEN_STRUCTURAL_RECENT", "gold_2025": "UNKNOWN/BLOCKED", "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "closed_annual_series": "2016-2024", "historical_2016_2024": "NO_AUTOMATIC_DOWNGRADE", "year_2026": "UNPROVEN_CURRENT_YEAR"}
    if state != expected:
        raise ValueError("canonical state was promoted, downgraded, or drifted")
    if data.get("next_gate_recommended") != "TASK_010N_R_INTERNAL_BRIDGE_EVIDENCE_GATE":
        raise ValueError("TASK 010O must not be opened")


def main():
    validate(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    print("PASS_TASK_010N_R_SIOPE_PROOF_STANDARD_RECONCILIATION_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
