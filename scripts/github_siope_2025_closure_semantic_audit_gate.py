#!/usr/bin/env python3
"""TASK 006 T0/offline evidence-sufficiency gate for SIOPE 2025 closure and semantics."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "config" / "siope_2025_closure_semantic_audit.v1.json"
REGIMES = ROOT / "config" / "siope_historical_regimes.v1.json"
PROMOTION = ROOT / "config" / "siope_2025_regime_promotion_assessment.v1.json"
NORMALIZED = ROOT / "docs" / "evidence" / "TASK_004C_SIOPE_2025_SECOND_LIVE_SUCCESS_NORMALIZED_0.8.0.json"
HISTORICAL = ROOT / "docs" / "evidence" / "M7_SIOPE_POST_GENERALIZATION_OFFLINE_REVIEW_0.8.0.json"
GOLD_SCOPE = ROOT / "docs" / "references" / "M7_SIOPE_LIMEIRA_GOLD_ARITHMETIC_SCOPE_0.8.0.md"
RESEARCH = ROOT / "docs" / "research" / "SIOPE_HISTORICAL_REGIME_EVIDENCE_V1.md"
PASS = "PASS_SIOPE_2025_CLOSURE_SEMANTIC_AUDIT_T0"


class ClosureSemanticAuditError(RuntimeError):
    pass


def _stop(ok: bool, code: str) -> None:
    if not ok:
        raise ClosureSemanticAuditError(f"STOP_SIOPE_2025_CLOSURE_SEMANTIC_AUDIT_{code}")


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ClosureSemanticAuditError(f"STOP_SIOPE_2025_CLOSURE_SEMANTIC_AUDIT_UNREADABLE_{path.name}") from exc
    _stop(isinstance(value, dict), f"OBJECT_{path.name}")
    return value


def validate(
    audit_path: Path = AUDIT,
    regimes_path: Path = REGIMES,
    promotion_path: Path = PROMOTION,
    normalized_path: Path = NORMALIZED,
    historical_path: Path = HISTORICAL,
) -> dict:
    audit = _load(audit_path)
    regimes = _load(regimes_path)
    promotion = _load(promotion_path)
    normalized = _load(normalized_path)
    historical = _load(historical_path)

    _stop(audit.get("schema") == "SIOPE_2025_CLOSURE_SEMANTIC_AUDIT_V1", "SCHEMA")
    _stop(audit.get("task") == "TASK_006" and audit.get("tier") == "T0_OFFLINE", "TASK_TIER")
    _stop(audit.get("source_get_count") == 0, "SOURCE_GET")
    _stop(audit.get("drive_read_count") == 0 and audit.get("drive_write_count") == 0, "DRIVE")
    _stop(audit.get("persistence") is False and audit.get("publication") is False, "EFFECTS")
    _stop(audit.get("new_authorization_created") is False, "AUTHORIZATION")
    _stop(audit.get("gold_computation_performed") is False, "GOLD_COMPUTATION")

    _stop(normalized.get("evidence_schema") == "SIOPE_2025_T1_SECOND_LIVE_SUCCESS_EVIDENCE_NORMALIZED_V1", "NORMALIZED_SCHEMA")
    _stop(normalized.get("runner", {}).get("outcome") == "2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN", "NORMALIZED_OUTCOME")
    _stop(normalized.get("semantic_boundary_at_observation", {}).get("annual_closure_status") == "UNKNOWN", "NORMALIZED_CLOSURE")
    _stop(normalized.get("semantic_boundary_at_observation", {}).get("semantic_comparability_status") == "UNKNOWN", "NORMALIZED_COMPARABILITY")
    _stop(normalized.get("semantic_boundary_at_observation", {}).get("any_metric_proven") is False, "NORMALIZED_GOLD")

    _stop(historical.get("coverage", {}).get("first_year") == 2016, "HISTORICAL_FIRST_YEAR")
    _stop(historical.get("coverage", {}).get("last_year") == 2024, "HISTORICAL_LAST_YEAR")
    _stop(historical.get("coverage", {}).get("period_by_year", {}).get("2017") == 6, "HISTORICAL_2017_P6")
    _stop(historical.get("coverage", {}).get("period_by_year", {}).get("2024") == 6, "HISTORICAL_2024_P6")

    try:
        gold_text = GOLD_SCOPE.read_text(encoding="utf-8")
        research_text = RESEARCH.read_text(encoding="utf-8")
    except Exception as exc:
        raise ClosureSemanticAuditError("STOP_SIOPE_2025_CLOSURE_SEMANTIC_AUDIT_REFERENCE_UNREADABLE") from exc
    _stop("exercício 2024, período 6" in gold_text, "GOLD_SCOPE_2024_ONLY")
    _stop("somente um resumo aritmético derivado" in gold_text, "GOLD_SCOPE_ARITHMETIC_ONLY")
    _stop("Engineering fact to verify/pin from the document" in research_text, "OFFICIAL_RULE_NOT_PINNED")
    _stop("Do not infer that matching names imply semantic equivalence" in research_text, "NAME_EQUIVALENCE_GUARD")

    gate_a = audit.get("gate_a_annual_closure", {})
    _stop(gate_a.get("status") == "NOT_PROVEN", "GATE_A_STATUS")
    _stop(gate_a.get("canonical_state_remains") == "UNKNOWN", "GATE_A_CANONICAL")
    _stop(gate_a.get("promotion_authorized") is False, "GATE_A_PROMOTION")
    _stop(len(gate_a.get("missing_proof", [])) >= 2, "GATE_A_MISSING_PROOF")

    gate_b = audit.get("gate_b_semantic_comparability", {})
    _stop(gate_b.get("status") == "NOT_PROVEN", "GATE_B_STATUS")
    _stop(gate_b.get("canonical_state_remains") == "UNKNOWN", "GATE_B_CANONICAL")
    _stop(gate_b.get("promotion_authorized") is False, "GATE_B_PROMOTION")
    _stop(len(gate_b.get("missing_proof", [])) >= 4, "GATE_B_MISSING_PROOF")

    result = audit.get("resulting_state", {})
    _stop(result.get("year_2025_status") == "PROVEN_STRUCTURAL_RECENT", "RESULT_2025")
    _stop(result.get("p6_status") == "PROVEN_AVAILABLE_CLOSURE_UNKNOWN", "RESULT_P6")
    _stop(result.get("annual_closure_status") == "UNKNOWN", "RESULT_CLOSURE")
    _stop(result.get("semantic_comparability_status") == "UNKNOWN", "RESULT_COMPARABILITY")
    _stop(result.get("closed_series_eligible") is False, "RESULT_CLOSED_SERIES")
    _stop(result.get("closed_annual_series_last_year") == 2024, "RESULT_SERIES_BOUNDARY")
    _stop(result.get("gold_metrics_status") == "UNKNOWN", "RESULT_GOLD")
    _stop(result.get("year_2026_status") == "UNPROVEN_CURRENT_YEAR", "RESULT_2026")

    by_year = {}
    for regime in regimes.get("regimes", []):
        for year in regime.get("years", []):
            by_year[year] = regime
    y2025 = by_year.get(2025, {})
    _stop(regimes.get("closed_annual_series") == {"first_year": 2016, "last_year": 2024}, "MAP_SERIES_BOUNDARY")
    _stop(y2025.get("status") == "PROVEN_STRUCTURAL_RECENT", "MAP_2025")
    _stop(y2025.get("period") == {"value": 6, "status": "PROVEN_AVAILABLE_CLOSURE_UNKNOWN"}, "MAP_P6")
    _stop(y2025.get("annual_closure_status") == "UNKNOWN", "MAP_CLOSURE")
    _stop(y2025.get("semantic_comparability_status") == "UNKNOWN", "MAP_COMPARABILITY")
    _stop(y2025.get("closed_series_eligible") is False, "MAP_CLOSED_SERIES")
    _stop(y2025.get("gold_metrics_status") == "UNKNOWN", "MAP_GOLD")
    _stop(by_year.get(2026, {}).get("status") == "UNPROVEN_CURRENT_YEAR", "MAP_2026")

    _stop(promotion.get("approved_narrow_promotion", {}).get("annual_closure_status") == "UNKNOWN", "PROMOTION_CLOSURE")
    _stop(promotion.get("approved_narrow_promotion", {}).get("semantic_comparability_status") == "UNKNOWN", "PROMOTION_COMPARABILITY")
    _stop(promotion.get("approved_narrow_promotion", {}).get("closed_series_eligible") is False, "PROMOTION_CLOSED_SERIES")
    _stop(promotion.get("approved_narrow_promotion", {}).get("gold_metrics_status") == "UNKNOWN", "PROMOTION_GOLD")

    for key, value in audit.get("guards", {}).items():
        _stop(value is False, f"GUARD_{key.upper()}")

    return {
        "status": PASS,
        "tier": "T0_OFFLINE",
        "source_get_count": 0,
        "gate_a_annual_closure": "NOT_PROVEN",
        "gate_b_semantic_comparability": "NOT_PROVEN",
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "closed_annual_series_last_year": 2024,
        "gold_metrics_status": "UNKNOWN",
        "year_2026_status": "UNPROVEN_CURRENT_YEAR",
    }


def main() -> int:
    try:
        result = validate()
    except ClosureSemanticAuditError as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
