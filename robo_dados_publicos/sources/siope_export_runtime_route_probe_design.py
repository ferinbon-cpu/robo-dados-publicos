from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


class SiopeRuntimeRouteProbeDesignError(RuntimeError):
    pass


def validate_runtime_route_probe_design(config: dict) -> dict:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "DESIGN_ONLY_NO_BROWSER_EXECUTION",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_download_or_install": "PROHIBITED",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "browser_persistence": "PROHIBITED",
        "initial_navigation_method": "GET",
        "cross_origin_initial_requests": "ABORT",
        "export_control_text": "Exportar artefato",
        "max_clicks": 1,
        "post_click_capture_window_ms": 3000,
        "interception_protocol": "CDP_FETCH_REQUEST_STAGE",
        "post_click_network_policy": "ABORT_ALL_BEFORE_NETWORK",
        "download_behavior": "DENY",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "request_headers_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "query_value_capture": "PROHIBITED",
        "candidate_deduplication": "METHOD_ROUTE_WITHOUT_QUERY",
        "unique_candidate_required_for_pass": True,
        "candidate_route_network_send": "PROHIBITED",
        "head_request": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "drive_oauth": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "fail_closed_on_interception_error": True,
        "fail_closed_on_browser_unavailable": True,
        "fail_closed_on_zero_candidates": True,
        "fail_closed_on_multiple_candidates": True,
        "next_gate_if_unique_intercepted_route": "M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0",
        "next_gate_if_runtime_route_unproven": "STOP_REVIEW_RUNTIME_ROUTE_EVIDENCE",
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopeRuntimeRouteProbeDesignError(f"STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_{key.upper()}")

    page = urlparse(str(config.get("page_url", "")))
    if page.scheme != "https" or page.hostname != "www.fnde.gov.br" or not page.path.endswith("/visualizar/20"):
        raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_PAGE_URL")
    if config.get("initial_allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_ALLOWED_HOSTS")
    if config.get("required_product_name") != "Dados Gerais - SIOPE":
        raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_PRODUCT")
    if config.get("required_artifact_path") != "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz":
        raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_ARTIFACT")
    if config.get("candidate_resource_types") != ["XHR", "Fetch", "Document", "Other"]:
        raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_RESOURCE_TYPES")
    if config.get("candidate_methods") != ["GET", "POST"]:
        raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_METHODS")
    if config.get("target_identifiers") != [
        "getArtifactByDataProductId",
        "getArtifactMetadataByDataProductId",
        "downloadFile",
        "exportKey",
    ]:
        raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_IDENTIFIERS")

    return {
        "status": "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "browser_backend": config["browser_backend"],
        "browser_download_or_install": False,
        "browser_execution": False,
        "click_executed": False,
        "candidate_route_network_sent": False,
        "artifact_downloaded": False,
        "response_body_captured": False,
        "request_body_captured": False,
        "request_headers_captured": False,
        "cookies_captured": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_IMPLEMENTATION_0_8_0",
    }


def load_runtime_route_probe_design(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_runtime_route_probe_design(config)
    return config
