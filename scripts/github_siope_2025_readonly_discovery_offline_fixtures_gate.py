#!/usr/bin/env python3
"""Run the pinned, sanitized SIOPE 2025 discovery fixtures offline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_2025_readonly_discovery_offline import (  # noqa: E402
    Siope2025OfflineFixtureError,
    validate_fixture,
)
FIXTURES = ROOT / "tests" / "fixtures" / "siope_2025_readonly_discovery"
DESIGN = ROOT / "config" / "siope_2025_readonly_discovery_design.v1.json"
PASS = "PASS_SIOPE_2025_READONLY_DISCOVERY_OFFLINE_FIXTURES_T0"


def validate_all(fixtures_dir: Path = FIXTURES) -> dict:
    paths = sorted(fixtures_dir.glob("*.json"))
    if [path.name for path in paths] != [
        "duplicate_p6_stop.json",
        "identity_mismatch_stop.json",
        "nextlink_stop.json",
        "no_periods.json",
        "p6_exact_schema.json",
        "p6_extra_schema_stop.json",
        "p6_schema_drift_stop.json",
        "periods_without_p6.json",
        "request_budget_stop.json",
        "transport_drift_stop.json",
    ]:
        raise Siope2025OfflineFixtureError("STOP_SIOPE_2025_OFFLINE_FIXTURE_SET")
    passed = 0
    stopped = 0
    outcomes = []
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    expected_fields = design.get("offline_validation", {}).get("expected_schema_fields")
    if not isinstance(expected_fields, list) or len(expected_fields) != 52:
        raise Siope2025OfflineFixtureError("STOP_SIOPE_2025_OFFLINE_FIXTURE_DESIGN_SCHEMA")
    for path in paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        expected_stop = fixture.get("expected_stop_code")
        try:
            result = validate_fixture(fixture, expected_schema_fields=expected_fields)
        except Siope2025OfflineFixtureError as exc:
            if not expected_stop or str(exc) != expected_stop:
                raise
            stopped += 1
        else:
            if expected_stop:
                raise Siope2025OfflineFixtureError("STOP_SIOPE_2025_OFFLINE_FIXTURE_EXPECTED_STOP_DID_NOT_STOP")
            passed += 1
            outcomes.append(result["outcome"])
    return {
        "status": PASS,
        "fixture_count": len(paths),
        "pass_case_count": passed,
        "expected_stop_case_count": stopped,
        "outcomes": sorted(outcomes),
        "network_called": False,
        "drive_called": False,
        "runtime_execution_authorized": False,
    }


def main() -> int:
    try:
        result = validate_all()
    except (OSError, ValueError, Siope2025OfflineFixtureError) as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
