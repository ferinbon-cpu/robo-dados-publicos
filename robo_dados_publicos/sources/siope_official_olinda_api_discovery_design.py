from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_DISCOVERY_DESIGN"


class SiopeOfficialOlindaApiDiscoveryDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiDiscoveryDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiDiscoveryDesignError(f"{ERROR}_{code}")


def validate_discovery_design(config: dict, base_source: dict, blocked_html: dict, research: dict) -> dict:
    expected_root = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/"
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_DISCOVERY_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_OFFICIAL_OLINDA_API_ALTERNATIVE_ROUTE_DISCOVERY_DESIGN",
        "base_source_config_path": "config/source_expansion.siope_limeira_0_8_0.json",
        "blocked_html_track_config_path": "config/source_expansion.siope_public_indexed_get_second_example_discovery_design.json",
        "public_research_evidence_path": "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_API_PUBLIC_RESEARCH_0.8.0.json",
        "official_application_url": "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
        "official_service_root": expected_root,
        "official_scheme": "https",
        "official_host": "www.fnde.gov.br",
        "official_service_path": "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/",
        "html_track_status": "BLOCKED_PENDING_EXPLICIT_SECOND_PUBLIC_EXAMPLE",
        "alternate_track_status": "DESIGN_ONLY_UNVERIFIED_SERVICE_DOCUMENT",
        "public_reference_candidate_resource": "Dados_Gerais_Siope",
        "candidate_resource_runtime_status": "UNPROVEN_BY_REPO_RUNTIME",
        "parameter_semantics_runtime_status": "UNPROVEN_BY_REPO_RUNTIME",
        "collection_name_pattern": "^[A-Za-z0-9_]+$",
        "max_collection_names": 64,
        "network_access": "PROHIBITED_IN_DESIGN_GATE",
        "browser_execution": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "raw_response_persistence": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "head_request": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "automatic_value_promotion": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    probe = config.get("initial_live_probe")
    if not isinstance(probe, dict):
        raise SiopeOfficialOlindaApiDiscoveryDesignError(f"{ERROR}_PROBE_OBJECT_REQUIRED")
    probe_exact = {
        "method": "GET",
        "exact_url": expected_root,
        "query_keys": [],
        "request_body": False,
        "municipality_parameter": False,
        "year_parameter": False,
        "period_parameter": False,
        "resource_parameter": False,
        "follow_links": False,
        "max_requests": 1,
        "max_response_bytes": 1048576,
        "accepted_content_types": ["application/json", "application/xml", "application/atomsvc+xml", "text/xml"],
        "raw_response_persistence": False,
        "sanitized_observation_only": True,
        "allowed_observation": [
            "http_status",
            "content_type",
            "service_document_parseable",
            "collection_name_count",
            "collection_names",
            "candidate_resource_present",
        ],
    }
    for key, expected in probe_exact.items():
        _require(probe.get(key), expected, f"PROBE_{key.upper()}")

    parsed = urlparse(config["official_service_root"])
    _require(parsed.scheme, config["official_scheme"], "ROOT_SCHEME")
    _require(parsed.hostname, config["official_host"], "ROOT_HOST")
    _require(parsed.path, config["official_service_path"], "ROOT_PATH")
    _require(parsed.query, "", "ROOT_QUERY_MUST_BE_EMPTY")
    _require(parsed.fragment, "", "ROOT_FRAGMENT_MUST_BE_EMPTY")
    if "352690" in config["official_service_root"] or "Limeira" in config["official_service_root"]:
        raise SiopeOfficialOlindaApiDiscoveryDesignError(f"{ERROR}_PILOT_VALUE_IN_ROOT")

    _require(base_source.get("gate_id"), "M7_CONTROLLED_SOURCE_EXPANSION_DESIGN_0_8_0", "BASE_GATE")
    _require(base_source.get("software_version"), "0.8.0", "BASE_VERSION")
    _require(base_source.get("active_validated_version"), "0.7.0", "BASE_ACTIVE_VERSION")
    _require(base_source.get("source", {}).get("collection_authorization"), "PROHIBITED", "BASE_COLLECTION_CLOSED")

    _require(blocked_html.get("gate_id"), "M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_DISCOVERY_DESIGN_0_8_0", "HTML_GATE")
    _require(blocked_html.get("next_state_without_candidate"), config["html_track_status"], "HTML_TRACK_REMAINS_BLOCKED")
    _require(blocked_html.get("runtime_gate_creation_authorized"), False, "HTML_RUNTIME_REMAINS_CLOSED")

    _require(research.get("finding"), "EXPLICIT_OFFICIAL_FNDE_OLINDA_ODATA_SURFACE_FOUND_AS_ALTERNATIVE_ACQUISITION_TRACK", "RESEARCH_FINDING")
    _require(research.get("official_odata_service_root"), expected_root, "RESEARCH_ROOT")
    _require(research.get("public_reference_candidate_resource"), config["public_reference_candidate_resource"], "RESEARCH_RESOURCE")
    _require(research.get("repo_interpretation", {}).get("limeira_api_request_authorized"), False, "RESEARCH_PILOT_CLOSED")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_DISCOVERY_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "html_track_status": config["html_track_status"],
        "alternate_track_status": config["alternate_track_status"],
        "official_service_contract": {
            "scheme": config["official_scheme"],
            "host": config["official_host"],
            "path": config["official_service_path"],
            "method": probe["method"],
            "query_keys": probe["query_keys"],
            "max_requests": probe["max_requests"],
        },
        "public_reference_candidate_resource": config["public_reference_candidate_resource"],
        "candidate_resource_runtime_status": config["candidate_resource_runtime_status"],
        "parameter_semantics_runtime_status": config["parameter_semantics_runtime_status"],
        "pilot_limeira_values_sent": False,
        "route_synthesized_or_guessed": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
