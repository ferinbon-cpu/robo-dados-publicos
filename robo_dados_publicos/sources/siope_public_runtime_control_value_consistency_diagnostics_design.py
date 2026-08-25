from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_DESIGN"


class SiopePublicRuntimeControlValueConsistencyDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeControlValueConsistencyDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeControlValueConsistencyDesignError(f"{ERROR}_{code}")


def validate_design(config: dict, review_config: dict, public_config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_BROWSER_SIDE_BOOLEAN_VALUE_CONSISTENCY_DESIGN",
        "prerequisite_review_config_path": "config/source_expansion.siope_public_runtime_control_inventory_review.json",
        "public_runtime_config_path": "config/source_expansion.siope_public_get_runtime_route_diagnostics_gate.json",
        "prerequisite_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_REVIEW_0_8_0",
        "prerequisite_control_identity_status": "STRUCTURALLY_OBSERVED_NOT_VALUE_PROVEN",
        "prerequisite_form_post_status": "OBSERVED_STRUCTURAL_ONLY_NOT_AUTHORIZED",
        "prerequisite_dynamic_route_status": "UNPROVEN_ZERO_CANDIDATES",
        "comparison_control_names": ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        "comparison_semantics": "BROWSER_SIDE_CONTROL_VALUE_EQUALS_CURRENT_DOCUMENT_QUERY_VALUE_BOOLEAN_ONLY",
        "returned_comparison_fields": ["control_name", "control_present", "query_key_present", "value_matches_query"],
        "actual_control_value_return": "PROHIBITED",
        "actual_query_value_return": "PROHIBITED",
        "option_text_return": "PROHIBITED",
        "option_value_return": "PROHIBITED",
        "html_return": "PROHIBITED",
        "free_text_return": "PROHIBITED",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "browser_download_or_install": "PROHIBITED",
        "initial_document_send": "EXACT_PINNED_PUBLIC_INDEXED_EXAMPLE_ONCE_ONLY",
        "official_static_assets": "GET_ONLY_ALLOWLISTED_HOST_AND_EXTENSION",
        "all_other_requests": "ABORT_BEFORE_NETWORK",
        "dom_interaction": "PROHIBITED",
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
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(review_config.get("gate_id"), config["prerequisite_gate_id"], "REVIEW_GATE")
    _require(review_config.get("control_identity_disposition"), config["prerequisite_control_identity_status"], "REVIEW_CONTROL_IDENTITY")
    _require(review_config.get("form_post_disposition"), config["prerequisite_form_post_status"], "REVIEW_FORM_POST")
    _require(review_config.get("dynamic_route_contract_disposition"), config["prerequisite_dynamic_route_status"], "REVIEW_DYNAMIC_ROUTE")
    _require(review_config.get("next_gate"), config["gate_id"], "REVIEW_NEXT_GATE")
    _require(review_config.get("control_value_semantics"), "UNPROVEN", "REVIEW_VALUE_SEMANTICS")
    _require(review_config.get("option_value_mapping"), "UNPROVEN", "REVIEW_OPTION_MAPPING")
    _require(review_config.get("post_request"), "PROHIBITED", "REVIEW_POST_REQUEST")

    _require(public_config.get("gate_id"), "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0", "PUBLIC_GATE")
    _require(public_config.get("expected_query_keys"), config["comparison_control_names"], "PUBLIC_QUERY_KEYS")
    _require(public_config.get("pilot_limeira_values_send"), "PROHIBITED", "PUBLIC_LIMEIRA")
    _require(public_config.get("dynamic_candidate_network_send"), "PROHIBITED", "PUBLIC_DYNAMIC_SEND")
    if "352690" in str(public_config.get("public_indexed_example_url", "")):
        raise SiopePublicRuntimeControlValueConsistencyDesignError(f"{ERROR}_PUBLIC_CONFIG_PILOT_VALUE")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "comparison_control_names": config["comparison_control_names"],
        "comparison_semantics": config["comparison_semantics"],
        "browser_may_return_actual_control_values": False,
        "browser_may_return_actual_query_values": False,
        "comparison_result_boolean_only": True,
        "dom_interaction_authorized": False,
        "form_submission_authorized": False,
        "post_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
