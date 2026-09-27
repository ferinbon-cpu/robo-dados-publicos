#!/usr/bin/env python3
"""Fail-closed offline gate for the TASK 010N continuity audit."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_SIOPE_2016_2025_CONTRACT_CONTINUITY_AUDIT_0.8.0.json"
ALLOWED_RESULTS = {
    "A": "CONTINUITY_SUPPORTED_NO_POSITIVE_BREAK_FOUND",
    "B": "HISTORICAL_PROOF_STANDARD_INSUFFICIENT",
    "C": "POSITIVE_SEMANTIC_BREAK_FOUND",
}
EXPECTED_STATE = {
    "release_0_8_0": "CANDIDATE",
    "year_2025": "PROVEN_STRUCTURAL_RECENT",
    "P6_availability": "PROVEN_AVAILABLE_CLOSURE_UNKNOWN",
    "P6_documentary_role": "P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN",
    "S1_NUM_POPU": "NOT_PROVEN",
    "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
    "annual_closure_status": "UNKNOWN",
    "semantic_comparability_status": "UNKNOWN",
    "gold_metrics_status": "UNKNOWN/BLOCKED",
    "closed_annual_series": "2016-2024",
    "year_2026": "UNPROVEN_CURRENT_YEAR",
}
REQUIRED_GUARDS = {
    "remote_network_authorized",
    "drive_write_authorized",
    "gold_2025_authorized",
    "semantic_promotion_authorized",
    "annual_series_expansion_authorized",
    "release_promotion_authorized",
    "current_year_2026_authorized",
}


def validate(data: dict[str, Any]) -> None:
    result = data.get("result", {})
    result_class = result.get("class")
    if result_class not in ALLOWED_RESULTS or result.get("code") != ALLOWED_RESULTS[result_class]:
        raise ValueError("result must be exactly one internally consistent A/B/C class")
    if result_class != "B":
        raise ValueError("pinned TASK 010N evidence must remain class B")
    if data.get("canonical_state") != EXPECTED_STATE:
        raise ValueError("canonical state was promoted or drifted")
    guards = data.get("guards", {})
    if set(guards) != REQUIRED_GUARDS or any(guards.values()):
        raise ValueError("all required authorizations must exist and remain false")
    years = [row.get("year") for row in data.get("annual_matrix", [])]
    if years != list(range(2016, 2026)):
        raise ValueError("annual matrix must contain exactly 2016..2025")
    if data.get("scope", {}).get("network_requests") != 0:
        raise ValueError("TASK 010N must remain offline")
    if data.get("scope", {}).get("gold_2025_computed") is not False:
        raise ValueError("Gold 2025 must not be computed")
    breaks = data.get("positive_break_audit", {}).get("positive_breaks_found")
    break_result = data.get("positive_break_audit", {}).get("result")
    if breaks == [] and break_result != "NO_POSITIVE_BREAK_EVIDENCE_FOUND":
        raise ValueError("absence of evidence must not be classified as a positive break")
    if result_class == "C" and not breaks:
        raise ValueError("class C requires concrete positive break evidence")


def main() -> int:
    validate(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    print("PASS_TASK_010N_SIOPE_CONTRACT_CONTINUITY_AUDIT_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
