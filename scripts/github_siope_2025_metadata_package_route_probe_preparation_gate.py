#!/usr/bin/env python3
"""TASK 009A T0 gate for the bounded official SIOPE 2025 metadata package route probe."""

from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.sources.siope_2025_metadata_package_route_probe import (
    AUTH_PATH,
    validate_preparation_contract,
)

ROOT = Path(__file__).resolve().parents[1]
PREPARATION = ROOT / "config" / "siope_2025_metadata_package_route_probe_preparation.v1.json"
AUTH_TEMPLATE = ROOT / "config" / "siope_2025_metadata_package_route_probe_authorization.template.v1.json"
AUTOMATION_POLICY = ROOT / "config" / "automation_policy.v1.json"
ACTUAL_AUTH = ROOT / AUTH_PATH
PASS = "PASS_SIOPE_2025_METADATA_PACKAGE_ROUTE_PROBE_PREPARATION_T0"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"STOP_TASK009A_OBJECT_REQUIRED_{path.name}")
    return value


def validate() -> dict:
    preparation = _load(PREPARATION)
    template = _load(AUTH_TEMPLATE)
    policy = _load(AUTOMATION_POLICY)
    if ACTUAL_AUTH.exists():
        raise RuntimeError("STOP_TASK009A_ACTUAL_AUTHORIZATION_MUST_BE_ABSENT")
    validate_preparation_contract(preparation, template, policy)
    return {
        "status": PASS,
        "current_tier": "T0_OFFLINE",
        "future_tier": "T1_REMOTE_READONLY",
        "live_execution_authorized": False,
        "source_get_count": 0,
        "maximum_future_probe_get_count": 1,
        "future_probe_range": "bytes=0-4095",
        "follow_redirects": False,
        "allowed_redirect_hosts": [],
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "gold_metrics_status": "UNKNOWN",
        "closed_annual_series_last_year": 2024,
    }


def main() -> int:
    try:
        result = validate()
    except Exception as exc:
        print(str(exc))
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
