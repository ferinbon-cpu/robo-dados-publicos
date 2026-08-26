from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, prerequisite_review: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_RENDERED_DOM_KNOWN_SYNTAX_SKELETON_COUNT_DIAGNOSTICS_DESIGN", "MODE")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMETERS")
    _require(config.get("analysis_window_chars"), 4096, "WINDOW")
    _require(config.get("parameter_sequence_window_chars"), 512, "PARAM_WINDOW")
    fields = config.get("returned_count_fields") or []
    _require(len(fields), 16, "FIELD_COUNT")
    _require(len(set(fields)), 16, "FIELD_UNIQUENESS")
    _require(config.get("observation_semantics"), "TRANSIENT_RENDERED_DOM_MINIMAL_CONTRACT_CONTAINER_KNOWN_SYNTAX_INTEGER_COUNTS_ONLY", "SEMANTICS")
    _require(config.get("dom_text_transient_analysis"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_KNOWN_PUBLIC_SYNTAX_RELATIONS", "TRANSIENT_DOM")

    _require(prerequisite_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(prerequisite_review.get("full_known_signature_skeleton_status"), "NOT_OBSERVED_ON_PINNED_LOADED_SCRIPTS", "REVIEW_SKELETON")
    _require(prerequisite_review.get("loaded_script_known_syntax_strategy_status"), "EXHAUSTED_FOR_THIS_KNOWN_TEXTUAL_SKELETON_ON_PINNED_RUN", "REVIEW_STRATEGY")
    _require(prerequisite_review.get("resource_route_contract_status"), "UNPROVEN", "REVIEW_ROUTE")

    for key in (
        "dom_text_return", "dom_attribute_value_return", "element_text_return", "element_attribute_return",
        "tag_name_return", "fragment_value_capture", "html_capture", "script_source_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dynamic_candidate_network_send",
        "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "navigation_execution",
        "form_submission", "post_request_send", "head_request", "authentication", "captcha_bypass",
        "credential_capture", "cookie_capture", "artifact_download", "remote_writes",
        "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "returned_observations": fields,
        "analysis_window_chars": config["analysis_window_chars"],
        "parameter_sequence_window_chars": config["parameter_sequence_window_chars"],
        "observation_semantics": config["observation_semantics"],
        "loaded_script_known_syntax_strategy_status": prerequisite_review["loaded_script_known_syntax_strategy_status"],
        "resource_route_contract_status": "UNPROVEN",
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
