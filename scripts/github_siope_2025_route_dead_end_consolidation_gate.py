#!/usr/bin/env python3
"""Fail-closed TASK 009D route dead-end consolidation gate; no network operations."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT_PATH = ROOT / "config" / "siope_2025_route_dead_end_consolidation.v1.json"
ANTONIETA_PATH = ROOT / "config" / "source_expansion.siope_artifact_access_boundary.json"
TASK008_PATH = ROOT / "config" / "siope_2025_alias_finality_audit.v1.json"
TASK009B_PATH = ROOT / "docs" / "evidence" / "TASK_009B_SIOPE_2025_METADATA_ROUTE_PROBE_RUN_2_REDIRECT_0.8.0.json"
TASK009C_PATH = ROOT / "docs" / "evidence" / "TASK_009C_SIOPE_2025_RESOLVED_PATH_PROBE_RUN_1_HTTP_401_0.8.0.json"


class RouteDeadEndConsolidationError(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise RouteDeadEndConsolidationError(reason)


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"OBJECT_REQUIRED:{path.name}")
    return value


def validate_consolidation(
    assessment: dict,
    antonieta: dict,
    task008: dict,
    task009b: dict,
    task009c: dict,
) -> None:
    _require(assessment.get("schema") == "SIOPE_2025_ROUTE_DEAD_END_CONSOLIDATION_V1", "ASSESSMENT_SCHEMA")
    _require(assessment.get("task") == "TASK_009D", "TASK_ID")
    _require(assessment.get("issue") == 219, "ISSUE_ID")
    _require(assessment.get("tier") == "T0_OFFLINE", "T0_OFFLINE_REQUIRED")
    _require(assessment.get("starting_main_sha") == "e22aa63cba54c01296cc70efa728c1a44778051e", "STARTING_MAIN_SHA")
    _require(assessment.get("network_authorized") is False, "NETWORK_MUST_BE_BLOCKED")
    _require(assessment.get("source_get_count") == 0, "ASSESSMENT_SOURCE_GET_ZERO")
    _require(assessment.get("drive_read_count") == 0, "DRIVE_READ_ZERO")
    _require(assessment.get("drive_write_count") == 0, "DRIVE_WRITE_ZERO")
    _require(assessment.get("persistence") is False, "PERSISTENCE_FALSE")
    _require(assessment.get("publication") is False, "PUBLICATION_FALSE")
    _require(assessment.get("workflow_live_added") is False, "NO_LIVE_WORKFLOW")

    _require(antonieta.get("product_page_status") == "PUBLIC_VERIFIED", "ANTONIETA_PRODUCT_PAGE")
    _require(antonieta.get("artifact_metadata_status") == "PUBLIC_VERIFIED", "ANTONIETA_METADATA")
    _require(antonieta.get("anonymous_export_status") == "AUTHENTICATION_BOUNDARY_OBSERVED", "ANTONIETA_AUTH_BOUNDARY")
    _require(antonieta.get("acquisition_route_status") == "UNPROVEN_BEYOND_AUTHENTICATION_BOUNDARY", "ANTONIETA_ROUTE_UNPROVEN")
    _require(antonieta.get("artifact_access_status") == "NOT_PROVEN_PUBLIC_ANONYMOUS", "ANTONIETA_PUBLIC_ACCESS_UNPROVEN")
    auth_boundary = antonieta.get("authentication_boundary", {})
    _require(auth_boundary.get("provider_label") == "gov.br", "ANTONIETA_PROVIDER")
    _require(auth_boundary.get("authenticated_browser_automation") == "PROHIBITED", "ANTONIETA_AUTH_AUTOMATION_PROHIBITED")
    _require(auth_boundary.get("credential_capture") == "PROHIBITED", "ANTONIETA_CREDENTIAL_CAPTURE_PROHIBITED")
    _require(auth_boundary.get("session_cookie_capture") == "PROHIBITED", "ANTONIETA_COOKIE_CAPTURE_PROHIBITED")

    alias_gate = task008.get("gate_a_alias_metadata", {})
    _require(alias_gate.get("official_2025_municipal_metadata_package_status") == "PROVEN_PUBLISHED_BY_FNDE", "TASK008_PACKAGE_PUBLICATION")
    _require(alias_gate.get("package_content_inspection_status") == "NOT_INSPECTED_CURRENT_CONNECTOR_BINARY_UNAVAILABLE", "TASK008_PACKAGE_NOT_INSPECTED")
    _require(alias_gate.get("current_2025_alias_bridge_status") == "NOT_PROVEN", "TASK008_ALIAS_BRIDGE")
    _require(alias_gate.get("population_denominator_status") == "NOT_PROVEN_OFFICIAL_PRIMARY_DEFINITION_AND_VINTAGE", "TASK008_NUM_POPU")
    _require(alias_gate.get("field_level_identity_proven_count") == 0, "TASK008_FIELD_IDENTITY_ZERO")
    _require(alias_gate.get("field_level_identity_required_count") == 11, "TASK008_FIELD_IDENTITY_REQUIRED_11")
    _require(alias_gate.get("gold_promotion_authorized") is False, "TASK008_GOLD_BLOCKED")

    b_workflow = task009b.get("workflow", {})
    _require(b_workflow.get("run_id") == 33217097796, "TASK009B_RUN_ID")
    b_obs = task009b.get("observation", {})
    _require(b_obs.get("http_status") == 302, "TASK009B_HTTP_302")
    _require(b_obs.get("source_get_count") == 1, "TASK009B_ONE_GET")
    _require(b_obs.get("redirect_path_observed") == "/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip", "TASK009B_REDIRECT_PATH")
    b_resolution = task009b.get("offline_route_resolution", {})
    _require(b_resolution.get("resolved_target_url") == "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip", "TASK009B_RESOLVED_TARGET")
    _require(task009b.get("authorization_consumption", {}).get("consumed") is True, "TASK009B_AUTH_CONSUMED")

    c_workflow = task009c.get("workflow", {})
    _require(c_workflow.get("run_id") == 33221146589, "TASK009C_RUN_ID")
    _require(c_workflow.get("workflow_id") == 344981895, "TASK009C_WORKFLOW_ID")
    _require(c_workflow.get("run_number") == 1 and c_workflow.get("run_attempt") == 1, "TASK009C_RUN_IDENTITY")
    _require(c_workflow.get("event") == "workflow_dispatch", "TASK009C_EVENT")
    c_obs = task009c.get("observation", {})
    _require(c_obs.get("http_status") == 401, "TASK009C_HTTP_401")
    _require(c_obs.get("source_get_count") == 1, "TASK009C_ONE_GET")
    _require(c_obs.get("reason") == "STOP_SIOPE_2025_METADATA_RESOLVED_PATH_PROBE_HTTP_401", "TASK009C_STOP_REASON")
    _require(c_obs.get("response_persisted") is False and c_obs.get("archive_persisted") is False, "TASK009C_NO_SOURCE_PERSISTENCE")
    c_auth = task009c.get("authorization_consumption", {})
    _require(c_auth.get("consumed") is True, "TASK009C_AUTH_CONSUMED")
    for key in ("rerun_authorized", "reuse_authorized", "authentication_attempt_authorized"):
        _require(c_auth.get(key) is False, f"TASK009C_MUST_BE_FALSE:{key}")

    routes = assessment.get("route_inventory")
    _require(isinstance(routes, list) and len(routes) == 3, "EXACT_ROUTE_INVENTORY_REQUIRED")
    expected_routes = {
        "ANTONIETA_ARTIFACT_METADATA": (
            "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/products/data-products/20/artifact-metadata",
            "PUBLIC_METADATA_VERIFIED_AUTH_BOUNDARY_BEFORE_ARTIFACT_ROUTE",
        ),
        "FNDE_2025_METADATA_SHARE_URL": (
            "https://fnde.sharepoint.com/:u:/s/SIOPE/EeP0ArdsxWJLuWyg3LQHt2IBKEWEhLDvDk2_7k1vbAx0tQ?download=1&e=UiD081",
            "OBSERVED_HTTP_302_RELATIVE_REDIRECT_ONLY",
        ),
        "FNDE_2025_METADATA_RESOLVED_SHAREPOINT_PATH": (
            "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip",
            "OBSERVED_HTTP_401_NOT_PUBLIC_ANONYMOUSLY_PROVEN",
        ),
    }
    actual_routes = {route.get("id"): (route.get("route"), route.get("status")) for route in routes}
    _require(actual_routes == expected_routes, "ROUTE_INVENTORY_DRIFT")
    _require(all(route.get("artifact_route_proven") is False for route in routes), "ARTIFACT_ROUTE_MUST_REMAIN_UNPROVEN")
    _require(all(route.get("repeat_probe_authorized") is False for route in routes), "REPEAT_PROBE_MUST_BE_BLOCKED")

    expected_future_classes = [
        "OFFICIAL_FNDE_EXPLICIT_PUBLIC_UNAUTHENTICATED_URL_FOR_METADADOS_MUN_2025",
        "OFFICIAL_REPO_RESIDENT_2025_METADATA_OR_LAYOUT_WITH_VERIFIABLE_PROVENANCE",
        "OFFICIAL_PRIMARY_2025_DICTIONARY_FOR_ALL_11_ALIASES_INCLUDING_NUM_POPU_DEFINITION_AND_VINTAGE",
    ]
    _require(assessment.get("future_evidence_classes_that_may_open_a_new_task") == expected_future_classes, "FUTURE_EVIDENCE_CLASS_DRIFT")

    prohibited = set(assessment.get("prohibited_inferences_and_actions", []))
    required_prohibited = {
        "SYNTHESIZE_URL_FROM_STORAGE_PATH",
        "INVENT_SHAREPOINT_LAYOUTS_DOWNLOAD_ROUTE",
        "APPEND_DOWNLOAD_QUERY_BY_INFERENCE",
        "AUTOMATE_GOV_BR_LOGIN",
        "CAPTURE_OR_REUSE_CREDENTIALS_COOKIES_OAUTH_OR_SESSION",
        "REPEAT_NEGATIVE_ROUTE_WITHOUT_NEW_OFFICIAL_EVIDENCE",
        "INFER_SEMANTIC_EQUIVALENCE_FROM_FIELD_NAME_SIMILARITY",
        "PROMOTE_2025_CLOSURE",
        "PROMOTE_2025_GOLD",
        "EXPAND_CLOSED_SERIES_BEYOND_2024",
        "PROMOTE_2026",
    }
    _require(prohibited == required_prohibited, "PROHIBITED_SET_DRIFT")

    semantics = assessment.get("semantic_guards", {})
    _require(semantics.get("year_2025_status") == "PROVEN_STRUCTURAL_RECENT", "YEAR_2025_STATUS")
    for key in ("annual_closure_status", "semantic_comparability_status", "gold_metrics_status"):
        _require(semantics.get(key) == "UNKNOWN", f"UNKNOWN_REQUIRED:{key}")
    _require(semantics.get("closed_annual_series_first_year") == 2016, "CLOSED_SERIES_START")
    _require(semantics.get("closed_annual_series_last_year") == 2024, "CLOSED_SERIES_END")
    _require(semantics.get("year_2026_status") == "UNPROVEN_CURRENT_YEAR", "YEAR_2026_STATUS")

    auth_guards = assessment.get("authorization_guards", {})
    for key in ("remote_execution_authorized", "rerun_authorized", "authentication_attempt_authorized", "future_batch_execution_authorized"):
        _require(auth_guards.get(key) is False, f"AUTH_GUARD_FALSE_REQUIRED:{key}")

    _require(assessment.get("decision") == "KEEP_BLOCKED_UNTIL_NEW_OFFICIAL_EVIDENCE_CLASS_IS_PINNED", "DECISION_KEEP_BLOCKED")
    _require(assessment.get("next_step") == "SEARCH_REPO_RESIDENT_OR_OFFICIAL_DOCUMENTARY_EVIDENCE_ONLY_BEFORE_DESIGNING_ANY_NEW_REMOTE_GATE", "NEXT_STEP_T0_ONLY")


def main() -> int:
    try:
        validate_consolidation(
            _load(ASSESSMENT_PATH),
            _load(ANTONIETA_PATH),
            _load(TASK008_PATH),
            _load(TASK009B_PATH),
            _load(TASK009C_PATH),
        )
    except (OSError, json.JSONDecodeError, RouteDeadEndConsolidationError) as exc:
        print(str(exc))
        return 13
    print(json.dumps({
        "status": "PASS_TASK009D_ROUTE_DEAD_END_CONSOLIDATION_T0",
        "network_authorized": False,
        "source_get_count": 0,
        "decision": "KEEP_BLOCKED_UNTIL_NEW_OFFICIAL_EVIDENCE_CLASS_IS_PINNED",
        "closed_annual_series_last_year": 2024,
        "gold_2025": "UNKNOWN",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
