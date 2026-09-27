from __future__ import annotations

from urllib.parse import urlparse

from .siope_artifact_download_runtime_route_probe import (
    SystemChromeCdpArtifactDownloadRuntime,
    load_artifact_download_runtime_route_probe_config,
)
from .siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError, sanitize_intercepted_url

ERROR = "STOP_SIOPE_ARTIFACT_DOWNLOAD_BLOCKED_SHAPE_DIAGNOSTICS"


def _shape(event: dict, config: dict) -> dict:
    method = str(event.get("method", "")).upper()
    resource_type = str(event.get("resource_type", "Other"))
    raw_url = str(event.get("url", ""))
    parsed = urlparse(raw_url)
    out = {
        "method": method,
        "resource_type": resource_type,
        "scheme": parsed.scheme,
        "network_sent": False,
        "intercepted_before_network": True,
    }
    sanitized = sanitize_intercepted_url(raw_url)
    if sanitized is not None:
        route = sanitized["route_without_query"]
        route_parsed = urlparse(route)
        out.update({
            "host": route_parsed.hostname or "",
            "route_without_query": route,
            "query_keys": list(sanitized["query_keys"]),
            "query_present": bool(sanitized["query_present"]),
        })
        if route == config["verified_metadata_url"]:
            reason = "VERIFIED_METADATA"
        elif route_parsed.hostname == config["static_asset_host"] and route_parsed.path == "/plataforma-antonieta-de-barros/favicon.ico":
            reason = "FAVICON"
        elif method not in set(config["candidate_methods"]):
            reason = "METHOD_NOT_CANDIDATE"
        elif route_parsed.scheme != "https":
            reason = "NON_HTTPS"
        else:
            reason = "CANDIDATE_ELIGIBLE"
    else:
        out.update({"host": parsed.hostname or "", "route_without_query": None, "query_keys": [], "query_present": bool(parsed.query)})
        if method not in set(config["candidate_methods"]):
            reason = "METHOD_NOT_CANDIDATE"
        elif parsed.scheme not in {"http", "https"}:
            reason = "LOCAL_OR_NON_HTTP_SCHEME"
        else:
            reason = "SANITIZER_REJECTED"
    out["classification_reason"] = reason
    return out


def diagnose_blocked_shape(config: dict, *, runtime=None) -> dict:
    runtime = runtime or SystemChromeCdpArtifactDownloadRuntime()
    raw = runtime.run_probe(config)
    for key in ("page_verified", "artifact_declared", "export_control_found", "click_executed", "post_click_interception_active", "browser_download_denied"):
        if raw.get(key) is not True:
            raise SiopeRuntimeRouteProbeError(f"{ERROR}_RUNTIME_CONTRACT")
    if raw.get("candidate_route_network_sent") is not False:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_CANDIDATE_NETWORK_SENT")
    metadata_count = int(raw.get("verified_metadata_request_count", 0))
    if not 1 <= metadata_count <= config["max_verified_metadata_requests"] or raw.get("verified_metadata_network_sent") is not True:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_VERIFIED_METADATA_NOT_OBSERVED")
    blocked = list(raw.get("blocked_requests") or [])
    if not blocked:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_NO_BLOCKED_REQUESTS")
    shapes = [_shape(event, config) for event in blocked[:16]]
    return {
        "status": "PASS_M7_SIOPE_ARTIFACT_DOWNLOAD_BLOCKED_SHAPE_DIAGNOSTICS_GATE",
        "diagnostic_status": "POST_METADATA_BLOCKED_SHAPES_OBSERVED_NOT_SENT",
        "verified_metadata_request_count": metadata_count,
        "verified_metadata_network_sent": True,
        "blocked_request_count": len(blocked),
        "blocked_request_shapes": shapes,
        "inventory_truncated": len(blocked) > 16,
        "candidate_route_network_sent": False,
        "response_body_captured": False,
        "request_body_captured": False,
        "request_headers_captured": False,
        "cookies_captured": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_ARTIFACT_DOWNLOAD_BLOCKED_SHAPE_EVIDENCE_REVIEW_0_8_0",
    }
