from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, signature_review: dict, resource_design: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_BOOLEAN_ONLY_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DESIGN",
        "observation_semantics": "BROWSER_SIDE_KNOWN_IDENTIFIER_STRUCTURAL_RELATIONS_BOOLEAN_ONLY",
        "dom_text_transient_comparison": "ALLOWED_KNOWN_PUBLIC_IDENTIFIERS_BOOLEAN_RELATIONS_ONLY",
        "dom_attribute_transient_comparison": "ALLOWED_KNOWN_PUBLIC_IDENTIFIERS_BOOLEAN_RELATIONS_ONLY",
        "dom_text_return": "PROHIBITED",
        "dom_attribute_value_return": "PROHIBITED",
        "element_text_return": "PROHIBITED",
        "element_attribute_return": "PROHIBITED",
        "tag_name_return": "PROHIBITED",
        "fragment_value_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "resource_data_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
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
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(signature_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_REVIEW", "SIGNATURE_REVIEW_STATUS")
    _require(signature_review.get("technical_callable_pattern_status"), "PROVEN_PRESENT_ON_OFFICIAL_APPLICATION_PINNED_RUN", "CALLABLE_STATUS")
    _require(signature_review.get("technical_parameter_presence_status"), "PROVEN_ALL_THREE_PRESENT_ON_OFFICIAL_APPLICATION_PINNED_RUN", "PARAMETER_STATUS")
    _require(signature_review.get("service_document_name_application_status"), "NOT_OBSERVED_ON_PINNED_APPLICATION_RUN", "SERVICE_NAME_APPLICATION_STATUS")
    _require(signature_review.get("cross_surface_name_relation_status"), "UNPROVEN_DIFFERENT_OFFICIAL_SURFACES", "NAME_RELATION")
    _require(signature_review.get("structural_binding_status"), "UNPROVEN", "STRUCTURAL_BINDING")
    _require(signature_review.get("resource_get_authorized"), False, "SIGNATURE_RESOURCE_AUTH")

    _require(resource_design.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN", "RESOURCE_DESIGN_STATUS")
    _require(resource_design.get("service_document_declared_name"), "_Dados_Gerais_Siope", "SERVICE_NAME")
    _require(resource_design.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE_NAME")
    _require(resource_design.get("technical_callable_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMETERS")
    _require(resource_design.get("resource_get_authorized"), False, "RESOURCE_AUTH")

    identifiers = config.get("known_public_identifiers") or {}
    _require(identifiers.get("service_document_declared_name"), resource_design["service_document_declared_name"], "CONFIG_SERVICE_NAME")
    _require(identifiers.get("technical_callable_pattern_name"), resource_design["technical_callable_pattern_name"], "CONFIG_CALLABLE_NAME")
    _require(identifiers.get("technical_parameter_names"), resource_design["technical_callable_parameter_names"], "CONFIG_PARAMETERS")

    expected_fields = [
        "technical_name_in_dom_text",
        "technical_name_in_dom_attribute",
        "all_parameters_in_dom_text",
        "all_parameters_in_dom_attributes",
        "minimal_container_with_callable_and_all_parameters",
        "code_like_container_with_callable_and_all_parameters",
        "ordered_callable_parameter_sequence_in_minimal_container",
        "navigation_attribute_contains_callable_name",
        "service_and_callable_same_minimal_container",
    ]
    _require(config.get("allowed_return_fields"), expected_fields, "RETURN_FIELDS")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "returned_observations": expected_fields,
        "observation_semantics": config["observation_semantics"],
        "known_identifier_count": 5,
        "structural_binding_status": "UNPROVEN_PENDING_BOOLEAN_DIAGNOSTICS",
        "network_called": False,
        "dom_interaction_authorized": False,
        "dom_text_return_authorized": False,
        "dom_attribute_value_return_authorized": False,
        "element_material_return_authorized": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
