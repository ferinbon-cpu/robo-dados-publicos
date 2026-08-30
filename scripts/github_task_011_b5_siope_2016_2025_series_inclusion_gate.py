#!/usr/bin/env python3
"""Validate the closed historical series and stop before any 2025 append."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.product.siope_historical import EXPECTED_METRIC_IDS, GOLD_CONTRACT, SOURCE_ID

CONFIG = ROOT / "config/siope_2016_2025_series_inclusion_prerequisites.v1.json"
HISTORICAL = ROOT / "config/siope_historical_regimes.v1.json"
DECISION = "STOP_2025_SERIES_INCLUSION_GOLD_NOT_ELIGIBLE"
READY = "READY_2025_SERIES_INCLUSION_REQUIRES_SEPARATE_EXECUTION"
YEARS = list(range(2016, 2025))
PERIODS = {str(year): 1 if year == 2016 else 6 for year in YEARS}
CANDIDATE_CONTRACT = {
    "identity": {"year": 2025, "period": 6, "period_label": "Annual", "uf": "SP", "municipality": "Limeira", "municipality_code": 352690},
    "gold_evidence": {
        "gold_contract": GOLD_CONTRACT,
        "source_id": SOURCE_ID,
        "metric_ids": list(EXPECTED_METRIC_IDS),
        "required_hashes": ["record_sha256", "silver_payload_sha256", "gold_payload_sha256"],
        "hash_format": "LOWERCASE_OR_UPPERCASE_64_HEX_SHA256",
        "provenance_status": "VALIDATED",
        "arithmetic_validation_status": "PROVEN",
    },
    "required_prerequisites": ["B4_GOLD_2025", "GOLD_2025_DETERMINISTIC_EVIDENCE", "SEMANTIC_COMPARABILITY", "REGRESSION_QA", "EXPLICIT_SERIES_INCLUSION_DECISION"],
    "financial_values_allowed_in_prerequisite_contract": False,
}
SHA256_RE = re.compile(r"[0-9a-fA-F]{64}\Z")


def _validate_candidate(candidate):
    if not isinstance(candidate, dict) or candidate.get("identity") != CANDIDATE_CONTRACT["identity"]:
        raise ValueError("future 2025 candidate identity invalid")
    evidence = candidate.get("gold_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("future 2025 candidate Gold evidence descriptor missing")
    if evidence.get("gold_contract") != GOLD_CONTRACT:
        raise ValueError("future 2025 candidate canonical Gold contract invalid")
    if evidence.get("source_id") != SOURCE_ID:
        raise ValueError("future 2025 candidate canonical source id invalid")
    metric_ids = evidence.get("metric_ids")
    if not isinstance(metric_ids, list) or tuple(metric_ids) != EXPECTED_METRIC_IDS:
        raise ValueError("future 2025 candidate canonical metric ids invalid")
    for field in ("record_sha256", "silver_payload_sha256", "gold_payload_sha256"):
        if not isinstance(evidence.get(field), str) or SHA256_RE.fullmatch(evidence[field]) is None:
            raise ValueError(f"future 2025 candidate {field} invalid")
    if evidence.get("provenance_status") != "VALIDATED" or evidence.get("arithmetic_validation_status") != "PROVEN":
        raise ValueError("future 2025 candidate provenance or arithmetic validation status invalid")
    if set(evidence) != {"gold_contract", "source_id", "metric_ids", "record_sha256", "silver_payload_sha256", "gold_payload_sha256", "provenance_status", "arithmetic_validation_status"}:
        raise ValueError("future 2025 candidate Gold evidence fields invalid")


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
    if data.get("required_state") != required or data.get("candidate_2025_contract") != CANDIDATE_CONTRACT:
        raise ValueError("B5 prerequisite boundary drift")
    candidate = data.get("candidate_2025")
    if candidate is not None:
        _validate_candidate(candidate)
    if data.get("closed_annual_series") != "2016-2024" or data.get("release_0_8_0") != "CANDIDATE" or data.get("automatic_append") is not False:
        raise ValueError("automatic append, series, 2026, or release promotion")
    if data.get("effects") != {"writes": 0, "series_rows_appended": 0, "release_promotion": False}:
        raise ValueError("forbidden B5 effect")
    unmet = [key for key, value in required.items() if data.get("prerequisites", {}).get(key) != value]
    ready = candidate is not None and not unmet
    return {"decision": READY if ready else DECISION, "unmet": unmet, "candidate_present": candidate is not None, "writes": 0, "series_rows_appended": 0, "release_promotion": False}


def main():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    print(json.dumps(validate(data, historical), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
