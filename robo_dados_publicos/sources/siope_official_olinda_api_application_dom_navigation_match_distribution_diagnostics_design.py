from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, prior_review: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("mode"), "OFFLINE_COUNT_ONLY_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_DESIGN", "MODE")
    _require(prior_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_REVIEW", "PRIOR_REVIEW")
    _require(prior_review.get("navigation_match_cardinality_status"), "MULTIPLE_MATCHES_OBSERVED_NO_SINGLE_TARGET_SELECTED", "MULTIPLE_PREREQUISITE")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("allowed_navigation_attribute_names"), ["href", "action"], "ATTRS")
    _require(config.get("max_navigation_matches"), 32, "MAX")
    _require(config.get("minimum_navigation_matches"), 2, "MIN")
    expected = ["navigation_match_count", "href_match_count", "action_match_count", "fragment_only_match_count", "relative_nonfragment_match_count", "same_origin_absolute_match_count", "resolves_to_application_document_match_count", "contains_all_parameter_names_match_count", "ordered_callable_parameter_sequence_match_count", "query_present_match_count", "parentheses_present_match_count", "callable_parameter_contract_like_match_count", "same_origin_contract_like_match_count"]
    _require(config.get("returned_count_fields"), expected, "FIELDS")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"{key.upper()}")
    prohibited = ["raw_navigation_value_return", "navigation_path_return", "navigation_query_return", "navigation_fragment_return", "element_material_return", "tag_name_return", "dom_text_return", "html_capture", "script_source_capture", "response_body_capture", "request_body_capture", "query_value_persistence", "dom_interaction", "navigation_execution", "form_submission", "dynamic_candidate_network_send", "resource_data_request", "pilot_limeira_values_send", "post_request_send", "head_request", "authentication", "captcha_bypass", "credential_capture", "cookie_capture", "artifact_download", "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion"]
    for key in prohibited:
        _require(config.get(key), "PROHIBITED", f"{key.upper()}")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "observation_semantics": config["observation_semantics"],
        "returned_observations": expected,
        "max_navigation_matches": 32,
        "minimum_navigation_matches": 2,
        "raw_navigation_value_return_authorized": False,
        "navigation_execution_authorized": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
