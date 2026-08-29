#!/usr/bin/env python3
"""Fail-closed TASK 009C-R assessment gate; performs no network operations."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "config" / "siope_2025_metadata_http_401_offline_assessment.v1.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_009C_SIOPE_2025_RESOLVED_PATH_PROBE_RUN_1_HTTP_401_0.8.0.json"
EXPECTED_HEAD = "0e70495e5ae8ccdf45aff7e2c76fd302d1294b0c"
EXPECTED_AUTH = "SIOPE2025-METADATA-DIRECT-PROBE-20260828-01"
EXPECTED_URL = "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip"


class OfflineAssessmentError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise OfflineAssessmentError(reason)


def validate_assessment(assessment: dict, evidence: dict) -> None:
    _require(assessment.get("schema") == "SIOPE_2025_METADATA_HTTP_401_OFFLINE_ASSESSMENT_V1", "ASSESSMENT_SCHEMA")
    _require(assessment.get("task") == "TASK_009C_R", "ASSESSMENT_TASK")
    _require(assessment.get("tier") == "T0_OFFLINE", "T0_OFFLINE_REQUIRED")
    _require(assessment.get("starting_main_sha") == EXPECTED_HEAD, "STARTING_MAIN_SHA_DRIFT")
    _require(assessment.get("network_authorized") is False, "NETWORK_MUST_BE_BLOCKED")
    _require(assessment.get("authorization_state") == "CONSUMED_AFTER_ONE_SOURCE_GET", "AUTHORIZATION_MUST_BE_CONSUMED")

    _require(evidence.get("evidence_schema") == "TASK_009C_SIOPE_2025_RESOLVED_PATH_PROBE_RUN_1_HTTP_401_V1", "EVIDENCE_SCHEMA")
    _require(evidence.get("task") == "TASK_009C" and evidence.get("review_task") == "TASK_009C_R", "EVIDENCE_TASK_IDENTITY")
    _require(evidence.get("software_version") == "0.8.0", "EVIDENCE_SOFTWARE_VERSION")
    _require(evidence.get("classification") == "SANITIZED_LIVE_EVIDENCE_REVIEWED_OFFLINE", "EVIDENCE_CLASSIFICATION")

    workflow = evidence.get("workflow", {})
    _require(workflow.get("run_id") == 33221146589, "WORKFLOW_RUN_ID")
    _require(workflow.get("workflow_id") == 344981895, "WORKFLOW_ID")
    _require(workflow.get("run_number") == 1, "WORKFLOW_RUN_NUMBER")
    _require(workflow.get("run_attempt") == 1, "WORKFLOW_RUN_ATTEMPT")
    _require(workflow.get("event") == "workflow_dispatch", "WORKFLOW_EVENT")
    _require(workflow.get("head_sha") == EXPECTED_HEAD, "WORKFLOW_HEAD_SHA")
    _require(workflow.get("run_started_at_utc") == "2026-08-28T23:39:27Z", "WORKFLOW_START_TIME")
    _require(workflow.get("authorization_id") == EXPECTED_AUTH, "WORKFLOW_AUTH_ID")

    request = evidence.get("request_contract", {})
    _require(request == {
        "method": "GET",
        "url": EXPECTED_URL,
        "range_header": "bytes=0-4095",
        "maximum_source_get_count": 1,
        "maximum_response_bytes": 4096,
        "timeout_seconds": 60,
        "max_attempts": 1,
        "retry_authorized": False,
        "follow_redirects": False,
    }, "REQUEST_CONTRACT_DRIFT")

    observation = evidence.get("observation", {})
    _require(observation.get("status") == "STOP_METADATA_RESOLVED_PATH_PROBE", "OBSERVATION_STATUS")
    _require(observation.get("reason") == "STOP_SIOPE_2025_METADATA_RESOLVED_PATH_PROBE_HTTP_401", "OBSERVATION_REASON")
    _require(observation.get("http_status") == 401, "HTTP_401_EVIDENCE_REQUIRED")
    _require(observation.get("source_get_count") == 1, "EXACTLY_ONE_OBSERVED_GET_REQUIRED")
    _require(observation.get("runner_exit_code") == 13, "RUNNER_EXIT_CODE")
    _require(observation.get("response_persisted") is False and observation.get("archive_persisted") is False, "OBSERVATION_PERSISTENCE_FORBIDDEN")

    consumption = evidence.get("authorization_consumption", {})
    _require(consumption.get("one_shot") is True and consumption.get("consumed") is True, "ONE_SHOT_CONSUMPTION_REQUIRED")
    _require(consumption.get("reason") == "ONE_SOURCE_GET_WAS_ISSUED", "CONSUMPTION_REASON")
    for key in ("rerun_authorized", "reuse_authorized", "authentication_attempt_authorized"):
        _require(consumption.get(key) is False, f"MUST_BE_FALSE:{key}")
    _require(consumption.get("next_remote_request_requires_new_explicit_owner_authorization") is True, "NEW_OWNER_AUTH_REQUIRED")

    evidence_effects = evidence.get("effects", {})
    _require(evidence_effects == {
        "drive_read_count": 0,
        "drive_write_count": 0,
        "response_persistence": False,
        "archive_persistence": False,
        "publication": False,
    }, "EVIDENCE_EFFECTS_DRIFT")

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
            EXPECTED_URL,
            "REQUIRES_AUTHENTICATION",
        ),
    }
    actual_routes = {
        route.get("route_kind"): (route.get("route"), route.get("classification"))
        for route in routes
    }
    _require(actual_routes == expected_routes, "ROUTE_INVENTORY_OR_CLASSIFICATION_DRIFT")
    direct = [route for route in routes if route.get("route_kind") == "RESOLVED_DIRECT_SHAREPOINT_PATH"]
    _require(len(direct) == 1 and direct[0].get("package_access_status") == "HTTP_401_OBSERVED", "DIRECT_PATH_401_STATUS_REQUIRED")

    task_009d = assessment.get("task_009d", {})
    _require(task_009d.get("decision") == "KEEP_BLOCKED", "TASK_009D_MUST_STAY_BLOCKED")
    _require(task_009d.get("authorized") is False, "TASK_009D_MUST_NOT_BE_AUTHORIZED")
    _require(task_009d.get("network_requests_authorized_now") == 0, "ZERO_NETWORK_AUTHORIZATION_REQUIRED")

    effects = assessment.get("effects", {})
    _require(effects == {"source_get_count": 0, "drive_read_count": 0, "drive_write_count": 0, "persistence": False, "publication": False}, "OFFLINE_ZERO_EFFECTS_REQUIRED")

    for semantics in (assessment.get("semantic_guards", {}), evidence.get("semantic_guards", {})):
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
