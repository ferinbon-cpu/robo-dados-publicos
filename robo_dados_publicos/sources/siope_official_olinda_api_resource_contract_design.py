from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN"


class SiopeOfficialOlindaApiResourceContractDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiResourceContractDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiResourceContractDesignError(f"{ERROR}_{code}")


def validate_config(config: dict, review: dict, research: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_OLINDA_RESOURCE_CONTRACT_AMBIGUITY_DESIGN",
        "review_config_path": "config/source_expansion.siope_official_olinda_api_service_discovery_review.json",
        "review_config_git_blob_sha": "ba38f3909beb35afd8afdb514236553588ab29d3",
        "public_research_evidence_path": "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_PUBLIC_RESEARCH_0.8.0.json",
        "official_service_root": "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/",
        "official_application_url": "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
        "service_document_declared_name": "_Dados_Gerais_Siope",
        "technical_callable_pattern_name": "Dados_Gerais_Siope",
        "technical_callable_parameter_names": ["Ano_Consulta", "Num_Peri", "Sig_UF"],
        "service_document_name_status": "PROVEN_STRUCTURAL_NAME_ON_PINNED_OFFICIAL_SERVICE_DOCUMENT",
        "technical_callable_pattern_status": "INDEPENDENT_TECHNICAL_CORROBORATION_ONLY",
        "name_identity_relation_status": "UNPROVEN",
        "leading_underscore_semantics_status": "UNPROVEN",
        "callable_operation_kind_status": "UNPROVEN",
        "resource_schema_status": "UNPROVEN",
        "parameter_semantics_status": "UNPROVEN",
        "direct_resource_get_safe_status": "NOT_PROVEN_SAFE",
        "application_static_surface_status": "OFFICIAL_REACHABLE_CLIENT_TEMPLATE_ONLY",
        "next_diagnostic_surface": "OFFICIAL_APPLICATION_PAGE_PASSIVE_RUNTIME",
        "network_access": "PROHIBITED_IN_DESIGN_GATE",
        "resource_get": "PROHIBITED",
        "query_parameters": "PROHIBITED",
        "request_body": "PROHIBITED",
        "follow_redirects": "PROHIBITED",
        "follow_service_links": "PROHIBITED",
        "browser_execution": "PROHIBITED_IN_DESIGN_GATE",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "authentication": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    policy = config.get("future_runtime_policy") or {}
    expected_policy = {
        "initial_document": "EXACT_OFFICIAL_APPLICATION_URL_GET_ONCE",
        "official_static_assets": "ALLOWLISTED_GET_ONLY",
        "xhr_fetch": "BLOCK_BEFORE_NETWORK_AND_RECORD_SANITIZED_SHAPE_ONLY",
        "other_dynamic_requests": "BLOCK_BEFORE_NETWORK",
        "query_values": "NEVER_PERSIST",
        "response_bodies": "NEVER_PERSIST",
        "resource_data_request": "PROHIBITED",
        "pilot_values": "PROHIBITED",
    }
    _require(policy, expected_policy, "FUTURE_RUNTIME_POLICY")

    _require(review.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_REVIEW_0_8_0", "REVIEW_GATE")
    _require(review.get("observed_target_collection"), "_Dados_Gerais_Siope", "REVIEW_OBSERVED_TARGET")
    _require(review.get("resource_call_disposition"), "NOT_CALLED", "REVIEW_RESOURCE_CALL")
    _require(review.get("resource_schema_disposition"), "UNPROVEN", "REVIEW_SCHEMA")
    _require(review.get("parameter_semantics_disposition"), "UNPROVEN", "REVIEW_PARAMETERS")
    _require(review.get("collection_authorized"), False, "REVIEW_COLLECTION")
    _require(review.get("next_gate"), config["gate_id"], "REVIEW_NEXT_GATE")

    ambiguity = research.get("contract_ambiguity") or {}
    _require(ambiguity.get("service_document_name"), "_Dados_Gerais_Siope", "RESEARCH_SERVICE_NAME")
    _require(ambiguity.get("technical_callable_name"), "Dados_Gerais_Siope", "RESEARCH_CALLABLE_NAME")
    _require(ambiguity.get("same_contract_identity_proven"), False, "RESEARCH_IDENTITY")
    _require(ambiguity.get("safe_direct_resource_get_available"), False, "RESEARCH_SAFE_GET")


def design_resource_contract(config: dict, review: dict, research: dict) -> dict:
    validate_config(config, review, research)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "service_document_declared_name": config["service_document_declared_name"],
        "service_document_name_status": config["service_document_name_status"],
        "technical_callable_pattern_name": config["technical_callable_pattern_name"],
        "technical_callable_pattern_status": config["technical_callable_pattern_status"],
        "technical_callable_parameter_names": config["technical_callable_parameter_names"],
        "name_identity_relation_status": config["name_identity_relation_status"],
        "leading_underscore_semantics_status": config["leading_underscore_semantics_status"],
        "callable_operation_kind_status": config["callable_operation_kind_status"],
        "resource_schema_status": config["resource_schema_status"],
        "parameter_semantics_status": config["parameter_semantics_status"],
        "direct_resource_get_safe_status": config["direct_resource_get_safe_status"],
        "next_diagnostic_surface": config["next_diagnostic_surface"],
        "route_synthesized_or_guessed": False,
        "resource_get_authorized": False,
        "query_parameters_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
