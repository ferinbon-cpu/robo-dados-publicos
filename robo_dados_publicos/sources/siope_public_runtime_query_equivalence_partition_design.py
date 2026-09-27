from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_QUERY_EQUIVALENCE_PARTITION_DESIGN"


class SiopePublicRuntimeQueryEquivalencePartitionDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeQueryEquivalencePartitionDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeQueryEquivalencePartitionDesignError(f"{ERROR}_{code}")


def validate_partition_design(config: dict, action_review: dict, value_review: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_QUERY_EQUIVALENCE_PARTITION_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_QUERY_EQUIVALENCE_PARTITION_DESIGN",
        "action_semantics_review_config_path": "config/source_expansion.siope_public_runtime_action_control_semantics_review.json",
        "value_consistency_review_config_path": "config/source_expansion.siope_public_runtime_control_value_consistency_review.json",
        "prerequisite_action_review_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_REVIEW_0_8_0",
        "prerequisite_value_review_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW_0_8_0",
        "all_same_name_query_control_names": ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        "query_equivalent_control_names": ["admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        "non_equivalent_same_name_control_names": ["acao"],
        "query_equivalent_disposition": "OBSERVED_QUERY_VALUE_EQUALITY_ON_PINNED_PUBLIC_EXAMPLE_ONLY",
        "non_equivalent_same_name_disposition": "STABLE_NON_EQUIVALENT_SAME_NAME_ON_PINNED_PUBLIC_EXAMPLE",
        "same_name_implies_value_equivalence": False,
        "same_name_implies_semantic_role_equivalence": False,
        "seven_control_generalization_status": "UNPROVEN_BEYOND_PINNED_PUBLIC_EXAMPLE",
        "acao_value_origin_status": "UNPROVEN",
        "acao_query_semantics_status": "UNPROVEN",
        "independent_public_example_required_before_generalization": True,
        "second_example_must_be_explicitly_proven_not_synthesized": True,
        "form_post_disposition": "OBSERVED_STRUCTURAL_ONLY_NOT_AUTHORIZED",
        "dynamic_route_contract_disposition": "UNPROVEN_ZERO_CANDIDATES",
        "network_access": "PROHIBITED",
        "browser_execution": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "control_mutation": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "control_value_capture": "PROHIBITED",
        "attribute_value_capture": "PROHIBITED",
        "query_value_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "free_text_capture": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_DISCOVERY_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(action_review.get("gate_id"), config["prerequisite_action_review_gate_id"], "ACTION_REVIEW_GATE")
    _require(action_review.get("next_gate"), config["gate_id"], "ACTION_REVIEW_NEXT_GATE")
    _require(action_review.get("relation_stability_disposition"), "STABLE_ACROSS_OBSERVED_WINDOW", "ACTION_STABILITY")
    _require(action_review.get("internal_consistency_disposition"), "PROPERTY_EQUALS_ATTRIBUTE_ON_BOTH_OBSERVATIONS", "ACTION_INTERNAL_CONSISTENCY")
    _require(action_review.get("query_equivalence_disposition"), "PROPERTY_AND_ATTRIBUTE_DIFFER_FROM_QUERY_ON_BOTH_OBSERVATIONS", "ACTION_QUERY_EQUIVALENCE")
    _require(action_review.get("client_side_mutation_disposition"), "NOT_OBSERVED_DURING_MEASURED_WINDOW", "ACTION_MUTATION")
    _require(action_review.get("value_origin_disposition"), "UNPROVEN", "ACTION_ORIGIN")
    _require(action_review.get("query_action_semantics_disposition"), "UNPROVEN", "ACTION_QUERY_SEMANTICS")
    _require(action_review.get("form_post_disposition"), "OBSERVED_STRUCTURAL_ONLY_NOT_AUTHORIZED", "ACTION_POST")
    _require(action_review.get("dynamic_route_contract_disposition"), "UNPROVEN_ZERO_CANDIDATES", "ACTION_DYNAMIC_ROUTE")

    _require(value_review.get("gate_id"), config["prerequisite_value_review_gate_id"], "VALUE_REVIEW_GATE")
    _require(value_review.get("matched_control_names"), config["query_equivalent_control_names"], "MATCHED_CONTROLS")
    _require(value_review.get("mismatched_control_names"), config["non_equivalent_same_name_control_names"], "MISMATCHED_CONTROLS")
    _require(value_review.get("matched_value_consistency_disposition"), "OBSERVED_MATCH_ON_PINNED_PUBLIC_EXAMPLE_ONLY", "MATCHED_DISPOSITION")
    _require(value_review.get("overall_value_mapping_disposition"), "PARTIAL_7_OF_8_PINNED_EXAMPLE_ONLY", "OVERALL_MAPPING")
    _require(value_review.get("automatic_value_promotion"), "PROHIBITED", "VALUE_PROMOTION")
    _require(value_review.get("route_synthesis_or_guessing"), "PROHIBITED", "VALUE_ROUTE_GUESSING")

    equivalent = list(config["query_equivalent_control_names"])
    non_equivalent = list(config["non_equivalent_same_name_control_names"])
    all_names = list(config["all_same_name_query_control_names"])
    if set(equivalent) & set(non_equivalent):
        raise SiopePublicRuntimeQueryEquivalencePartitionDesignError(f"{ERROR}_PARTITION_OVERLAP")
    if set(equivalent) | set(non_equivalent) != set(all_names):
        raise SiopePublicRuntimeQueryEquivalencePartitionDesignError(f"{ERROR}_PARTITION_COVERAGE")
    if len(equivalent) != 7 or non_equivalent != ["acao"]:
        raise SiopePublicRuntimeQueryEquivalencePartitionDesignError(f"{ERROR}_PARTITION_CARDINALITY")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_QUERY_EQUIVALENCE_PARTITION_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "query_equivalent_control_names": equivalent,
        "query_equivalent_status": config["query_equivalent_disposition"],
        "non_equivalent_same_name_control_names": non_equivalent,
        "non_equivalent_same_name_status": config["non_equivalent_same_name_disposition"],
        "same_name_implies_value_equivalence": False,
        "same_name_implies_semantic_role_equivalence": False,
        "seven_control_generalization_status": config["seven_control_generalization_status"],
        "acao_value_origin_status": config["acao_value_origin_status"],
        "acao_query_semantics_status": config["acao_query_semantics_status"],
        "independent_public_example_required_before_generalization": True,
        "second_example_must_be_explicitly_proven_not_synthesized": True,
        "form_post_status": config["form_post_disposition"],
        "dynamic_route_contract_status": config["dynamic_route_contract_disposition"],
        "automatic_value_promotion": False,
        "route_synthesized_or_guessed": False,
        "dom_interaction_authorized": False,
        "post_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
