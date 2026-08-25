from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_DISCOVERY_DESIGN"


class SiopePublicIndexedGetSecondExampleDiscoveryDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicIndexedGetSecondExampleDiscoveryDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicIndexedGetSecondExampleDiscoveryDesignError(f"{ERROR}_{code}")


def validate_discovery_design(config: dict, partition: dict, public_config: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_DISCOVERY_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_EXPLICIT_SECOND_PUBLIC_EXAMPLE_DISCOVERY_DESIGN",
        "partition_design_config_path": "config/source_expansion.siope_public_runtime_query_equivalence_partition_design.json",
        "public_runtime_config_path": "config/source_expansion.siope_public_get_runtime_route_diagnostics_gate.json",
        "prerequisite_partition_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_QUERY_EQUIVALENCE_PARTITION_DESIGN_0_8_0",
        "required_scheme": "https",
        "required_host": "www.fnde.gov.br",
        "required_path": "/siope/dadosInformadosMunicipio.do",
        "required_query_keys": ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        "candidate_must_be_explicit_full_url_from_public_source": True,
        "candidate_public_source_reference_required": True,
        "candidate_must_not_equal_pinned_example": True,
        "candidate_must_be_non_limeira": True,
        "candidate_must_not_be_constructed_by_parameter_substitution": True,
        "candidate_must_not_be_synthesized_or_guessed": True,
        "candidate_query_key_set_must_match_current_contract": True,
        "legacy_schema_examples_are_not_current_contract_evidence": True,
        "base_surface_without_complete_query_is_not_second_example": True,
        "candidate_selected": False,
        "candidate_status": "UNRESOLVED_NO_EXPLICIT_ELIGIBLE_SECOND_EXAMPLE_PINNED",
        "candidate_url": None,
        "candidate_source_reference": None,
        "candidate_full_url_persistence": "PROHIBITED_UNTIL_CANDIDATE_REVIEW",
        "runtime_gate_creation_authorized": False,
        "cross_example_generalization_authorized": False,
        "seven_control_generalization_status": "UNPROVEN_BEYOND_PINNED_PUBLIC_EXAMPLE",
        "acao_query_semantics_status": "UNPROVEN",
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
        "query_value_capture": "PROHIBITED",
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
        "next_gate_when_candidate_exists": "M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_CANDIDATE_REVIEW_0_8_0",
        "next_state_without_candidate": "BLOCKED_PENDING_EXPLICIT_SECOND_PUBLIC_EXAMPLE",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(partition.get("gate_id"), config["prerequisite_partition_gate_id"], "PARTITION_GATE")
    _require(partition.get("next_gate"), config["gate_id"], "PARTITION_NEXT_GATE")
    _require(partition.get("query_equivalent_control_names"), ["admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"], "PARTITION_EQUIVALENT_CONTROLS")
    _require(partition.get("non_equivalent_same_name_control_names"), ["acao"], "PARTITION_NON_EQUIVALENT")
    _require(partition.get("seven_control_generalization_status"), "UNPROVEN_BEYOND_PINNED_PUBLIC_EXAMPLE", "PARTITION_GENERALIZATION")
    _require(partition.get("independent_public_example_required_before_generalization"), True, "PARTITION_SECOND_EXAMPLE_REQUIRED")
    _require(partition.get("second_example_must_be_explicitly_proven_not_synthesized"), True, "PARTITION_EXPLICIT_REQUIRED")

    _require(public_config.get("gate_id"), "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0", "PUBLIC_GATE")
    _require(public_config.get("expected_scheme"), config["required_scheme"], "PUBLIC_SCHEME")
    _require(public_config.get("expected_host"), config["required_host"], "PUBLIC_HOST")
    _require(public_config.get("expected_path"), config["required_path"], "PUBLIC_PATH")
    _require(public_config.get("expected_query_keys"), config["required_query_keys"], "PUBLIC_QUERY_KEYS")
    pinned = str(public_config.get("public_indexed_example_url", ""))
    if not pinned:
        raise SiopePublicIndexedGetSecondExampleDiscoveryDesignError(f"{ERROR}_PINNED_EXAMPLE_REQUIRED")
    if "352690" in pinned:
        raise SiopePublicIndexedGetSecondExampleDiscoveryDesignError(f"{ERROR}_PINNED_EXAMPLE_MUST_BE_NON_PILOT")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_INDEXED_GET_SECOND_EXAMPLE_DISCOVERY_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "network_called": False,
        "required_contract": {
            "scheme": config["required_scheme"],
            "host": config["required_host"],
            "path": config["required_path"],
            "query_keys": config["required_query_keys"],
        },
        "candidate_selected": False,
        "candidate_status": config["candidate_status"],
        "candidate_url_persisted": False,
        "candidate_source_reference_persisted": False,
        "legacy_schema_eligible": False,
        "base_surface_without_complete_query_eligible": False,
        "parameter_substitution_authorized": False,
        "route_synthesized_or_guessed": False,
        "runtime_gate_creation_authorized": False,
        "cross_example_generalization_authorized": False,
        "seven_control_generalization_status": config["seven_control_generalization_status"],
        "acao_query_semantics_status": config["acao_query_semantics_status"],
        "post_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate_when_candidate_exists": config["next_gate_when_candidate_exists"],
        "next_state": config["next_state_without_candidate"],
    }
