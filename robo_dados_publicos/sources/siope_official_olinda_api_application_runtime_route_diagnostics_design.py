from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError(f"{ERROR}_{code}")


def validate_design(config: dict, resource_design: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PASSIVE_OFFICIAL_APPLICATION_ROUTE_DIAGNOSTICS_DESIGN",
        "resource_contract_design_path": "config/source_expansion.siope_official_olinda_api_resource_contract_design.json",
        "resource_contract_design_git_blob_sha": "302e97aab423435ba74970524415629eb5c89541",
        "exact_application_url": "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
        "expected_scheme": "https",
        "expected_host": "www.fnde.gov.br",
        "expected_path": "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_download_or_install": "PROHIBITED",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "initial_document_policy": "CONTINUE_EXACT_APPLICATION_DOCUMENT_ONCE",
        "static_asset_policy": "CONTINUE_OFFICIAL_GET_STATIC_ASSETS_ONLY",
        "dynamic_request_policy": "ABORT_ALL_DYNAMIC_BEFORE_NETWORK_AND_RECORD_SANITIZED_SHAPES",
        "allowed_hosts": ["www.fnde.gov.br"],
        "static_asset_methods": ["GET"],
        "static_asset_resource_types": ["Script", "Stylesheet", "Image", "Font"],
        "candidate_methods": ["GET", "POST"],
        "candidate_resource_types": ["XHR", "Fetch"],
        "surface_verification": "DOCUMENT_LOCATION_AND_READY_STATE_ONLY_NO_BODY_TEXT",
        "body_text_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "resource_data_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request_send": "PROHIBITED",
        "head_request": "PROHIBITED",
        "authentication": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "automatic_route_promotion": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "URL_SCHEME")
    _require(parsed.hostname, config["expected_host"], "URL_HOST")
    _require(parsed.path, config["expected_path"], "URL_PATH")
    _require(parsed.query, "", "URL_QUERY")
    _require(parsed.fragment, "", "URL_FRAGMENT")
    if "352690" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError(f"{ERROR}_PILOT_VALUE")

    _require(resource_design.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN_0_8_0", "RESOURCE_DESIGN_GATE")
    _require(resource_design.get("name_identity_relation_status"), "UNPROVEN", "RESOURCE_NAME_RELATION")
    _require(resource_design.get("direct_resource_get_safe_status"), "NOT_PROVEN_SAFE", "RESOURCE_SAFE_GET")
    _require(resource_design.get("resource_get"), "PROHIBITED", "RESOURCE_GET")
    _require(resource_design.get("collection_authorized"), False, "RESOURCE_COLLECTION")
    _require(resource_design.get("next_gate"), config["gate_id"], "RESOURCE_NEXT_GATE")

    fields = config.get("sanitized_shape_fields") or []
    forbidden = {"url", "query_values", "body", "headers", "response_body", "request_body"}
    if forbidden.intersection(fields):
        raise SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError(f"{ERROR}_UNSAFE_SHAPE_FIELDS")
    if "route_without_query" not in fields or "query_keys" not in fields:
        raise SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError(f"{ERROR}_MISSING_SANITIZED_FIELDS")


def design_application_route_diagnostics(config: dict, resource_design: dict) -> dict:
    validate_design(config, resource_design)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "initial_document_policy": config["initial_document_policy"],
        "static_asset_policy": config["static_asset_policy"],
        "dynamic_request_policy": config["dynamic_request_policy"],
        "surface_verification": config["surface_verification"],
        "dynamic_candidate_network_sent": False,
        "resource_data_request_authorized": False,
        "pilot_limeira_values_sent": False,
        "route_synthesized_or_guessed": False,
        "automatic_route_promotion": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
