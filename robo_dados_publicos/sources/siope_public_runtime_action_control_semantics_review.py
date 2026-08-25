from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_REVIEW"


class SiopePublicRuntimeActionControlSemanticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeActionControlSemanticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeActionControlSemanticsReviewError(f"{ERROR}_{code}")


def validate_review_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_ACTION_CONTROL_SEMANTICS_REVIEW",
        "evidence_path": "docs/evidence/M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_RUN_1_0.8.0.json",
        "evidence_git_blob_sha": "fa4dc080f843cdf73b1406f69fd81e55e5672e2f",
        "expected_prior_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_0_8_0",
        "expected_prior_status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS",
        "expected_runtime_status": "PUBLIC_INDEXED_GET_ACTION_CONTROL_BOOLEAN_RELATIONS_OBSERVED_PASSIVELY",
        "expected_run_id": 32888054228,
        "expected_run_number": 1,
        "expected_head_sha": "682ee334e35ec0ff24092d8d46423387ceba2cb4",
        "expected_job_id": 97933084498,
        "expected_artifact_id": 9578344654,
        "expected_artifact_digest": "sha256:e54574588f1a7db0035dff287431e6fccfffe85bd9c8b1f645fab1ddbc1261f4",
        "target_control_name": "acao",
        "expected_boolean_observation": {
            "control_present": True,
            "control_is_hidden_input": True,
            "query_key_present": True,
            "value_attribute_present": True,
            "property_equals_query": False,
            "attribute_equals_query": False,
            "property_equals_attribute": True,
        },
        "relation_stability_disposition": "STABLE_ACROSS_OBSERVED_WINDOW",
        "internal_consistency_disposition": "PROPERTY_EQUALS_ATTRIBUTE_ON_BOTH_OBSERVATIONS",
        "query_equivalence_disposition": "PROPERTY_AND_ATTRIBUTE_DIFFER_FROM_QUERY_ON_BOTH_OBSERVATIONS",
        "client_side_mutation_disposition": "NOT_OBSERVED_DURING_MEASURED_WINDOW",
        "value_origin_disposition": "UNPROVEN",
        "value_semantics_disposition": "STABLE_INTERNAL_VALUE_DIFFERENT_FROM_QUERY_ON_PINNED_PUBLIC_EXAMPLE",
        "query_action_semantics_disposition": "UNPROVEN",
        "form_post_disposition": "OBSERVED_STRUCTURAL_ONLY_NOT_AUTHORIZED",
        "dynamic_route_contract_disposition": "UNPROVEN_ZERO_CANDIDATES",
        "network_access": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "control_mutation": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_QUERY_EQUIVALENCE_PARTITION_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")


def review_action_control_semantics(config: dict, evidence: dict) -> dict:
    validate_review_config(config)

    _require(evidence.get("gate_id"), config["expected_prior_gate_id"], "EVIDENCE_GATE_ID")
    _require(evidence.get("software_version"), config["software_version"], "EVIDENCE_VERSION")
    _require(evidence.get("release_status"), config["release_status"], "EVIDENCE_RELEASE_STATUS")

    run = evidence.get("run") or {}
    _require(run.get("id"), config["expected_run_id"], "RUN_ID")
    _require(run.get("number"), config["expected_run_number"], "RUN_NUMBER")
    _require(run.get("event"), "workflow_dispatch", "RUN_EVENT")
    _require(run.get("branch"), "main", "RUN_BRANCH")
    _require(run.get("head_sha"), config["expected_head_sha"], "RUN_HEAD_SHA")
    _require(run.get("status"), "completed", "RUN_STATUS")
    _require(run.get("conclusion"), "success", "RUN_CONCLUSION")
    _require(run.get("job_id"), config["expected_job_id"], "RUN_JOB_ID")

    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), 512, "QA_UNIT_TESTS")
    _require(qa.get("unit_test_failures"), 0, "QA_UNIT_FAILURES")
    _require(qa.get("historical_regressions"), 109, "QA_REGRESSIONS")
    _require(qa.get("historical_regression_passes"), 109, "QA_REGRESSION_PASSES")
    _require(qa.get("historical_regression_failures"), 0, "QA_REGRESSION_FAILURES")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["expected_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["expected_artifact_digest"], "ARTIFACT_DIGEST")

    result = evidence.get("result") or {}
    _require(result.get("status"), config["expected_prior_status"], "PRIOR_STATUS")
    _require(result.get("runtime_status"), config["expected_runtime_status"], "RUNTIME_STATUS")
    _require(result.get("target_control_name"), config["target_control_name"], "TARGET_CONTROL")
    _require(result.get("page_surface_verified"), True, "PUBLIC_SURFACE")
    _require(result.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(result.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(result.get("candidate_shape_count"), 0, "CANDIDATE_COUNT")
    _require(result.get("candidate_shapes"), [], "CANDIDATE_SHAPES")
    _require(result.get("first_observation"), config["expected_boolean_observation"], "FIRST_OBSERVATION")
    _require(result.get("final_observation"), config["expected_boolean_observation"], "FINAL_OBSERVATION")
    _require(result.get("boolean_relation_state_changed"), False, "RELATION_STATE_CHANGED")
    _require(result.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    _require(result.get("human_challenge_active"), False, "HUMAN_CHALLENGE")
    _require(result.get("remote_writes"), "NONE", "REMOTE_WRITES")

    for key in (
        "actual_control_value_returned",
        "actual_query_value_returned",
        "actual_attribute_value_returned",
        "script_source_captured",
        "html_returned",
        "free_text_returned",
        "dom_interaction_performed",
        "control_mutation_performed",
        "form_submission",
        "post_request_performed",
        "navigation_after_initial_document",
        "pilot_limeira_values_sent",
        "dynamic_candidate_network_sent",
        "captcha_bypass",
        "authentication_performed",
        "credentials_captured",
        "cookies_captured",
        "request_body_persisted",
        "response_body_persisted",
        "query_values_persisted",
        "head_request_performed",
        "artifact_downloaded",
        "route_synthesized_or_guessed",
        "automatic_value_promotion",
        "collection_authorized",
        "processing_authorized",
        "recurrence_authorized",
        "schedule_enabled",
    ):
        _require(result.get(key), False, key.upper())
    _require(result.get("next_gate"), config["gate_id"], "PRIOR_NEXT_GATE")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("acao_boolean_relation_vector_stable_across_observed_window"), True, "INTERPRETATION_STABILITY")
    _require(interpretation.get("acao_property_equals_attribute_on_both_observations"), True, "INTERPRETATION_INTERNAL_EQUALITY")
    _require(interpretation.get("acao_property_equals_query_on_both_observations"), False, "INTERPRETATION_PROPERTY_QUERY")
    _require(interpretation.get("acao_attribute_equals_query_on_both_observations"), False, "INTERPRETATION_ATTRIBUTE_QUERY")
    _require(interpretation.get("client_side_mutation_during_observed_window"), "NOT_OBSERVED", "INTERPRETATION_MUTATION")
    _require(interpretation.get("acao_value_origin"), "UNPROVEN", "INTERPRETATION_ORIGIN")
    _require(interpretation.get("acao_value_semantics"), config["value_semantics_disposition"], "INTERPRETATION_VALUE_SEMANTICS")
    _require(interpretation.get("query_value_semantics_for_acao"), "UNPROVEN", "INTERPRETATION_QUERY_SEMANTICS")
    _require(interpretation.get("post_authorized"), False, "INTERPRETATION_POST")
    _require(interpretation.get("automatic_value_promotion"), "PROHIBITED", "INTERPRETATION_PROMOTION")
    _require(interpretation.get("route_synthesis_or_guessing"), "PROHIBITED", "INTERPRETATION_ROUTE_GUESSING")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "evidence_run_id": config["expected_run_id"],
        "evidence_artifact_id": config["expected_artifact_id"],
        "target_control_name": config["target_control_name"],
        "relation_stability_status": config["relation_stability_disposition"],
        "internal_consistency_status": config["internal_consistency_disposition"],
        "query_equivalence_status": config["query_equivalence_disposition"],
        "client_side_mutation_status": config["client_side_mutation_disposition"],
        "value_origin_status": config["value_origin_disposition"],
        "value_semantics_status": config["value_semantics_disposition"],
        "query_action_semantics_status": config["query_action_semantics_disposition"],
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
