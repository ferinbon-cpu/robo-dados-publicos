from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "config" / "siope_2025_official_alias_documentary_discovery_authorization.v1.json"


def _load() -> dict:
    return json.loads(AUTH.read_text(encoding="utf-8"))


def test_authorization_is_exactly_bounded() -> None:
    data = _load()
    assert data["schema"] == "SIOPE_2025_OFFICIAL_ALIAS_DOCUMENTARY_DISCOVERY_AUTHORIZATION_V1"
    assert data["task"] == "TASK_009E_L"
    assert data["authorized"] is True
    assert data["one_shot"] is True
    assert data["scope"] == "BOUNDED_OFFICIAL_DOCUMENTARY_DISCOVERY_ONLY"
    assert data["questions"] == ["S1_NUM_POPU", "S2_FINANCIAL_ALIAS_BRIDGE"]
    assert data["allowed_authorities"] == ["FNDE"]
    assert set(data["allowed_hosts"]) == {"www.gov.br", "gov.br", "www.fnde.gov.br", "fnde.gov.br"}
    assert data["allowed_methods"] == ["GET"]
    assert data["maximum_official_document_opens"] == 12
    assert data["maximum_distinct_official_urls"] == 12
    assert data["maximum_attempts_per_url"] == 1


def test_authorization_is_consumed_and_high_risk_actions_remain_blocked() -> None:
    data = _load()
    for key in (
        "retry_authorized",
        "authentication_authorized",
        "cookies_authorized",
        "oauth_authorized",
        "credential_use_authorized",
        "sharepoint_401_route_reuse_authorized",
        "antonieta_login_authorized",
        "limeira_financial_data_query_authorized",
        "municipality_parameter_authorized",
        "year_period_data_parameter_authorized",
        "binary_package_download_authorized",
        "source_data_collection_authorized",
        "gold_computation_authorized",
        "semantic_promotion_in_same_execution_authorized",
        "closure_promotion_in_same_execution_authorized",
        "publication_authorized",
        "drive_access_authorized",
    ):
        assert data[key] is False
    assert data["authorization_consumed"] is True
    assert data["consumption_result"] == "COMPLETED_BOUNDED_DOCUMENTARY_DISCOVERY_NO_PROMOTION"
    assert data["official_document_open_count"] == 11
    assert data["distinct_official_url_count"] == 11
    assert data["unused_url_budget"] == 1
    assert data["rerun_authorized"] is False
    assert data["result_review_required_before_any_promotion"] is True
