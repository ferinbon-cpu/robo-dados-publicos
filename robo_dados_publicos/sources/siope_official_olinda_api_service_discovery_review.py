from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_REVIEW"


class SiopeOfficialOlindaApiServiceDiscoveryReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiServiceDiscoveryReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiServiceDiscoveryReviewError(f"{ERROR}_{code}")


def validate_review_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_OLINDA_SERVICE_DISCOVERY_STOP_REVIEW",
        "evidence_path": "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_ATTEMPT_1_0.8.0.json",
        "evidence_git_blob_sha": "10288f69a6d7cddb0df5bfe51493ac2fdc717877",
        "expected_prior_gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_0_8_0",
        "expected_prior_status": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY",
        "expected_error_code": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_CANDIDATE_ABSENT",
        "expected_run_id": 32896802313,
        "expected_run_number": 1,
        "expected_head_sha": "57f521a222f5f2051cf1a43c364121b8ca8f1c07",
        "expected_job_id": 97961261207,
        "expected_workflow_conclusion": "failure",
        "expected_artifact_id": 9581521897,
        "expected_artifact_digest": "sha256:7a488dca4414c0528c98398676c7df9683dd29be5da7ea2a72b4ec10228e0635",
        "expected_unit_tests": 559,
        "expected_historical_regressions": 109,
        "expected_http_status": 200,
        "expected_content_type": "application/xml",
        "expected_collection_names": [
            "_Receita_Siope",
            "_Indicadores_Siope",
            "_Despesas_Siope",
            "_Despesas_Funcao_Educacao_Siope",
            "_Dados_Gerais_Siope_Dados_Responsaveis",
            "_Informacoes_Complementares_Siope",
            "_Dados_Gerais_Siope",
            "_Remuneracao_Siope",
        ],
        "rejected_reference_candidate": "Dados_Gerais_Siope",
        "observed_target_collection": "_Dados_Gerais_Siope",
        "service_root_disposition": "PROVEN_PUBLIC_OFFICIAL_SERVICE_ROOT_ON_PINNED_RUN",
        "service_document_disposition": "PARSEABLE_XML_EIGHT_COLLECTIONS_OBSERVED",
        "reference_candidate_disposition": "REJECTED_NAME_MISMATCH",
        "observed_target_collection_disposition": "STRUCTURALLY_DECLARED_IN_OFFICIAL_SERVICE_DOCUMENT",
        "all_collection_names_disposition": "OBSERVED_SERVICE_DOCUMENT_NAMES_ONLY",
        "resource_call_disposition": "NOT_CALLED",
        "resource_schema_disposition": "UNPROVEN",
        "parameter_semantics_disposition": "UNPROVEN",
        "network_access": "PROHIBITED",
        "resource_get": "PROHIBITED",
        "query_parameters": "PROHIBITED",
        "request_body": "PROHIBITED",
        "follow_redirects": "PROHIBITED",
        "follow_service_links": "PROHIBITED",
        "browser_execution": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "authentication": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "response_body_persistence": "PROHIBITED",
        "raw_response_persistence": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_RESOURCE_CONTRACT_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")


def review_service_discovery(config: dict, evidence: dict) -> dict:
    validate_review_config(config)

    _require(evidence.get("gate_id"), config["expected_prior_gate_id"], "EVIDENCE_GATE_ID")
    _require(evidence.get("attempt"), 1, "ATTEMPT")
    _require(evidence.get("workflow_run_id"), config["expected_run_id"], "RUN_ID")
    _require(evidence.get("workflow_run_number"), config["expected_run_number"], "RUN_NUMBER")
    _require(evidence.get("workflow_event"), "workflow_dispatch", "RUN_EVENT")
    _require(evidence.get("workflow_branch"), "main", "RUN_BRANCH")
    _require(evidence.get("head_sha"), config["expected_head_sha"], "RUN_HEAD_SHA")
    _require(evidence.get("job_id"), config["expected_job_id"], "JOB_ID")
    _require(evidence.get("workflow_conclusion"), config["expected_workflow_conclusion"], "WORKFLOW_CONCLUSION")

    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), config["expected_unit_tests"], "QA_UNIT_TESTS")
    _require(qa.get("unit_failures"), 0, "QA_UNIT_FAILURES")
    _require(qa.get("historical_regressions"), config["expected_historical_regressions"], "QA_REGRESSIONS")
    _require(qa.get("historical_regression_failures"), 0, "QA_REGRESSION_FAILURES")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["expected_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["expected_artifact_digest"], "ARTIFACT_DIGEST")

    result = evidence.get("result") or {}
    _require(result.get("status"), config["expected_prior_status"], "PRIOR_STATUS")
    _require(result.get("error_code"), config["expected_error_code"], "PRIOR_ERROR_CODE")
    _require(result.get("network_scope"), "EXACT_ONE_GET_OFFICIAL_SERVICE_ROOT_ONLY", "NETWORK_SCOPE")
    _require(result.get("http_status"), config["expected_http_status"], "HTTP_STATUS")
    _require(result.get("content_type"), config["expected_content_type"], "CONTENT_TYPE")
    _require(result.get("service_document_parseable"), True, "SERVICE_DOCUMENT_PARSEABLE")
    _require(result.get("collection_name_count"), 8, "COLLECTION_COUNT")
    _require(result.get("collection_names"), config["expected_collection_names"], "COLLECTION_NAMES")
    _require(result.get("original_reference_candidate"), config["rejected_reference_candidate"], "REFERENCE_CANDIDATE")
    _require(result.get("original_reference_candidate_present"), False, "REFERENCE_CANDIDATE_PRESENT")
    _require(result.get("observed_similar_collection"), config["observed_target_collection"], "OBSERVED_TARGET_COLLECTION")

    safety = evidence.get("safety") or {}
    for key in (
        "pilot_limeira_values_sent",
        "collection_authorized",
        "processing_authorized",
        "recurrence_authorized",
        "schedule_enabled",
        "request_body_sent",
        "redirect_followed",
        "service_link_followed",
        "authentication_performed",
        "captcha_bypass",
        "artifact_downloaded",
        "query_values_persisted",
        "raw_response_persisted",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "SAFETY_REMOTE_WRITES")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("service_root_reachable"), True, "INTERPRETATION_SERVICE_ROOT")
    _require(interpretation.get("service_document_contract_observed"), True, "INTERPRETATION_SERVICE_DOCUMENT")
    _require(interpretation.get("reference_candidate_name_correct"), False, "INTERPRETATION_REFERENCE_CANDIDATE")
    _require(interpretation.get("observed_collection_name_may_be_promoted_without_review"), False, "INTERPRETATION_PROMOTION")
    _require(interpretation.get("collection_request_authorized"), False, "INTERPRETATION_COLLECTION_REQUEST")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "evidence_run_id": config["expected_run_id"],
        "evidence_artifact_id": config["expected_artifact_id"],
        "service_root_status": config["service_root_disposition"],
        "service_document_status": config["service_document_disposition"],
        "reference_candidate_status": config["reference_candidate_disposition"],
        "rejected_reference_candidate": config["rejected_reference_candidate"],
        "observed_target_collection": config["observed_target_collection"],
        "observed_target_collection_status": config["observed_target_collection_disposition"],
        "all_collection_names_status": config["all_collection_names_disposition"],
        "resource_call_status": config["resource_call_disposition"],
        "resource_schema_status": config["resource_schema_disposition"],
        "parameter_semantics_status": config["parameter_semantics_disposition"],
        "route_synthesized_or_guessed": False,
        "automatic_value_promotion": False,
        "resource_get_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
