from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_DESIGN"


class SiopePublicRuntimeActionControlSemanticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeActionControlSemanticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeActionControlSemanticsDesignError(f"{ERROR}_{code}")


def validate_design(config: dict, review: dict, public_config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PASSIVE_BOOLEAN_ACTION_CONTROL_SEMANTICS_DESIGN",
        "prerequisite_review_config_path": "config/source_expansion.siope_public_runtime_control_value_consistency_review.json",
        "public_runtime_config_path": "config/source_expansion.siope_public_get_runtime_route_diagnostics_gate.json",
        "prerequisite_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW_0_8_0",
        "target_control_name": "acao",
        "target_control_structure": "HIDDEN_INPUT_STRUCTURALLY_OBSERVED",
        "prerequisite_action_semantics": "UNPROVEN_MISMATCH_ON_PINNED_PUBLIC_EXAMPLE",
        "observation_mode": "PASSIVE_NO_INTERACTION_BOOLEAN_RELATIONS_ONLY",
        "returned_boolean_fields": [
            "control_present", "control_is_hidden_input", "query_key_present", "value_attribute_present",
            "property_equals_query", "attribute_equals_query", "property_equals_attribute",
        ],
        "observation_points": ["STABLE_SURFACE_FIRST_OBSERVATION", "PASSIVE_CAPTURE_WINDOW_FINAL_OBSERVATION"],
        "actual_control_value_return": "PROHIBITED",
        "actual_query_value_return": "PROHIBITED",
        "actual_attribute_value_return": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "html_return": "PROHIBITED",
        "free_text_return": "PROHIBITED",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "browser_download_or_install": "PROHIBITED",
        "initial_document_send": "EXACT_PINNED_PUBLIC_INDEXED_EXAMPLE_ONCE_ONLY",
        "official_static_assets": "GET_ONLY_ALLOWLISTED_HOST_AND_EXTENSION",
        "all_other_requests": "ABORT_BEFORE_NETWORK",
        "dom_interaction": "PROHIBITED",
        "control_mutation": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "navigation_after_initial_document": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(review.get("gate_id"), config["prerequisite_gate_id"], "REVIEW_GATE")
    _require(review.get("next_gate"), config["gate_id"], "REVIEW_NEXT_GATE")
    _require(review.get("mismatched_control_names"), ["acao"], "REVIEW_MISMATCH_SCOPE")
    _require(
        review.get("acao_expected_structure"),
        {"id": "acao", "name": "acao", "tag_name": "input", "type": "hidden", "option_count": 0, "associated_stable_label": ""},
        "REVIEW_ACAO_STRUCTURE",
    )
    _require(review.get("acao_value_semantics_disposition"), config["prerequisite_action_semantics"], "REVIEW_ACAO_SEMANTICS")
    _require(review.get("post_request"), "PROHIBITED", "REVIEW_POST_AUTH")
    _require(review.get("dom_interaction"), "PROHIBITED", "REVIEW_INTERACTION_AUTH")
    _require(review.get("pilot_limeira_values_send"), "PROHIBITED", "REVIEW_LIMEIRA")

    _require(public_config.get("gate_id"), "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0", "PUBLIC_GATE")
    _require(public_config.get("pilot_limeira_values_send"), "PROHIBITED", "PUBLIC_LIMEIRA")
    _require(public_config.get("dynamic_candidate_network_send"), "PROHIBITED", "PUBLIC_DYNAMIC_SEND")
    if "352690" in str(public_config.get("public_indexed_example_url", "")):
        raise SiopePublicRuntimeActionControlSemanticsDesignError(f"{ERROR}_PUBLIC_CONFIG_PILOT_VALUE")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "target_control_name": config["target_control_name"],
        "target_control_structure": config["target_control_structure"],
        "observation_mode": config["observation_mode"],
        "returned_boolean_fields": config["returned_boolean_fields"],
        "observation_points": config["observation_points"],
        "actual_values_may_leave_browser": False,
        "script_source_may_be_captured": False,
        "dom_interaction_authorized": False,
        "control_mutation_authorized": False,
        "form_submission_authorized": False,
        "post_authorized": False,
        "pilot_limeira_values_sent": False,
        "automatic_value_promotion": False,
        "route_synthesized_or_guessed": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
