#!/usr/bin/env python3
"""TASK 005 T0/offline gate for the narrow SIOPE 2025 structural regime promotion."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_regime_promotion_assessment.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_004C_SIOPE_2025_SECOND_LIVE_SUCCESS_0.8.0.json"
REGIMES = ROOT / "config" / "siope_historical_regimes.v1.json"
MATRIX = ROOT / "config" / "siope_historical_evidence_matrix.v1.json"
POLICY = ROOT / "config" / "automation_policy.v1.json"

PASS = "PASS_SIOPE_2025_REGIME_PROMOTION_T0"
REQUIRED_GOLD_FIELDS = {
    "VAL_RECE_REAL", "VAL_RECE_PREV_ATUA", "VAL_DESP_PAGA", "VAL_DESP_DOTA_ATUA",
    "VL_DESP_PAGA_EDU", "VL_DESP_DOTA_ATUA_EDU", "VL_DESP_EMPE_EDU", "VAL_DESP_EMPE",
    "VL_DESP_LIQU_EDU", "VAL_DESP_LIQU", "NUM_POPU",
}


class Siope2025RegimePromotionError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025RegimePromotionError(f"STOP_SIOPE_2025_REGIME_PROMOTION_{code}")


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise Siope2025RegimePromotionError(f"STOP_SIOPE_2025_REGIME_PROMOTION_UNREADABLE_{path.name}") from exc
    _stop(isinstance(value, dict), f"OBJECT_{path.name}")
    return value


def validate(
    assessment_path: Path = ASSESSMENT,
    evidence_path: Path = EVIDENCE,
    regimes_path: Path = REGIMES,
    matrix_path: Path = MATRIX,
    policy_path: Path = POLICY,
) -> dict:
    assessment = _load(assessment_path)
    evidence = _load(evidence_path)
    regimes_payload = _load(regimes_path)
    matrix = _load(matrix_path)
    policy = _load(policy_path)

    _stop(assessment.get("schema") == "SIOPE_2025_REGIME_PROMOTION_ASSESSMENT_V1", "ASSESSMENT_SCHEMA")
    _stop(assessment.get("task") == "TASK_005", "TASK")
    _stop(assessment.get("tier") == "T0_OFFLINE", "TIER")
    _stop(assessment.get("source_get_count") == 0, "TASK005_SOURCE_GET")
    _stop(assessment.get("drive_read_count") == 0 and assessment.get("drive_write_count") == 0, "TASK005_DRIVE")
    _stop(assessment.get("persistence") is False and assessment.get("publication") is False, "TASK005_EFFECTS")
    _stop(assessment.get("new_authorization_created") is False, "TASK005_AUTHORIZATION")

    _stop(evidence.get("schema") == "SIOPE_2025_T1_SECOND_LIVE_SUCCESS_EVIDENCE_V1", "EVIDENCE_SCHEMA")
    _stop(evidence.get("run_id") == 33204578436, "EVIDENCE_RUN")
    _stop(evidence.get("source_get_count") == 7, "EVIDENCE_GET_COUNT")
    _stop(evidence.get("observed_periods") == [1, 2, 3, 4, 5, 6], "EVIDENCE_PERIODS")
    _stop(evidence.get("outcome") == "2025_P6_SCHEMA_EXACT_SEMANTICS_AND_CLOSURE_UNKNOWN", "EVIDENCE_OUTCOME")
    _stop(evidence.get("schema", {}).get("schema_exact") is True, "EVIDENCE_SCHEMA_EXACT")
    _stop(evidence.get("schema", {}).get("observed_field_count") == 52, "EVIDENCE_FIELD_COUNT")
    _stop(evidence.get("schema", {}).get("observed_fields_sha256") == "cd601ba7ee604df2e157028a2a18eefa226659fcbe0f2288937d3342d00e12a6", "EVIDENCE_FIELD_HASH")
    required_status = evidence.get("schema", {}).get("required_gold_input_status", {})
    _stop(set(required_status) == REQUIRED_GOLD_FIELDS, "EVIDENCE_REQUIRED_FIELDS_SET")
    _stop(all(value == "PRESENT" for value in required_status.values()), "EVIDENCE_REQUIRED_FIELDS_PRESENT")
    semantic = evidence.get("semantic_boundary", {})
    _stop(semantic.get("annual_closure_status") == "UNKNOWN", "EVIDENCE_CLOSURE")
    _stop(semantic.get("semantic_comparability_status") == "UNKNOWN", "EVIDENCE_COMPARABILITY")
    _stop(semantic.get("any_metric_proven") is False, "EVIDENCE_METRIC_PROMOTION")
    _stop(evidence.get("effects", {}).get("drive_read_count") == 0, "EVIDENCE_DRIVE_READ")
    _stop(evidence.get("effects", {}).get("drive_write_count") == 0, "EVIDENCE_DRIVE_WRITE")
    _stop(evidence.get("effects", {}).get("response_body_persisted") is False, "EVIDENCE_RESPONSE_PERSIST")
    _stop(evidence.get("effects", {}).get("record_values_persisted") is False, "EVIDENCE_VALUES_PERSIST")
    _stop(evidence.get("effects", {}).get("publication") is False, "EVIDENCE_PUBLICATION")

    classification = assessment.get("classification_matrix", {})
    _stop(classification.get("resource_family_2025", {}).get("status") == "PROVEN", "RESOURCE_STATUS")
    _stop(classification.get("resource_family_2025", {}).get("value") == "Dados_Gerais_Siope", "RESOURCE_FAMILY")
    _stop(classification.get("periods_1_to_6_available", {}).get("status") == "PROVEN", "PERIODS_STATUS")
    _stop(classification.get("periods_1_to_6_available", {}).get("value") == [1, 2, 3, 4, 5, 6], "PERIODS_VALUE")
    _stop(classification.get("p6_availability", {}).get("status") == "PROVEN", "P6_AVAILABILITY")
    _stop(classification.get("p6_annual_role", {}).get("status") == "OBSERVED_SUPPORTED_CANDIDATE", "P6_ANNUAL_ROLE")
    _stop(classification.get("annual_closure", {}).get("status") == "UNKNOWN", "ANNUAL_CLOSURE")
    _stop(classification.get("semantic_comparability_2017_2024", {}).get("status") == "UNKNOWN", "SEMANTIC_COMPARABILITY")
    _stop(classification.get("closed_series_eligibility", {}).get("status") == "UNKNOWN", "CLOSED_SERIES_STATUS")
    _stop(classification.get("closed_series_eligibility", {}).get("value") is False, "CLOSED_SERIES_VALUE")
    _stop(classification.get("gold_metrics", {}).get("status") == "UNKNOWN", "GOLD_STATUS")
    _stop(classification.get("gold_metrics", {}).get("computed") is False, "GOLD_COMPUTED")
    _stop(classification.get("year_2026", {}).get("status") == "UNPROVEN_CURRENT_YEAR", "2026_STATUS")
    _stop(classification.get("year_2026", {}).get("in_scope") is False, "2026_SCOPE")

    promotion = assessment.get("approved_narrow_promotion", {})
    _stop(promotion.get("year_2025_status") == "PROVEN_STRUCTURAL_RECENT", "PROMOTION_STATUS")
    _stop(promotion.get("period") == {"value": 6, "status": "PROVEN_AVAILABLE_CLOSURE_UNKNOWN"}, "PROMOTION_PERIOD")
    _stop(promotion.get("resource_family") == "Dados_Gerais_Siope", "PROMOTION_RESOURCE")
    _stop(promotion.get("schema") == {"status": "PROVEN_2025_P6_SCHEMA", "name": "DADOS_GERAIS_SIOPE_52_FIELDS"}, "PROMOTION_SCHEMA")
    _stop(promotion.get("annual_closure_status") == "UNKNOWN", "PROMOTION_CLOSURE")
    _stop(promotion.get("semantic_comparability_status") == "UNKNOWN", "PROMOTION_COMPARABILITY")
    _stop(promotion.get("closed_series_eligible") is False, "PROMOTION_CLOSED_SERIES")
    _stop(promotion.get("gold_metrics_status") == "UNKNOWN", "PROMOTION_GOLD")

    guards = assessment.get("guards", {})
    for key in (
        "future_batch_execution_authorized", "live_discovery_authorized", "retry_authorized",
        "pagination_authorized", "redirect_authorized", "year_2026_promotion_authorized",
        "gold_computation_authorized", "compliance_authorized", "causal_inference_authorized",
    ):
        _stop(guards.get(key) is False, f"GUARD_{key.upper()}")
    _stop(policy.get("policy_invariants", {}).get("future_batch_execution_authorized") is False, "POLICY_FUTURE_BATCH")

    by_year = {}
    for regime in regimes_payload.get("regimes", []):
        for year in regime.get("years", []):
            by_year[year] = regime
    _stop(regimes_payload.get("closed_annual_series") == {"first_year": 2016, "last_year": 2024}, "MAP_CLOSED_SERIES")
    y2025 = by_year.get(2025, {})
    _stop(y2025.get("id") == "STRUCTURALLY_PROVEN_2025", "MAP_2025_ID")
    _stop(y2025.get("status") == "PROVEN_STRUCTURAL_RECENT", "MAP_2025_STATUS")
    _stop(y2025.get("period") == {"value": 6, "status": "PROVEN_AVAILABLE_CLOSURE_UNKNOWN"}, "MAP_2025_PERIOD")
    _stop(y2025.get("resource_family") == "Dados_Gerais_Siope", "MAP_2025_RESOURCE")
    _stop(y2025.get("schema") == {"status": "PROVEN_2025_P6_SCHEMA", "name": "DADOS_GERAIS_SIOPE_52_FIELDS"}, "MAP_2025_SCHEMA")
    _stop(set(y2025.get("required_fields", [])) == REQUIRED_GOLD_FIELDS, "MAP_2025_FIELDS")
    _stop(y2025.get("annual_closure_status") == "UNKNOWN", "MAP_2025_CLOSURE")
    _stop(y2025.get("semantic_comparability_status") == "UNKNOWN", "MAP_2025_COMPARABILITY")
    _stop(y2025.get("closed_series_eligible") is False, "MAP_2025_CLOSED_SERIES")
    _stop(y2025.get("gold_metrics_status") == "UNKNOWN", "MAP_2025_GOLD")
    y2026 = by_year.get(2026, {})
    _stop(y2026.get("status") == "UNPROVEN_CURRENT_YEAR", "MAP_2026_STATUS")
    _stop(y2026.get("period") == {"value": None, "status": "UNKNOWN"}, "MAP_2026_PERIOD")

    rows = matrix.get("rows", [])
    _stop(len(rows) == 7 and rows[5].get("years") == "2025", "MATRIX_2025_ROW")
    row2025 = rows[5]
    _stop(row2025.get("evidence_class") == "INTERNAL_PROVEN_STRUCTURAL", "MATRIX_2025_EVIDENCE")
    _stop(row2025.get("surface") == "Dados_Gerais_Siope", "MATRIX_2025_SURFACE")
    _stop(row2025.get("annual_period") == "P6_STRUCTURAL_CANDIDATE_CLOSURE_UNKNOWN", "MATRIX_2025_PERIOD")
    _stop(row2025.get("current_fields") == "52_FIELD_SCHEMA_PROVEN_2025_P6", "MATRIX_2025_FIELDS")
    _stop(row2025.get("semantic_break_risk") == "ALL_8_SEMANTIC_COMPARABILITY_UNKNOWN", "MATRIX_2025_SEMANTICS")
    _stop(rows[6].get("annual_period") == "NOT_CLOSED_UNKNOWN", "MATRIX_2026")

    return {
        "status": PASS,
        "tier": "T0_OFFLINE",
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "year_2025_status": "PROVEN_STRUCTURAL_RECENT",
        "p6_status": "PROVEN_AVAILABLE_CLOSURE_UNKNOWN",
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "gold_metrics_status": "UNKNOWN",
        "year_2026_status": "UNPROVEN_CURRENT_YEAR",
    }


def main() -> int:
    try:
        result = validate()
    except Siope2025RegimePromotionError as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
