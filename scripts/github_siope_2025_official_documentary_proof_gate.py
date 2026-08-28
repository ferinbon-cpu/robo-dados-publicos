#!/usr/bin/env python3
"""TASK 007 fail-closed gate for official SIOPE 2025 documentary evidence."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_official_documentary_proof.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_EVIDENCE_0.8.0.json"
REGIMES = ROOT / "config" / "siope_historical_regimes.v1.json"
PRIOR_AUDIT = ROOT / "config" / "siope_2025_closure_semantic_audit.v1.json"
LIVE_NORMALIZED = ROOT / "docs" / "evidence" / "TASK_004C_SIOPE_2025_SECOND_LIVE_SUCCESS_NORMALIZED_0.8.0.json"
PASS = "PASS_SIOPE_2025_OFFICIAL_DOCUMENTARY_PROOF_T0"

REQUIRED_GOLD_FIELDS = {
    "NUM_POPU",
    "VAL_DESP_DOTA_ATUA",
    "VAL_DESP_EMPE",
    "VAL_DESP_LIQU",
    "VAL_DESP_PAGA",
    "VAL_RECE_PREV_ATUA",
    "VAL_RECE_REAL",
    "VL_DESP_DOTA_ATUA_EDU",
    "VL_DESP_EMPE_EDU",
    "VL_DESP_LIQU_EDU",
    "VL_DESP_PAGA_EDU",
}


class DocumentaryProofError(RuntimeError):
    pass


def _stop(ok: bool, code: str) -> None:
    if not ok:
        raise DocumentaryProofError(f"STOP_SIOPE_2025_OFFICIAL_DOCUMENTARY_PROOF_{code}")


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DocumentaryProofError(f"STOP_SIOPE_2025_OFFICIAL_DOCUMENTARY_PROOF_UNREADABLE_{path.name}") from exc
    _stop(isinstance(value, dict), f"OBJECT_{path.name}")
    return value


def _official_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host == "www.fnde.gov.br" or host == "fnde.gov.br" or host == "www.gov.br" or host.endswith(".fnde.gov.br")


def validate(
    assessment_path: Path = ASSESSMENT,
    evidence_path: Path = EVIDENCE,
    regimes_path: Path = REGIMES,
    prior_audit_path: Path = PRIOR_AUDIT,
    live_normalized_path: Path = LIVE_NORMALIZED,
) -> dict:
    assessment = _load(assessment_path)
    evidence = _load(evidence_path)
    regimes = _load(regimes_path)
    prior = _load(prior_audit_path)
    live = _load(live_normalized_path)

    _stop(assessment.get("schema") == "SIOPE_2025_OFFICIAL_DOCUMENTARY_PROOF_V1", "SCHEMA")
    _stop(assessment.get("task") == "TASK_007", "TASK")
    _stop(assessment.get("tier") == "T0_DOCUMENTARY_RESEARCH", "TIER")
    _stop(assessment.get("source_data_get_count") == 0, "SOURCE_DATA_GET")
    _stop(assessment.get("drive_read_count") == 0 and assessment.get("drive_write_count") == 0, "DRIVE")
    _stop(assessment.get("gold_computation_performed") is False, "GOLD_COMPUTATION")
    _stop(assessment.get("persistence") is False and assessment.get("publication") is False, "EFFECTS")

    sources = assessment.get("official_sources", [])
    _stop(len(sources) == 4, "SOURCE_COUNT")
    _stop(all(source.get("authority") == "FNDE" for source in sources), "SOURCE_AUTHORITY")
    _stop(all(str(source.get("source_class", "")).startswith("OFFICIAL_PRIMARY") for source in sources), "SOURCE_CLASS")
    _stop(all(_official_url(source.get("url", "")) for source in sources), "SOURCE_HOST")

    gate_a = assessment.get("gate_a_p6_closure", {})
    _stop(gate_a.get("annual_period_role_status") == "PROVEN_OFFICIAL_REGIME", "GATE_A_ANNUAL_ROLE")
    _stop(gate_a.get("annual_period_role") == "P6_ANNUAL_CONSOLIDATION", "GATE_A_PERIOD")
    _stop(gate_a.get("finality_status") == "NOT_PROVEN", "GATE_A_FINALITY")
    _stop(gate_a.get("annual_closure_status") == "UNKNOWN", "GATE_A_CLOSURE")
    _stop(
        gate_a.get("rectification_status")
        == "PROVEN_POSSIBLE_FOR_SIXTH_BIMESTER_WITH_AUTHORIZATION_IN_CURRENT_DOCUMENTED_REGIME",
        "GATE_A_RECTIFICATION",
    )
    _stop(gate_a.get("closed_series_promotion_authorized") is False, "GATE_A_PROMOTION")
    _stop(len(gate_a.get("missing_proof", [])) == 2, "GATE_A_MISSING")

    gate_b = assessment.get("gate_b_field_semantics", {})
    _stop(gate_b.get("status") == "PARTIAL_NOT_PROVEN", "GATE_B_STATUS")
    _stop(gate_b.get("semantic_comparability_status") == "UNKNOWN", "GATE_B_COMPARABILITY")
    _stop(gate_b.get("current_2025_alias_bridge_status") == "NOT_PROVEN", "GATE_B_ALIAS")
    _stop(gate_b.get("population_denominator_status") == "NOT_PROVEN_OFFICIAL_PRIMARY_DEFINITION", "GATE_B_POPULATION")
    _stop(gate_b.get("gold_promotion_authorized") is False, "GATE_B_PROMOTION")

    field_rows = gate_b.get("field_assessment", [])
    _stop(len(field_rows) == 11, "FIELD_COUNT")
    _stop({row.get("odata_field") for row in field_rows} == REQUIRED_GOLD_FIELDS, "FIELD_SET")
    _stop(sum(bool(row.get("historical_definition_found")) for row in field_rows) == 10, "HISTORICAL_DEFINITION_COVERAGE")
    _stop(all(row.get("2025_alias_identity_proven") is False for row in field_rows), "ALIAS_OVERPROMOTION")
    population = next(row for row in field_rows if row.get("odata_field") == "NUM_POPU")
    _stop(population.get("historical_definition_found") is False, "POPULATION_DEFINITION")

    _stop(evidence.get("evidence_schema") == "TASK_007_SIOPE_2025_OFFICIAL_DOCUMENTARY_EVIDENCE_V1", "EVIDENCE_SCHEMA")
    _stop(evidence.get("source_data_get_count") == 0, "EVIDENCE_SOURCE_GET")
    _stop(evidence.get("financial_values_persisted") is False and evidence.get("response_records_persisted") is False, "EVIDENCE_VALUES")
    documents = evidence.get("documents", [])
    _stop(len(documents) == 4, "EVIDENCE_DOCUMENT_COUNT")
    _stop(all(document.get("authority") == "FNDE" and _official_url(document.get("url", "")) for document in documents), "EVIDENCE_DOCUMENT_AUTHORITY")
    _stop(evidence.get("field_definition_summary", {}).get("historical_financial_concepts_with_official_dictionary_counterparts") == 10, "EVIDENCE_FIELD_COVERAGE")
    _stop(evidence.get("field_definition_summary", {}).get("official_primary_definition_missing_for") == ["NUM_POPU"], "EVIDENCE_POPULATION")
    _stop(evidence.get("field_definition_summary", {}).get("2025_odata_alias_identity_proven_count") == 0, "EVIDENCE_ALIAS")
    _stop(evidence.get("closure_summary", {}).get("period_6_annual_consolidation") == "PROVEN_OFFICIAL_REGIME", "EVIDENCE_ANNUAL_ROLE")
    _stop(evidence.get("closure_summary", {}).get("observed_2025_p6_final_non_rectifiable_state") == "NOT_PROVEN", "EVIDENCE_FINALITY")

    _stop(prior.get("gate_a_annual_closure", {}).get("status") == "NOT_PROVEN", "PRIOR_GATE_A")
    _stop(prior.get("gate_b_semantic_comparability", {}).get("status") == "NOT_PROVEN", "PRIOR_GATE_B")
    _stop(prior.get("resulting_state", {}).get("closed_annual_series_last_year") == 2024, "PRIOR_SERIES")

    _stop(live.get("observed_resource_schema", {}).get("schema_exact") is True, "LIVE_SCHEMA")
    _stop(set(live.get("observed_resource_schema", {}).get("required_gold_input_status", {}).keys()) == REQUIRED_GOLD_FIELDS, "LIVE_FIELD_SET")
    _stop(live.get("semantic_boundary_at_observation", {}).get("any_metric_proven") is False, "LIVE_METRIC_GUARD")

    by_year = {}
    for regime in regimes.get("regimes", []):
        for year in regime.get("years", []):
            by_year[year] = regime
    y2025 = by_year.get(2025, {})
    _stop(regimes.get("closed_annual_series") == {"first_year": 2016, "last_year": 2024}, "CANONICAL_SERIES")
    _stop(y2025.get("status") == "PROVEN_STRUCTURAL_RECENT", "CANONICAL_2025")
    _stop(y2025.get("annual_closure_status") == "UNKNOWN", "CANONICAL_CLOSURE")
    _stop(y2025.get("semantic_comparability_status") == "UNKNOWN", "CANONICAL_COMPARABILITY")
    _stop(y2025.get("closed_series_eligible") is False and y2025.get("gold_metrics_status") == "UNKNOWN", "CANONICAL_GOLD")
    _stop(by_year.get(2026, {}).get("status") == "UNPROVEN_CURRENT_YEAR", "CANONICAL_2026")

    result = assessment.get("resulting_state", {})
    _stop(result.get("p6_documentary_role") == "P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN", "RESULT_P6_ROLE")
    _stop(result.get("annual_closure_status") == "UNKNOWN", "RESULT_CLOSURE")
    _stop(result.get("semantic_comparability_status") == "UNKNOWN", "RESULT_COMPARABILITY")
    _stop(result.get("closed_series_eligible") is False, "RESULT_SERIES_ELIGIBILITY")
    _stop(result.get("closed_annual_series_last_year") == 2024, "RESULT_SERIES")
    _stop(result.get("gold_metrics_status") == "UNKNOWN", "RESULT_GOLD")
    _stop(result.get("year_2026_status") == "UNPROVEN_CURRENT_YEAR", "RESULT_2026")

    for key, value in assessment.get("guards", {}).items():
        _stop(value is False, f"GUARD_{key.upper()}")

    effects = evidence.get("effects", {})
    _stop(effects.get("drive_read_count") == 0 and effects.get("drive_write_count") == 0, "EVIDENCE_DRIVE")
    _stop(effects.get("gold_computation") is False and effects.get("bronze_silver_gold_creation") is False, "EVIDENCE_GOLD")
    _stop(effects.get("publication") is False and effects.get("year_2026_promotion") is False, "EVIDENCE_PROMOTION")

    return {
        "status": PASS,
        "tier": "T0_DOCUMENTARY_RESEARCH",
        "source_data_get_count": 0,
        "p6_documentary_role": "P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN",
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "official_historical_financial_definition_coverage": "10_OF_11",
        "population_denominator_status": "NOT_PROVEN",
        "closed_annual_series_last_year": 2024,
        "gold_metrics_status": "UNKNOWN",
        "year_2026_status": "UNPROVEN_CURRENT_YEAR",
    }


def main() -> int:
    try:
        result = validate()
    except DocumentaryProofError as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
