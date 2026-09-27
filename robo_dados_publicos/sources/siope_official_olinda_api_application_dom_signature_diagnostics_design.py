from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, fragment_review: dict, resource_design: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_BOOLEAN_ONLY_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_DESIGN",
        "observation_semantics": "BROWSER_SIDE_EXACT_KNOWN_PUBLIC_IDENTIFIER_PRESENCE_BOOLEAN_ONLY",
        "dom_text_transient_comparison": "ALLOWED_EXACT_KNOWN_IDENTIFIERS_BOOLEAN_ONLY",
        "dom_attribute_transient_comparison": "ALLOWED_EXACT_KNOWN_IDENTIFIERS_BOOLEAN_ONLY",
        "dom_text_return": "PROHIBITED",
        "dom_attribute_value_return": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "fragment_value_capture": "PROHIBITED",
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
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(fragment_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_REVIEW", "FRAGMENT_REVIEW_STATUS")
    _require(fragment_review.get("application_surface_status"), "PROVEN_FRAGMENT_TOLERANT_ON_PINNED_RUN", "SURFACE_STATUS")
    _require(fragment_review.get("passive_network_route_status"), "EXHAUSTED_ZERO_DYNAMIC_CANDIDATES_ON_PINNED_RUN", "NETWORK_STATUS")
    _require(fragment_review.get("resource_get_authorized"), False, "FRAGMENT_RESOURCE_AUTH")

    _require(resource_design.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN", "RESOURCE_DESIGN_STATUS")
    _require(resource_design.get("service_document_declared_name"), "_Dados_Gerais_Siope", "SERVICE_NAME")
    _require(resource_design.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE_NAME")
    _require(resource_design.get("technical_callable_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMETERS")
    _require(resource_design.get("resource_get_authorized"), False, "RESOURCE_AUTH")

    identifiers = config.get("known_public_identifiers") or {}
    _require(identifiers.get("service_document_declared_name"), resource_design["service_document_declared_name"], "CONFIG_SERVICE_NAME")
    _require(identifiers.get("technical_callable_pattern_name"), resource_design["technical_callable_pattern_name"], "CONFIG_CALLABLE_NAME")
    _require(identifiers.get("technical_parameter_names"), resource_design["technical_callable_parameter_names"], "CONFIG_PARAMETERS")
    _require(config.get("allowed_return_fields"), [
        "service_document_declared_name_present",
        "technical_callable_pattern_name_present",
        "Ano_Consulta_present",
        "Num_Peri_present",
        "Sig_UF_present",
    ], "RETURN_FIELDS")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "target_public_identifier_count": 5,
        "returned_observations": config["allowed_return_fields"],
        "observation_semantics": config["observation_semantics"],
        "network_called": False,
        "dom_interaction_authorized": False,
        "body_or_dom_text_return_authorized": False,
        "attribute_value_return_authorized": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
