#!/usr/bin/env python3
"""T0/offline, fail-closed validation for SIOPE historical regime discovery."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "config" / "siope_historical_regimes.v1.json"
MATRIX = ROOT / "config" / "siope_historical_evidence_matrix.v1.json"
POLICY = ROOT / "config" / "automation_policy.v1.json"
PASS = "PASS_SIOPE_HISTORICAL_REGIME_DISCOVERY_T0"


class RegimeDiscoveryError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise RegimeDiscoveryError(f"STOP_SIOPE_REGIME_DISCOVERY_{code}")


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RegimeDiscoveryError(f"STOP_SIOPE_REGIME_DISCOVERY_UNREADABLE_{path.name}") from exc
    _stop(isinstance(value, dict), f"OBJECT_{path.name}")
    return value


def validate(map_path: Path = MAP, matrix_path: Path = MATRIX, policy_path: Path = POLICY) -> dict:
    regime_map, matrix, policy = _load(map_path), _load(matrix_path), _load(policy_path)
    _stop(regime_map.get("schema") == "SIOPE_HISTORICAL_REGIME_MAP_V1", "MAP_SCHEMA")
    _stop(regime_map.get("tier") == "T0_OFFLINE", "TIER")
    _stop(regime_map.get("future_batch_execution_authorized") is False, "FUTURE_BATCH")
    _stop(regime_map.get("live_discovery_authorized") is False, "LIVE_DISCOVERY")
    _stop(policy.get("policy_invariants", {}).get("future_batch_execution_authorized") is False, "POLICY_FUTURE_BATCH")
    _stop(regime_map.get("closed_annual_series") == {"first_year": 2016, "last_year": 2024}, "CLOSED_SERIES")
    _stop(len(regime_map.get("gold_metric_ids", [])) == 8, "GOLD_METRICS")

    regimes = regime_map.get("regimes")
    _stop(isinstance(regimes, list) and len(regimes) == 7, "REGIMES")
    by_year: dict[int, dict] = {}
    for regime in regimes:
        for required in ("years", "period", "status", "evidence_classes", "evidence_refs", "resource_family", "schema", "required_fields", "allowed_aliases", "potential_gold_metrics", "non_comparable_metrics", "cautions", "release_notes", "promotion_requires"):
            _stop(required in regime, f"REGIME_FIELD_{required.upper()}")
        for year in regime["years"]:
            _stop(isinstance(year, int) and year not in by_year, f"YEAR_DUPLICATE_{year}")
            by_year[year] = regime
    _stop(set(by_year) == set(range(2000, 2027)), "YEAR_COVERAGE")

    _stop(by_year[2016]["status"] == "PROVEN" and by_year[2016]["period"] == {"value": 1, "status": "PROVEN"}, "2016_P1")
    _stop(by_year[2017]["status"] == "PROVEN" and by_year[2017]["period"] == {"value": 6, "status": "PROVEN"}, "2017_P6")
    for year in range(2008, 2016):
        item = by_year[year]
        _stop(item["status"] == "OFFICIAL_DOCUMENTED_CANDIDATE_RUNTIME", f"PRE2016_STATUS_{year}")
        _stop(item["period"] == {"value": 1, "status": "DOCUMENTED"}, f"PRE2016_P1_{year}")
        _stop(item["schema"]["status"] == "UNKNOWN", f"PRE2016_SCHEMA_{year}")
    for year in range(2005, 2008):
        _stop(by_year[year]["status"] == "LEGACY_DOCUMENTED_CANDIDATE", f"LEGACY_PROMOTION_{year}")
    for year in range(2000, 2005):
        _stop(by_year[year]["status"] == "CANDIDATE_EXTERNAL_ONLY", f"EXTERNAL_PROMOTION_{year}")
    _stop(by_year[2025]["status"] == "UNPROVEN_RECENT" and by_year[2025]["schema"]["status"] == "UNKNOWN", "2025_PROMOTION")
    _stop(by_year[2026]["status"] == "UNPROVEN_CURRENT_YEAR", "2026_PROMOTION")
    _stop(by_year[2026]["period"] == {"value": None, "status": "UNKNOWN"}, "2026_PERIOD")
    _stop(2026 > regime_map["closed_annual_series"]["last_year"], "2026_CLOSED_SERIES")

    _stop(matrix.get("schema") == "SIOPE_HISTORICAL_EVIDENCE_MATRIX_V1", "MATRIX_SCHEMA")
    _stop(matrix.get("regime_map") == "config/siope_historical_regimes.v1.json", "MATRIX_MAP")
    _stop(matrix.get("future_batch_execution_authorized") is False, "MATRIX_FUTURE_BATCH")
    rows = matrix.get("rows")
    _stop(isinstance(rows, list) and [row.get("years") for row in rows] == ["2000-2004", "2005-2007", "2008-2015", "2016", "2017-2024", "2025", "2026"], "MATRIX_ROWS")
    for row in rows:
        for field in ("official_document", "evidence_class", "surface", "annual_period", "current_fields", "gold_if_fields_exist", "semantic_break_risk", "adapter_or_corrections"):
            _stop(field in row, f"MATRIX_FIELD_{field.upper()}")
    _stop(rows[2]["surface"].endswith("NOT_PROVEN"), "MATRIX_2008_RESOURCE_SEPARATION")
    _stop(rows[5]["current_fields"] == "UNKNOWN" and rows[6]["annual_period"] == "NOT_CLOSED_UNKNOWN", "MATRIX_FRONTIER")
    return {"status": PASS, "tier": "T0_OFFLINE", "year_count": len(by_year), "network_called": False, "secrets_used": False, "future_batch_execution_authorized": False}


def main() -> int:
    try:
        result = validate()
    except RegimeDiscoveryError as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
