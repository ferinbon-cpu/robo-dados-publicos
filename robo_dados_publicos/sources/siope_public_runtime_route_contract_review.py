from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW"


class SiopePublicRuntimeRouteContractReviewError(RuntimeError):
    pass


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def review_runtime_route_contract(config: dict, evidence: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_EVIDENCE_CONTRACT_REVIEW",
        "required_runtime_status": "PASS_M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS",
        "required_initial_document_send_count": 1,
        "required_page_surface_verified": True,
        "required_candidate_shape_count": 0,
        "dynamic_route_status": "UNPROVEN_ZERO_RUNTIME_CANDIDATES",
        "observed_document_route_role": "SOLE_OBSERVED_SAME_HOST_DATA_SURFACE_CANDIDATE",
        "observed_document_route_status": "CANDIDATE_NOT_AUTHORIZED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_PUBLIC_INDEXED_GET_ACQUISITION_CONTRACT_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_CONFIG_{key.upper()}")

    result = evidence.get("result") or {}
    interpretation = evidence.get("interpretation") or {}
    if result.get("status") != config["required_runtime_status"]:
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_RUNTIME_STATUS")
    if result.get("page_surface_verified") is not True:
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_SURFACE")
    if int(result.get("initial_document_continued_count", 0)) != 1 or result.get("initial_document_network_sent") is not True:
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_INITIAL_DOCUMENT")
    if int(result.get("candidate_shape_count", -1)) != 0 or list(result.get("candidate_shapes") or []):
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_ZERO_CANDIDATE_CONTRACT")
    if result.get("dynamic_candidate_network_sent") is not False:
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_DYNAMIC_NETWORK_SENT")
    if interpretation.get("dynamic_data_route_proven") is not False:
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_DYNAMIC_ROUTE_INTERPRETATION")
    if interpretation.get("route_synthesis_or_guessing") != "PROHIBITED":
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_ROUTE_GUESSING")

    closed_flags = [
        "pilot_limeira_values_sent",
        "form_submission",
        "captcha_bypass",
        "authentication_performed",
        "request_body_persisted",
        "response_body_persisted",
        "query_values_persisted",
        "artifact_downloaded",
        "collection_authorized",
        "processing_authorized",
        "recurrence_authorized",
        "schedule_enabled",
    ]
    for key in closed_flags:
        if result.get(key) is not False:
            raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_SAFETY_{key.upper()}")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "runtime_evidence_status": result["status"],
        "public_indexed_document_runtime_verified": True,
        "dynamic_route_status": config["dynamic_route_status"],
        "dynamic_route_proven": False,
        "candidate_shape_count": 0,
        "route_synthesis_or_guessing": "PROHIBITED",
        "observed_document_route_role": config["observed_document_route_role"],
        "observed_document_route_status": config["observed_document_route_status"],
        "pilot_limeira_values_send": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "remote_writes": "NONE",
        "next_gate": config["next_gate"],
    }


def run_review(config_path: str | Path, evidence_path: str | Path | None = None) -> dict:
    config = _load_json(config_path)
    evidence = _load_json(evidence_path or config["evidence_path"])
    return review_runtime_route_contract(config, evidence)
