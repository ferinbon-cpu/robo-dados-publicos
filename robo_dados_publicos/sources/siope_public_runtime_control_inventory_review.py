from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_REVIEW"


class SiopePublicRuntimeControlInventoryReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeControlInventoryReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeControlInventoryReviewError(f"{ERROR}_{code}")


EXPECTED_CONTROLS = [
    {"id": "acao", "name": "acao", "tag_name": "input", "type": "hidden", "option_count": 0, "associated_stable_label": ""},
    {"id": "formato", "name": "formato", "tag_name": "input", "type": "hidden", "option_count": 0, "associated_stable_label": ""},
    {"id": "pag", "name": "pag", "tag_name": "input", "type": "hidden", "option_count": 0, "associated_stable_label": ""},
    {"id": "tp_relatorio", "name": "tp_relatorio", "tag_name": "select", "type": "select", "option_count": 3, "associated_stable_label": "Exibir:"},
    {"id": "num_ano", "name": "num_ano", "tag_name": "select", "type": "select", "option_count": 22, "associated_stable_label": "Ano:"},
    {"id": "num_peri", "name": "num_peri", "tag_name": "select", "type": "select", "option_count": 6, "associated_stable_label": ""},
    {"id": "cod_uf", "name": "cod_uf", "tag_name": "select", "type": "select", "option_count": 28, "associated_stable_label": "UF:"},
    {"id": "cod_muni", "name": "cod_muni", "tag_name": "select", "type": "select", "option_count": 418, "associated_stable_label": ""},
    {"id": "admin", "name": "admin", "tag_name": "select", "type": "select", "option_count": 1, "associated_stable_label": ""},
    {"id": "planilhas", "name": "planilhas", "tag_name": "select", "type": "select", "option_count": 2, "associated_stable_label": "Planilha:"},
    {"id": "descricaoItem", "name": "descricaoItem", "tag_name": "input", "type": "hidden", "option_count": 0, "associated_stable_label": ""},
    {"id": "", "name": "Submit", "tag_name": "input", "type": "button", "option_count": 0, "associated_stable_label": ""},
]


def validate_review_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_CONTROL_INVENTORY_REVIEW",
        "evidence_path": "docs/evidence/M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_RUN_1_0.8.0.json",
        "evidence_git_blob_sha": "d7273e36462829491d2f6b6236515635e5837b4e",
        "expected_prior_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_0_8_0",
        "expected_prior_status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY",
        "expected_run_id": 32879032646,
        "expected_run_number": 1,
        "expected_head_sha": "e27cabab4c3c4a3c1a5bc3849ef3d3a91a50d7c8",
        "expected_artifact_id": 9575050795,
        "expected_artifact_digest": "sha256:715ea05bd4dbac5cf58b3df7d50a9e8b591fcdb087be9a4c785dcc1d83fd1ea7",
        "expected_control_count": 12,
        "expected_associated_stable_label_control_count": 4,
        "expected_form_contract": {
            "scheme": "https",
            "host": "www.fnde.gov.br",
            "path": "/siope/dadosInformadosMunicipio.do",
            "method": "POST",
        },
        "stable_label_bindings": {
            "Exibir:": "tp_relatorio",
            "Ano:": "num_ano",
            "UF:": "cod_uf",
            "Planilha:": "planilhas",
        },
        "indexed_get_query_key_control_names": [
            "acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"
        ],
        "structurally_observed_select_names": [
            "tp_relatorio", "num_ano", "num_peri", "cod_uf", "cod_muni", "admin", "planilhas"
        ],
        "control_identity_disposition": "STRUCTURALLY_OBSERVED_NOT_VALUE_PROVEN",
        "stable_label_binding_disposition": "PROVEN_FOR_PINNED_PUBLIC_EXAMPLE",
        "form_post_disposition": "OBSERVED_STRUCTURAL_ONLY_NOT_AUTHORIZED",
        "dynamic_route_contract_disposition": "UNPROVEN_ZERO_CANDIDATES",
        "control_value_semantics": "UNPROVEN",
        "option_value_mapping": "UNPROVEN",
        "network_access": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "control_value_capture": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")


def _review_label_bindings(controls: list[dict], expected: dict[str, str]) -> None:
    observed = {
        control["associated_stable_label"]: control["name"]
        for control in controls
        if control.get("associated_stable_label")
    }
    _require(observed, expected, "STABLE_LABEL_BINDINGS")


def review_public_runtime_control_inventory(config: dict, evidence: dict) -> dict:
    validate_review_config(config)

    _require(evidence.get("gate_id"), config["expected_prior_gate_id"], "EVIDENCE_GATE_ID")
    _require(evidence.get("software_version"), config["software_version"], "EVIDENCE_VERSION")
    _require(evidence.get("release_status"), config["release_status"], "EVIDENCE_RELEASE_STATUS")

    run = evidence.get("run") or {}
    _require(run.get("id"), config["expected_run_id"], "RUN_ID")
    _require(run.get("number"), config["expected_run_number"], "RUN_NUMBER")
    _require(run.get("event"), "workflow_dispatch", "RUN_EVENT")
    _require(run.get("status"), "completed", "RUN_STATUS")
    _require(run.get("conclusion"), "success", "RUN_CONCLUSION")
    _require(run.get("head_branch"), "main", "RUN_HEAD_BRANCH")
    _require(run.get("head_sha"), config["expected_head_sha"], "RUN_HEAD_SHA")

    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), 456, "QA_UNIT_TEST_COUNT")
    _require(qa.get("unit_failures"), 0, "QA_UNIT_FAILURES")
    _require(qa.get("historical_regressions"), 109, "QA_REGRESSION_COUNT")
    _require(qa.get("historical_regression_failures"), 0, "QA_REGRESSION_FAILURES")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["expected_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["expected_artifact_digest"], "ARTIFACT_DIGEST")

    result = evidence.get("result") or {}
    _require(result.get("status"), config["expected_prior_status"], "PRIOR_STATUS")
    _require(result.get("page_surface_verified"), True, "PUBLIC_SURFACE")
    _require(result.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(result.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(result.get("candidate_shape_count"), 0, "CANDIDATE_COUNT")
    _require(result.get("candidate_shapes"), [], "CANDIDATE_SHAPES")
    _require(result.get("dynamic_candidate_network_sent"), False, "DYNAMIC_NETWORK_SENT")
    _require(result.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    _require(result.get("human_challenge_active"), False, "HUMAN_CHALLENGE")
    _require(result.get("navigation_after_initial_document"), False, "SECOND_NAVIGATION")
    _require(result.get("dom_interaction_performed"), False, "DOM_INTERACTION")
    _require(result.get("form_submission"), False, "FORM_SUBMISSION")
    _require(result.get("control_identity_promoted"), False, "CONTROL_IDENTITY_PROMOTION")

    for key in (
        "control_values_captured",
        "option_text_captured",
        "option_values_captured",
        "html_captured",
        "free_text_captured",
        "query_values_persisted",
        "request_body_persisted",
        "response_body_persisted",
        "pilot_limeira_values_sent",
        "authentication_performed",
        "captcha_bypass",
        "cookies_captured",
        "credentials_captured",
        "head_request_performed",
        "artifact_downloaded",
        "collection_authorized",
        "processing_authorized",
        "recurrence_authorized",
        "schedule_enabled",
    ):
        _require(result.get(key), False, key.upper())
    _require(result.get("remote_writes"), "NONE", "REMOTE_WRITES")

    _require(result.get("control_count"), config["expected_control_count"], "CONTROL_COUNT")
    _require(
        result.get("associated_stable_label_control_count"),
        config["expected_associated_stable_label_control_count"],
        "STABLE_LABEL_CONTROL_COUNT",
    )
    _require(result.get("form_contract"), config["expected_form_contract"], "FORM_CONTRACT")
    _require(result.get("controls_structural_summary"), EXPECTED_CONTROLS, "CONTROL_STRUCTURAL_SUMMARY")
    _require(result.get("next_gate"), config["gate_id"], "PRIOR_NEXT_GATE")

    controls = list(result.get("controls_structural_summary") or [])
    _review_label_bindings(controls, config["stable_label_bindings"])

    observed_names = {control.get("name") for control in controls}
    expected_indexed_names = set(config["indexed_get_query_key_control_names"])
    if not expected_indexed_names.issubset(observed_names):
        raise SiopePublicRuntimeControlInventoryReviewError(f"{ERROR}_INDEXED_GET_QUERY_KEY_CONTROL_COVERAGE")

    select_names = [control["name"] for control in controls if control.get("tag_name") == "select"]
    _require(select_names, config["structurally_observed_select_names"], "SELECT_NAMES")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("structural_control_inventory_proven"), True, "INTERPRETATION_STRUCTURAL_INVENTORY")
    _require(interpretation.get("control_values_proven"), False, "INTERPRETATION_CONTROL_VALUES")
    _require(interpretation.get("control_semantics_fully_proven"), False, "INTERPRETATION_SEMANTICS")
    _require(interpretation.get("form_post_observed_structurally"), True, "INTERPRETATION_FORM_POST")
    _require(interpretation.get("post_authorized"), False, "INTERPRETATION_POST_AUTH")
    _require(interpretation.get("dynamic_data_route_proven"), False, "INTERPRETATION_DYNAMIC_ROUTE")
    _require(interpretation.get("automatic_control_identity_promotion"), "PROHIBITED", "INTERPRETATION_PROMOTION")
    _require(interpretation.get("automatic_post_or_submit"), "PROHIBITED", "INTERPRETATION_POST_SUBMIT")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "evidence_run_id": config["expected_run_id"],
        "evidence_artifact_id": config["expected_artifact_id"],
        "control_count": config["expected_control_count"],
        "structurally_observed_select_names": config["structurally_observed_select_names"],
        "stable_label_bindings": config["stable_label_bindings"],
        "indexed_get_query_key_control_names": config["indexed_get_query_key_control_names"],
        "indexed_get_query_key_controls_structurally_covered": True,
        "control_identity_status": config["control_identity_disposition"],
        "stable_label_binding_status": config["stable_label_binding_disposition"],
        "control_value_semantics": config["control_value_semantics"],
        "option_value_mapping": config["option_value_mapping"],
        "form_contract": config["expected_form_contract"],
        "form_post_status": config["form_post_disposition"],
        "post_authorized": False,
        "dynamic_route_contract_status": config["dynamic_route_contract_disposition"],
        "dom_interaction_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
