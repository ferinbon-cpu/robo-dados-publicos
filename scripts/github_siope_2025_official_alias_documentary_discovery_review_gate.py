from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "config" / "siope_2025_official_alias_documentary_discovery_review.v1.json"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "TASK_009E_L_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_RUN_1_0.8.0.json"
AUTH_PATH = ROOT / "config" / "siope_2025_official_alias_documentary_discovery_authorization.v1.json"
PASS = "PASS_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_REVIEW_T0"
ERROR = "STOP_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_REVIEW"


class ReviewGateError(RuntimeError):
    pass


def _stop(code: str) -> None:
    raise ReviewGateError(f"{ERROR}_{code}")


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _stop("OBJECT_REQUIRED")
    return value


def validate(review: dict, evidence: dict, auth: dict) -> str:
    if review.get("schema") != "SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_REVIEW_V1":
        _stop("REVIEW_SCHEMA")
    if review.get("task") != "TASK_009E_L_R" or review.get("tier") != "T0_OFFLINE_REVIEW":
        _stop("REVIEW_SCOPE")
    if evidence.get("evidence_schema") != "TASK_009E_L_SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_RUN_1_V1":
        _stop("EVIDENCE_SCHEMA")
    if auth.get("schema") != "SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_AUTHORIZATION_V1":
        _stop("AUTH_SCHEMA")

    expected_auth = "SIOPE2025-ALIAS-DOC-DISCOVERY-20260828-01"
    if evidence.get("authorization_id") != expected_auth or auth.get("authorization_id") != expected_auth:
        _stop("AUTH_ID")
    if auth.get("one_shot") is not True or auth.get("authorization_consumed") is not True:
        _stop("AUTH_CONSUMPTION")
    if auth.get("rerun_authorized") is not False:
        _stop("AUTH_RERUN")

    execution = evidence.get("execution")
    if not isinstance(execution, dict):
        _stop("EXECUTION")
    if execution.get("official_document_open_count") != 11:
        _stop("OPEN_COUNT")
    if execution.get("distinct_official_url_count") != 11:
        _stop("URL_COUNT")
    if execution.get("maximum_authorized_official_document_opens") != 12:
        _stop("OPEN_BUDGET")
    if execution.get("maximum_authorized_distinct_official_urls") != 12:
        _stop("URL_BUDGET")
    if execution.get("unused_url_budget") != 1:
        _stop("UNUSED_BUDGET")
    if execution.get("attempts_per_url_max_observed") != 1 or execution.get("retry_count") != 0:
        _stop("RETRY")

    zero_effects = (
        "authentication_attempt_count",
        "sharepoint_401_route_reuse_count",
        "antonieta_login_attempt_count",
        "limeira_financial_data_query_count",
        "municipality_parameter_data_query_count",
        "year_period_data_query_count",
        "binary_package_download_count",
        "drive_read_count",
        "drive_write_count",
        "publication_count",
        "gold_computation_count",
    )
    for key in zero_effects:
        if execution.get(key) != 0:
            _stop(f"NONZERO_{key.upper()}")

    attempts = evidence.get("official_url_attempts")
    if not isinstance(attempts, list) or len(attempts) != 11:
        _stop("URL_ATTEMPTS")
    urls = [item.get("url") for item in attempts if isinstance(item, dict)]
    if len(urls) != 11 or len(set(urls)) != 11:
        _stop("URL_UNIQUENESS")
    blocked_sharepoint = "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip"
    if blocked_sharepoint in urls:
        _stop("SHAREPOINT_REUSED")

    question_results = evidence.get("question_results")
    if not isinstance(question_results, dict):
        _stop("QUESTION_RESULTS")
    s1 = question_results.get("S1_NUM_POPU")
    s2 = question_results.get("S2_FINANCIAL_ALIAS_BRIDGE")
    if not isinstance(s1, dict) or s1.get("status") != "NOT_PROVEN":
        _stop("S1_STATUS")
    if any(
        s1.get(key) is not False
        for key in (
            "official_primary_field_definition_found",
            "official_primary_population_source_rule_found",
            "official_primary_vintage_rule_found",
            "current_or_2025_applicability_proven",
        )
    ):
        _stop("S1_PROMOTION")
    if not isinstance(s2, dict) or s2.get("status") != "NOT_PROVEN":
        _stop("S2_STATUS")
    if s2.get("historical_concept_definitions_reaffirmed_count") != 10:
        _stop("S2_HISTORICAL_COUNT")
    if s2.get("current_alias_identity_proven_count") != 0 or s2.get("current_alias_identity_required_count") != 10:
        _stop("S2_ALIAS_COUNT")
    if s2.get("current_or_2025_applicability_proven") is not False:
        _stop("S2_PROMOTION")

    if evidence.get("promotion_performed") is not False:
        _stop("PROMOTION_PERFORMED")
    consumption = evidence.get("authorization_consumption")
    if not isinstance(consumption, dict) or consumption.get("consumed") is not True:
        _stop("EVIDENCE_CONSUMPTION")
    if consumption.get("rerun_authorized") is not False:
        _stop("EVIDENCE_RERUN")
    if consumption.get("future_remote_discovery_requires_new_explicit_owner_authorization") is not True:
        _stop("FUTURE_AUTH_BOUNDARY")

    if review.get("decision") != "KEEP_UNKNOWN":
        _stop("DECISION")
    remote = review.get("remote_effects_in_review")
    if not isinstance(remote, dict):
        _stop("REVIEW_REMOTE_EFFECTS")
    if remote != {
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "gold_computation": False,
    }:
        _stop("REVIEW_NOT_T0")

    resulting = review.get("resulting_state")
    if not isinstance(resulting, dict):
        _stop("RESULTING_STATE")
    expected_state = {
        "year_2025_status": "PROVEN_STRUCTURAL_RECENT",
        "p6_availability_status": "PROVEN_AVAILABLE_CLOSURE_UNKNOWN",
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "closed_series_eligible": False,
        "closed_annual_series_first_year": 2016,
        "closed_annual_series_last_year": 2024,
        "gold_metrics_status": "UNKNOWN",
        "year_2026_status": "UNPROVEN_CURRENT_YEAR",
    }
    if resulting != expected_state:
        _stop("STATE_PROMOTION")

    guards = review.get("guards")
    if not isinstance(guards, dict) or not guards:
        _stop("GUARDS")
    if any(value is not False for value in guards.values()):
        _stop("GUARD_PROMOTION")

    if review.get("next_gate") != "NEW_OFFICIAL_EVIDENCE_REQUIRED_BEFORE_ANY_FURTHER_REMOTE_DISCOVERY_OR_2025_SEMANTIC_PROMOTION":
        _stop("NEXT_GATE")
    return PASS


def main() -> int:
    review = _load(REVIEW_PATH)
    evidence = _load(EVIDENCE_PATH)
    auth = _load(AUTH_PATH)
    print(validate(review, evidence, auth))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
