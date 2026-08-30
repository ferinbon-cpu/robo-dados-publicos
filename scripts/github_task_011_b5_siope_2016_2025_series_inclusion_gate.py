#!/usr/bin/env python3
"""Validate the closed historical series and stop before any 2025 append."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/siope_2016_2025_series_inclusion_prerequisites.v1.json"
HISTORICAL = ROOT / "config/siope_historical_regimes.v1.json"
DECISION = "STOP_2025_SERIES_INCLUSION_GOLD_NOT_ELIGIBLE"
YEARS = list(range(2016, 2025))
PERIODS = {str(year): 1 if year == 2016 else 6 for year in YEARS}


def validate(data, historical=None):
    if (data.get("schema"), data.get("tier"), data.get("decision")) != ("SIOPE_2016_2025_SERIES_INCLUSION_PREREQUISITES_V1", "T0_OFFLINE", DECISION):
        raise ValueError("B5 identity or decision drift")
    contract = data.get("historical_contract", {})
    if contract != {"years": YEARS, "periods": PERIODS, "source": "config/siope_historical_regimes.v1.json"} or len(set(contract.get("years", []))) != len(YEARS):
        raise ValueError("historical year, order, duplicate, or period drift")
    if historical is not None:
        if historical.get("closed_annual_series") != {"first_year": 2016, "last_year": 2024}:
            raise ValueError("canonical historical boundary drift")
        regimes = {r["id"]: r for r in historical.get("regimes", [])}
        if regimes.get("PROVEN_ANNUAL_2016", {}).get("period", {}).get("value") != 1 or regimes.get("PROVEN_BIMONTHLY_2017_2024", {}).get("period", {}).get("value") != 6:
            raise ValueError("canonical historical regime drift")
    required = {"B4_GOLD_2025": "PROVEN_AUTHORIZED_COMPUTED", "GOLD_2025_DETERMINISTIC_EVIDENCE": "VALIDATED_PROVENANCE_AND_ARITHMETIC", "SEMANTIC_COMPARABILITY": "PROVEN", "REGRESSION_QA": "PROVEN", "EXPLICIT_SERIES_INCLUSION_DECISION": "AUTHORIZED"}
    if data.get("required_state") != required or data.get("prerequisites", {}).get("B4_GOLD_2025") == required["B4_GOLD_2025"]:
        raise ValueError("B5 prerequisite boundary drift")
    if data.get("candidate_2025") is not None or data.get("closed_annual_series") != "2016-2024" or data.get("release_0_8_0") != "CANDIDATE" or data.get("automatic_append") is not False:
        raise ValueError("automatic append, series, 2026, or release promotion")
    if data.get("effects") != {"writes": 0, "series_rows_appended": 0, "release_promotion": False}:
        raise ValueError("forbidden B5 effect")
    return DECISION


def main():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    print(validate(data, historical))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
