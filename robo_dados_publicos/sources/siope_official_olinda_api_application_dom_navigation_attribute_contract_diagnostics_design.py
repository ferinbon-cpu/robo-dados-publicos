from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, structural_review: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_BOOLEAN_ONLY_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DESIGN",
        "observation_semantics": "BROWSER_SIDE_MATCHING_NAVIGATION_ATTRIBUTE_CLASSIFICATION_BOOLEAN_ONLY",
        "technical_callable_pattern_name": "Dados_Gerais_Siope",
        "technical_parameter_names": ["Ano_Consulta", "Num_Peri", "Sig_UF"],
        "allowed_navigation_attribute_names": ["href", "action"],
        "navigation_attribute_transient_read": "ALLOWED_MATCHING_HREF_ACTION_CLASSIFICATION_BOOLEAN_ONLY",
        "navigation_attribute_value_return": "PROHIBITED",
        "navigation_path_return": "PROHIBITED",
        "navigation_query_return": "PROHIBITED",
        "navigation_fragment_return": "PROHIBITED",
        "element_material_return": "PROHIBITED",
        "tag_name_return": "PROHIBITED",
        "dom_text_return": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "navigation_execution": "PROHIBITED",
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
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(
        structural_review.get("status"),
        "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_REVIEW",
        "REVIEW_STATUS",
    )
    _require(
        structural_review.get("structural_binding_status"),
        "PROVEN_CALLABLE_AND_PARAMETERS_COLOCATED_ORDERED_ON_PINNED_RUN",
        "STRUCTURAL_BINDING",
    )
    _require(
        structural_review.get("navigation_attribute_presence_status"),
        "PROVEN_CALLABLE_NAME_IN_NAVIGATION_ATTRIBUTE_ON_PINNED_RUN",
        "NAVIGATION_ATTRIBUTE_PRESENCE",
    )
    _require(structural_review.get("navigation_target_semantics_status"), "UNPROVEN_VALUE_NOT_RETURNED", "TARGET_SEMANTICS")
    _require(structural_review.get("resource_route_contract_status"), "UNPROVEN", "RESOURCE_ROUTE")
    _require(structural_review.get("resource_get_authorized"), False, "RESOURCE_AUTH")

    fields = config.get("allowed_return_fields") or []
    expected_fields = [
        "navigation_match_present",
        "navigation_match_unique",
        "navigation_attribute_is_href",
        "navigation_attribute_is_action",
        "navigation_value_fragment_only",
        "navigation_value_relative_nonfragment",
        "navigation_value_same_origin_absolute",
        "navigation_value_resolves_to_application_document",
        "navigation_value_contains_callable_name",
        "navigation_value_contains_all_parameter_names",
        "navigation_value_ordered_callable_parameter_sequence",
        "navigation_value_query_present",
        "navigation_value_parentheses_present",
    ]
    _require(fields, expected_fields, "RETURN_FIELDS")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "observation_semantics": config["observation_semantics"],
        "returned_observations": fields,
        "matching_attribute_names": config["allowed_navigation_attribute_names"],
        "network_called": False,
        "dom_interaction_authorized": False,
        "navigation_execution_authorized": False,
        "raw_navigation_value_return_authorized": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
