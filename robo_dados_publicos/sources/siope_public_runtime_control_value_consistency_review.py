from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW"


class SiopePublicRuntimeControlValueConsistencyReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeControlValueConsistencyReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeControlValueConsistencyReviewError(f"{ERROR}_{code}")


def validate_review_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_BOOLEAN_VALUE_CONSISTENCY_REVIEW",
        "evidence_path": "docs/evidence/M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_ATTEMPT_1_0.8.0.json",
        "inventory_evidence_path": "docs/evidence/M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_RUN_1_0.8.0.json",
        "expected_prior_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_0_8_0",
        "expected_prior_status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS",
        "expected_run_id": 32883743062,
        "expected_run_number": 1,
        "expected_head_sha": "9233b193b2de63ec073c89e2605daa9b26fcd816",
        "expected_artifact_id": 9576794184,
        "expected_artifact_digest": "sha256:8389334a4ee0443810d3836a2bd51e9bfe775621090e567cff73326e8490cd59",
        "expected_comparison_count": 8,
        "expected_control_names": ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        "matched_control_names": ["admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        "mismatched_control_names": ["acao"],
        "acao_expected_structure": {"id": "acao", "name": "acao", "tag_name": "input", "type": "hidden", "option_count": 0, "associated_stable_label": ""},
        "matched_value_consistency_disposition": "OBSERVED_MATCH_ON_PINNED_PUBLIC_EXAMPLE_ONLY",
        "acao_value_semantics_disposition": "UNPROVEN_MISMATCH_ON_PINNED_PUBLIC_EXAMPLE",
        "overall_value_mapping_disposition": "PARTIAL_7_OF_8_PINNED_EXAMPLE_ONLY",
        "form_post_disposition": "OBSERVED_STRUCTURAL_ONLY_NOT_AUTHORIZED",
        "dynamic_route_contract_disposition": "UNPROVEN_ZERO_CANDIDATES",
        "automatic_value_promotion": "PROHIBITED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "network_access": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "control_value_capture": "PROHIBITED",
        "query_value_capture": "PROHIBITED",
        "option_text_capture": "PROHIBITED",
        "option_value_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "free_text_capture": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")


def review_public_runtime_control_value_consistency(config: dict, evidence: dict, inventory_evidence: dict) -> dict:
    validate_review_config(config)

    _require(evidence.get("gate_id"), config["expected_prior_gate_id"], "EVIDENCE_GATE")
    _require(evidence.get("software_version"), config["software_version"], "EVIDENCE_VERSION")

    run = evidence.get("run") or {}
    _require(run.get("id"), config["expected_run_id"], "RUN_ID")
    _require(run.get("number"), config["expected_run_number"], "RUN_NUMBER")
    _require(run.get("event"), "workflow_dispatch", "RUN_EVENT")
    _require(run.get("branch"), "main", "RUN_BRANCH")
    _require(run.get("head_sha"), config["expected_head_sha"], "RUN_HEAD_SHA")
    _require(run.get("status"), "completed", "RUN_STATUS")
    _require(run.get("conclusion"), "success", "RUN_CONCLUSION")

    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), 486, "QA_UNIT_TESTS")
    _require(qa.get("unit_test_failures"), 0, "QA_UNIT_FAILURES")
    _require(qa.get("historical_regressions"), 109, "QA_REGRESSIONS")
    _require(qa.get("historical_regression_passes"), 109, "QA_REGRESSION_PASSES")
    _require(qa.get("historical_regression_failures"), 0, "QA_REGRESSION_FAILURES")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["expected_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["expected_artifact_digest"], "ARTIFACT_DIGEST")

    result = evidence.get("result") or {}
    _require(result.get("status"), config["expected_prior_status"], "PRIOR_STATUS")
    _require(result.get("comparison_count"), config["expected_comparison_count"], "COMPARISON_COUNT")
    _require(result.get("all_controls_present"), True, "ALL_CONTROLS_PRESENT")
    _require(result.get("all_query_keys_present"), True, "ALL_QUERY_KEYS_PRESENT")
    _require(result.get("all_values_match_query"), False, "ALL_VALUES_MATCH")
    _require(result.get("comparison_result_boolean_only"), True, "BOOLEAN_ONLY")
    _require(result.get("page_surface_verified"), True, "PUBLIC_SURFACE")
    _require(result.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(result.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(result.get("candidate_shape_count"), 0, "CANDIDATE_COUNT")
    _require(result.get("candidate_shapes"), [], "CANDIDATE_SHAPES")
    _require(result.get("dynamic_candidate_network_sent"), False, "DYNAMIC_NETWORK_SENT")
    _require(result.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    _require(result.get("human_challenge_active"), False, "HUMAN_CHALLENGE")
    _require(result.get("next_gate"), config["gate_id"], "PRIOR_NEXT_GATE")

    for key in (
        "actual_control_values_returned", "actual_query_values_returned", "option_text_returned", "option_values_returned",
        "html_returned", "free_text_returned", "dom_interaction_performed", "form_submission",
        "post_request_performed", "navigation_after_initial_document", "pilot_limeira_values_sent", "captcha_bypass",
        "authentication_performed", "credentials_captured", "cookies_captured", "request_body_persisted",
        "response_body_persisted", "query_values_persisted", "head_request_performed", "artifact_downloaded",
        "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled",
    ):
        _require(result.get(key), False, key.upper())
    _require(result.get("remote_writes"), "NONE", "REMOTE_WRITES")

    comparisons = list(result.get("comparison_results") or [])
    _require([row.get("control_name") for row in comparisons], config["expected_control_names"], "CONTROL_NAMES")
    for row in comparisons:
        _require(set(row.keys()), {"control_name", "control_present", "query_key_present", "value_matches_query"}, "COMPARISON_FIELDS")
        _require(row.get("control_present"), True, f"{row.get('control_name')}_CONTROL_PRESENT")
        _require(row.get("query_key_present"), True, f"{row.get('control_name')}_QUERY_PRESENT")

    matched = [row["control_name"] for row in comparisons if row["value_matches_query"] is True]
    mismatched = [row["control_name"] for row in comparisons if row["value_matches_query"] is False]
    _require(matched, config["matched_control_names"], "MATCHED_CONTROLS")
    _require(mismatched, config["mismatched_control_names"], "MISMATCHED_CONTROLS")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("seven_of_eight_controls_match_current_query"), True, "INTERPRETATION_SEVEN_MATCH")
    _require(interpretation.get("mismatching_control_names"), config["mismatched_control_names"], "INTERPRETATION_MISMATCH")
    _require(interpretation.get("acao_value_semantics"), config["acao_value_semantics_disposition"], "INTERPRETATION_ACAO")
    _require(interpretation.get("other_seven_value_consistency"), config["matched_value_consistency_disposition"], "INTERPRETATION_SEVEN")
    _require(interpretation.get("form_post_authorized"), False, "INTERPRETATION_POST")
    _require(interpretation.get("route_synthesis_or_guessing"), "PROHIBITED", "INTERPRETATION_ROUTE_GUESS")
    _require(interpretation.get("automatic_value_promotion"), "PROHIBITED", "INTERPRETATION_VALUE_PROMOTION")

    inventory_result = (inventory_evidence.get("result") or {})
    structures = list(inventory_result.get("controls_structural_summary") or [])
    acao_rows = [row for row in structures if row.get("name") == "acao"]
    _require(len(acao_rows), 1, "ACAO_STRUCTURE_COUNT")
    _require(acao_rows[0], config["acao_expected_structure"], "ACAO_STRUCTURE")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "evidence_run_id": config["expected_run_id"],
        "evidence_artifact_id": config["expected_artifact_id"],
        "comparison_count": config["expected_comparison_count"],
        "matched_control_names": matched,
        "mismatched_control_names": mismatched,
        "matched_value_consistency_status": config["matched_value_consistency_disposition"],
        "acao_control_structure": "HIDDEN_INPUT_STRUCTURALLY_OBSERVED",
        "acao_value_semantics_status": config["acao_value_semantics_disposition"],
        "overall_value_mapping_status": config["overall_value_mapping_disposition"],
        "form_post_status": config["form_post_disposition"],
        "dynamic_route_contract_status": config["dynamic_route_contract_disposition"],
        "automatic_value_promotion": False,
        "route_synthesized_or_guessed": False,
        "post_authorized": False,
        "dom_interaction_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
