#!/usr/bin/env python3
"""TASK 008 fail-closed gate for SIOPE 2025 alias metadata and finality evidence."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_alias_finality_audit.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_008_SIOPE_2025_ALIAS_FINALITY_EVIDENCE_0.8.0.json"
TASK007 = ROOT / "config" / "siope_2025_official_documentary_proof.v1.json"
REGIMES = ROOT / "config" / "siope_historical_regimes.v1.json"
PASS = "PASS_SIOPE_2025_ALIAS_FINALITY_AUDIT_T0_KEEP_UNKNOWN"

REQUIRED_ALIASES = {
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


class AliasFinalityAuditError(RuntimeError):
    pass


def _stop(ok: bool, code: str) -> None:
    if not ok:
        raise AliasFinalityAuditError(f"STOP_SIOPE_2025_ALIAS_FINALITY_AUDIT_{code}")


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AliasFinalityAuditError(f"STOP_SIOPE_2025_ALIAS_FINALITY_AUDIT_UNREADABLE_{path.name}") from exc
    _stop(isinstance(value, dict), f"OBJECT_{path.name}")
    return value


def _official_url(url: str) -> bool:
    host = (urlparse(str(url)).hostname or "").lower()
    return host in {"www.gov.br", "gov.br", "www.fnde.gov.br", "fnde.gov.br"} or host.endswith(".fnde.gov.br")


def validate(
    assessment_path: Path = ASSESSMENT,
    evidence_path: Path = EVIDENCE,
    task007_path: Path = TASK007,
    regimes_path: Path = REGIMES,
) -> dict:
    assessment = _load(assessment_path)
    evidence = _load(evidence_path)
    task007 = _load(task007_path)
    regimes = _load(regimes_path)

    _stop(assessment.get("schema") == "SIOPE_2025_ALIAS_FINALITY_AUDIT_V1", "SCHEMA")
    _stop(assessment.get("task") == "TASK_008", "TASK")
    _stop(assessment.get("tier") == "T0_DOCUMENTARY_RESEARCH", "TIER")
    _stop(assessment.get("source_data_get_count") == 0, "SOURCE_DATA_GET")
    _stop(assessment.get("drive_read_count") == 0 and assessment.get("drive_write_count") == 0, "DRIVE")
    _stop(assessment.get("gold_computation_performed") is False, "GOLD_COMPUTATION")
    _stop(assessment.get("persistence") is False and assessment.get("publication") is False, "EFFECTS")

    sources = assessment.get("official_sources", [])
    _stop(len(sources) == 3, "SOURCE_COUNT")
    _stop(all(source.get("authority") == "FNDE" for source in sources), "SOURCE_AUTHORITY")
    _stop(all(str(source.get("source_class", "")).startswith("OFFICIAL_PRIMARY") for source in sources), "SOURCE_CLASS")
    _stop(all(_official_url(source.get("url", "")) for source in sources), "SOURCE_HOST")

    gate_a = assessment.get("gate_a_alias_metadata", {})
    _stop(gate_a.get("official_2025_municipal_metadata_package_status") == "PROVEN_PUBLISHED_BY_FNDE", "GATE_A_PACKAGE_EXISTS")
    _stop(gate_a.get("package_content_inspection_status") == "NOT_INSPECTED_CURRENT_CONNECTOR_BINARY_UNAVAILABLE", "GATE_A_PACKAGE_CONTENT")
    _stop(gate_a.get("current_2025_alias_bridge_status") == "NOT_PROVEN", "GATE_A_ALIAS")
    _stop(gate_a.get("population_denominator_status") == "NOT_PROVEN_OFFICIAL_PRIMARY_DEFINITION_AND_VINTAGE", "GATE_A_POPULATION")
    _stop(gate_a.get("semantic_comparability_status") == "UNKNOWN", "GATE_A_COMPARABILITY")
    _stop(set(gate_a.get("required_aliases", [])) == REQUIRED_ALIASES, "GATE_A_ALIAS_SET")
    _stop(gate_a.get("field_level_identity_proven_count") == 0, "GATE_A_IDENTITY_COUNT")
    _stop(gate_a.get("field_level_identity_required_count") == 11, "GATE_A_REQUIRED_COUNT")
    _stop(gate_a.get("gold_promotion_authorized") is False, "GATE_A_GOLD")

    gate_b = assessment.get("gate_b_finality_state", {})
    _stop(gate_b.get("p6_documentary_role") == "P6_ANNUAL_CONSOLIDATION_PROVEN_FINALITY_UNKNOWN", "GATE_B_P6_ROLE")
    _stop(gate_b.get("mavs_processing_publication_status") == "PROVEN_REQUIRES_CONFIRMATIONS", "GATE_B_MAVS")
    _stop(gate_b.get("sixth_bimester_rectification_path") == "PROVEN_REQUIRES_TECHNICAL_AUTHORIZATION", "GATE_B_RECTIFICATION")
    _stop(gate_b.get("observed_2025_p6_finality_state") == "NOT_PROVEN", "GATE_B_FINALITY")
    _stop(gate_b.get("annual_closure_status") == "UNKNOWN", "GATE_B_CLOSURE")
    _stop(gate_b.get("processed_or_published_equivalent_to_non_rectifiable_final") is False, "GATE_B_FINAL_EQUIVALENCE")
    _stop(gate_b.get("closed_series_promotion_authorized") is False, "GATE_B_PROMOTION")

    _stop(evidence.get("evidence_schema") == "TASK_008_SIOPE_2025_ALIAS_FINALITY_EVIDENCE_V1", "EVIDENCE_SCHEMA")
    _stop(evidence.get("source_data_get_count") == 0, "EVIDENCE_SOURCE_GET")
    _stop(evidence.get("operational_receipt_status_query_count") == 0, "EVIDENCE_RECEIPT_QUERY")
    _stop(evidence.get("financial_values_persisted") is False and evidence.get("response_records_persisted") is False, "EVIDENCE_VALUES")
    _stop(len(evidence.get("documents", [])) == 3, "EVIDENCE_DOCUMENT_COUNT")
    _stop(all(document.get("authority") == "FNDE" and _official_url(document.get("url", "")) for document in evidence.get("documents", [])), "EVIDENCE_AUTHORITY")

    alias_summary = evidence.get("alias_metadata_summary", {})
    _stop(alias_summary.get("official_2025_metadata_package_exists") is True, "EVIDENCE_PACKAGE_EXISTS")
    _stop(alias_summary.get("official_2025_metadata_package_content_inspected") is False, "EVIDENCE_PACKAGE_CONTENT")
    _stop(alias_summary.get("required_alias_count") == 11, "EVIDENCE_ALIAS_REQUIRED")
    _stop(alias_summary.get("alias_identity_proven_count") == 0, "EVIDENCE_ALIAS_PROVEN")
    _stop(alias_summary.get("num_popu_definition_proven") is False, "EVIDENCE_POPULATION")
    _stop(alias_summary.get("num_popu_source_vintage_rule_proven") is False, "EVIDENCE_POPULATION_VINTAGE")
    _stop(alias_summary.get("semantic_comparability_status") == "UNKNOWN", "EVIDENCE_COMPARABILITY")

    finality_summary = evidence.get("finality_summary", {})
    _stop(finality_summary.get("p6_annual_consolidation_role") == "PROVEN_INHERITED_TASK_007", "EVIDENCE_P6_ROLE")
    _stop(finality_summary.get("mavs_validation_before_processing_publication") == "PROVEN_OFFICIAL_CURRENT_DOCUMENTATION", "EVIDENCE_MAVS")
    _stop(finality_summary.get("sixth_bimester_rectification_path") == "PROVEN_OFFICIAL_CURRENT_REGIME", "EVIDENCE_RECTIFICATION")
    _stop(finality_summary.get("processed_or_published_means_non_rectifiable_final") == "NOT_PROVEN", "EVIDENCE_FINAL_EQUIVALENCE")
    _stop(finality_summary.get("observed_2025_limeira_finality_state") == "NOT_QUERIED_IN_T0", "EVIDENCE_LIMEIRA_STATE")
    _stop(finality_summary.get("annual_closure_status") == "UNKNOWN", "EVIDENCE_CLOSURE")

    _stop(task007.get("resulting_state", {}).get("closed_annual_series_last_year") == 2024, "TASK007_SERIES")
    _stop(task007.get("resulting_state", {}).get("annual_closure_status") == "UNKNOWN", "TASK007_CLOSURE")
    _stop(task007.get("resulting_state", {}).get("semantic_comparability_status") == "UNKNOWN", "TASK007_COMPARABILITY")
    _stop(task007.get("resulting_state", {}).get("gold_metrics_status") == "UNKNOWN", "TASK007_GOLD")

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
    _stop(result.get("annual_closure_status") == "UNKNOWN", "RESULT_CLOSURE")
    _stop(result.get("semantic_comparability_status") == "UNKNOWN", "RESULT_COMPARABILITY")
    _stop(result.get("closed_series_eligible") is False, "RESULT_SERIES_ELIGIBILITY")
    _stop(result.get("closed_annual_series_last_year") == 2024, "RESULT_SERIES")
    _stop(result.get("gold_metrics_status") == "UNKNOWN", "RESULT_GOLD")
    _stop(result.get("year_2026_status") == "UNPROVEN_CURRENT_YEAR", "RESULT_2026")
    _stop(assessment.get("decision") == "KEEP_UNKNOWN", "DECISION")

    for key, value in assessment.get("guards", {}).items():
        _stop(value is False, f"GUARD_{key.upper()}")

    effects = evidence.get("effects", {})
    _stop(effects.get("drive_read_count") == 0 and effects.get("drive_write_count") == 0, "EVIDENCE_DRIVE")
    _stop(effects.get("gold_computation") is False and effects.get("bronze_silver_gold_creation") is False, "EVIDENCE_GOLD")
    _stop(effects.get("persistence") is False and effects.get("publication") is False, "EVIDENCE_EFFECTS")
    _stop(effects.get("closed_series_expansion") is False and effects.get("year_2026_promotion") is False, "EVIDENCE_PROMOTION")

    return {
        "status": PASS,
        "tier": "T0_DOCUMENTARY_RESEARCH",
        "decision": "KEEP_UNKNOWN",
        "source_data_get_count": 0,
        "operational_receipt_status_query_count": 0,
        "alias_identity_proven_count": 0,
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "closed_annual_series_last_year": 2024,
        "gold_metrics_status": "UNKNOWN",
        "year_2026_status": "UNPROVEN_CURRENT_YEAR",
    }


def main() -> int:
    try:
        result = validate()
    except AliasFinalityAuditError as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
