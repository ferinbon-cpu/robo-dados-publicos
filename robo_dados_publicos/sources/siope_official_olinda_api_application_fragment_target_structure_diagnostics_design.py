from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_DESIGN"

COUNT_FIELDS = [
    "fragment_navigation_match_count",
    "distinct_fragment_value_count",
    "fragment_route_like_count",
    "fragment_anchor_like_count",
    "fragment_target_resolved_count",
    "fragment_target_contains_callable_name_count",
    "fragment_target_contains_all_parameter_names_count",
    "fragment_target_ordered_parameter_sequence_count",
    "fragment_target_open_parenthesis_count",
    "fragment_target_query_marker_count",
    "fragment_target_format_token_count",
    "fragment_target_contract_like_count",
    "fragment_value_contains_all_parameter_names_count",
    "fragment_value_parentheses_present_count",
    "fragment_value_query_marker_present_count",
    "fragment_value_format_token_present_count",
]


class SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, prerequisite_review: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PASSIVE_SAME_DOCUMENT_FRAGMENT_TARGET_STRUCTURE_COUNT_DIAGNOSTICS_DESIGN", "MODE")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMETERS")
    _require(config.get("matching_attribute_name"), "href", "ATTRIBUTE")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("minimum_fragment_matches"), 2, "MIN_MATCH")
    _require(config.get("max_fragment_matches"), 8, "MAX_MATCH")
    _require(config.get("fragment_value_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_FOR_FIXED_COUNT_CLASSIFICATION", "TRANSIENT_FRAGMENT")
    _require(config.get("fragment_target_text_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_FOR_FIXED_COUNT_CLASSIFICATION", "TRANSIENT_TARGET")

    _require(prerequisite_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(prerequisite_review.get("rendered_dom_known_syntax_strategy_status"), "EXHAUSTED_FOR_THIS_KNOWN_TEXTUAL_SKELETON_ON_PINNED_RUN", "REVIEW_EXHAUSTED")
    _require(prerequisite_review.get("technical_callable_presence_status"), "TWO_EXACT_CALLABLE_OCCURRENCES_IN_MINIMAL_CONTAINER_ON_PINNED_RUN", "REVIEW_CALLABLE")
    _require(prerequisite_review.get("resource_route_contract_status"), "UNPROVEN", "REVIEW_RESOURCE")
    _require(prerequisite_review.get("callable_semantics_status"), "UNPROVEN", "REVIEW_SEMANTICS")

    for key in (
        "raw_navigation_value_return", "navigation_fragment_return", "fragment_target_identifier_return",
        "fragment_target_text_return", "dom_text_return", "dom_attribute_value_return", "element_text_return",
        "element_attribute_return", "tag_name_return", "html_capture", "script_source_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dom_interaction",
        "navigation_execution", "history_state_mutation", "form_submission", "dynamic_candidate_network_send",
        "resource_data_request", "pilot_limeira_values_send", "post_request_send", "head_request",
        "authentication", "captcha_bypass", "credential_capture", "cookie_capture", "artifact_download",
        "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "observation_semantics": config["observation_semantics"],
        "returned_observations": COUNT_FIELDS,
        "fragment_value_transient_read_authorized": True,
        "fragment_target_text_transient_read_authorized": True,
        "raw_fragment_material_return_authorized": False,
        "navigation_execution_authorized": False,
        "history_state_mutation_authorized": False,
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "resource_route_contract_status": "UNPROVEN",
        "callable_semantics_status": "UNPROVEN",
        "next_gate": config["next_gate"],
    }
