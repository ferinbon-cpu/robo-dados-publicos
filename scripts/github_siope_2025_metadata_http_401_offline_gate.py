#!/usr/bin/env python3
"""Fail-closed TASK 009C-R assessment gate; performs no network operations."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_metadata_http_401_offline_assessment.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_009C_SIOPE_2025_RESOLVED_PATH_PROBE_RUN_1_HTTP_401_0.8.0.json"


class OfflineAssessmentError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise OfflineAssessmentError(reason)


def validate_assessment(assessment: dict, evidence: dict) -> None:
    _require(assessment.get("tier") == "T0_OFFLINE", "T0_OFFLINE_REQUIRED")
    _require(assessment.get("network_authorized") is False, "NETWORK_MUST_BE_BLOCKED")
    _require(assessment.get("authorization_state") == "CONSUMED_AFTER_ONE_SOURCE_GET", "AUTHORIZATION_MUST_BE_CONSUMED")
    observation = evidence.get("observation", {})
    _require(observation.get("http_status") == 401, "HTTP_401_EVIDENCE_REQUIRED")
    _require(observation.get("source_get_count") == 1, "EXACTLY_ONE_OBSERVED_GET_REQUIRED")
    consumption = evidence.get("authorization_consumption", {})
    _require(consumption.get("consumed") is True, "ONE_SHOT_CONSUMPTION_REQUIRED")
    for key in ("rerun_authorized", "reuse_authorized", "authentication_attempt_authorized"):
        _require(consumption.get(key) is False, f"MUST_BE_FALSE:{key}")
    _require(assessment.get("next_public_package_route") == "UNKNOWN", "NEXT_ROUTE_MUST_REMAIN_UNKNOWN")
    routes = assessment.get("route_assessment")
    _require(isinstance(routes, list) and len(routes) == 4, "EXACT_PINNED_ROUTE_INVENTORY_REQUIRED")
    allowed = {"PUBLIC_ROUTE_CANDIDATE", "REQUIRES_AUTHENTICATION", "UNKNOWN"}
    _require(all(route.get("classification") in allowed for route in routes), "INVALID_ROUTE_CLASSIFICATION")
    expected_routes = {
        "OFFICIAL_FNDE_DOWNLOADS_PAGE": (
            "https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads",
            "PUBLIC_ROUTE_CANDIDATE",
        ),
        "OBSERVED_SHAREPOINT_SHARE_URL": (
            "https://fnde.sharepoint.com/:u:/s/SIOPE/EeP0ArdsxWJLuWyg3LQHt2IBKEWEhLDvDk2_7k1vbAx0tQ?download=1&e=UiD081",
            "PUBLIC_ROUTE_CANDIDATE",
        ),
        "OBSERVED_RELATIVE_REDIRECT": (
            "/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip",
            "UNKNOWN",
        ),
        "RESOLVED_DIRECT_SHAREPOINT_PATH": (
            "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip",
            "REQUIRES_AUTHENTICATION",
        ),
    }
    actual_routes = {
        route.get("route_kind"): (route.get("route"), route.get("classification"))
        for route in routes
    }
    _require(actual_routes == expected_routes, "ROUTE_INVENTORY_OR_CLASSIFICATION_DRIFT")
    direct = [route for route in routes if route.get("route_kind") == "RESOLVED_DIRECT_SHAREPOINT_PATH"]
    _require(len(direct) == 1 and direct[0].get("classification") == "REQUIRES_AUTHENTICATION", "DIRECT_PATH_MUST_REQUIRE_AUTHENTICATION")
    task_009d = assessment.get("task_009d", {})
    _require(task_009d.get("decision") == "KEEP_BLOCKED", "TASK_009D_MUST_STAY_BLOCKED")
    _require(task_009d.get("authorized") is False, "TASK_009D_MUST_NOT_BE_AUTHORIZED")
    _require(task_009d.get("network_requests_authorized_now") == 0, "ZERO_NETWORK_AUTHORIZATION_REQUIRED")
    effects = assessment.get("effects", {})
    _require(effects == {"source_get_count": 0, "drive_read_count": 0, "drive_write_count": 0, "persistence": False, "publication": False}, "OFFLINE_ZERO_EFFECTS_REQUIRED")
    semantics = assessment.get("semantic_guards", {})
    for key in ("annual_closure_status", "semantic_comparability_status", "gold_metrics_status"):
        _require(semantics.get(key) == "UNKNOWN", f"UNKNOWN_REQUIRED:{key}")
    _require(semantics.get("closed_annual_series_first_year") == 2016, "CLOSED_SERIES_START_DRIFT")
    _require(semantics.get("closed_annual_series_last_year") == 2024, "CLOSED_SERIES_END_DRIFT")
    _require(semantics.get("include_2026_authorized") is False, "2026_MUST_STAY_BLOCKED")


def main() -> int:
    try:
        assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        validate_assessment(assessment, evidence)
    except (OSError, json.JSONDecodeError, OfflineAssessmentError) as exc:
        print(str(exc))
        return 13
    print(json.dumps({"status": "PASS_TASK009C_R_HTTP_401_OFFLINE_KEEP_BLOCKED", "source_get_count": 0, "network_authorized": False, "next_public_package_route": "UNKNOWN"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
