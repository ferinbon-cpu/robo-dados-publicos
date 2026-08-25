from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN"


class SiopePublicRuntimeControlInteractionDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeControlInteractionDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeControlInteractionDesignError(f"{ERROR}_{code}")


def validate_design(config: dict, contract_review_config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN",
        "prerequisite_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW_0_8_0",
        "prerequisite_public_get_contract_status": "PROVEN_FOR_PINNED_PUBLIC_INDEXED_EXAMPLE",
        "prerequisite_dynamic_route_contract_status": "UNPROVEN_ZERO_CANDIDATES",
        "control_identity_status": "UNPROVEN",
        "stable_surface_labels": ["Exibir:", "Ano:", "UF:", "Planilha:"],
        "label_only_control_selection": "PROHIBITED",
        "control_interaction_authorized": False,
        "control_inventory_required": True,
        "pilot_limeira_values_send": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "form_submission": "PROHIBITED",
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
        "network_access_for_design_gate": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    inventory = config.get("inventory_observation_scope") or {}
    _require(inventory.get("allowed_control_tags"), ["select", "input", "button"], "INVENTORY_TAGS")
    _require(
        inventory.get("allowed_persisted_fields"),
        [
            "associated_stable_label",
            "tag_name",
            "type",
            "id",
            "name",
            "disabled",
            "option_count",
            "form_method",
            "form_action_scheme",
            "form_action_host",
            "form_action_path",
        ],
        "INVENTORY_FIELDS",
    )
    for key in ("control_value_capture", "option_text_capture", "option_value_capture", "html_capture", "free_text_capture"):
        _require(inventory.get(key), "PROHIBITED", f"INVENTORY_{key.upper()}")

    runtime = config.get("future_inventory_runtime") or {}
    runtime_exact = {
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "browser_download_or_install": "PROHIBITED",
        "initial_document_send": "EXACT_PINNED_PUBLIC_INDEXED_EXAMPLE_ONCE_ONLY",
        "official_static_assets": "GET_ONLY_ALLOWLISTED_HOST_AND_EXTENSION",
        "all_other_requests": "ABORT_BEFORE_NETWORK",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "navigation_after_initial_document": "PROHIBITED",
    }
    for key, expected in runtime_exact.items():
        _require(runtime.get(key), expected, f"RUNTIME_{key.upper()}")

    _require(contract_review_config.get("gate_id"), config["prerequisite_gate_id"], "PREREQUISITE_GATE")
    _require(
        contract_review_config.get("public_get_contract_disposition"),
        config["prerequisite_public_get_contract_status"],
        "PREREQUISITE_PUBLIC_GET",
    )
    _require(
        contract_review_config.get("dynamic_route_contract_disposition"),
        config["prerequisite_dynamic_route_contract_status"],
        "PREREQUISITE_DYNAMIC_ROUTE",
    )
    _require(contract_review_config.get("next_gate"), config["gate_id"], "PREREQUISITE_NEXT_GATE")
    _require(contract_review_config.get("automatic_route_promotion"), "PROHIBITED", "PREREQUISITE_PROMOTION")
    _require(contract_review_config.get("route_synthesis_or_guessing"), "PROHIBITED", "PREREQUISITE_GUESSING")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "public_get_contract_status": config["prerequisite_public_get_contract_status"],
        "dynamic_route_contract_status": config["prerequisite_dynamic_route_contract_status"],
        "control_identity_status": "UNPROVEN",
        "control_interaction_authorized": False,
        "control_inventory_required": True,
        "inventory_may_capture_values": False,
        "route_synthesized_or_guessed": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
