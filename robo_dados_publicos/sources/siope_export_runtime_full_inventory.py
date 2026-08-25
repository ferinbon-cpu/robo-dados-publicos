from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import urlparse

from .siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    SystemChromeCdpRuntime,
    sanitize_intercepted_url,
)


FULL_INVENTORY_LIMIT = 128
_STATIC_RESOURCE_TYPES = {"Image", "Script", "Stylesheet", "Font", "Media", "Manifest"}
_STATIC_SUFFIXES = {
    ".css", ".js", ".mjs", ".map",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".mp4", ".webm", ".ogg",
}


def _static_asset(route_without_query: str, resource_type: str) -> bool:
    if resource_type in _STATIC_RESOURCE_TYPES:
        return True
    path = urlparse(route_without_query).path.lower()
    return any(path.endswith(suffix) for suffix in _STATIC_SUFFIXES)


def _marker_hits(route_without_query: str, config: dict) -> list[str]:
    route_lower = route_without_query.lower()
    markers = list(config.get("export_route_markers") or [])
    artifact_name = PurePosixPath(str(config.get("required_artifact_path", ""))).name
    if artifact_name:
        markers.append(artifact_name)
    hits = {str(marker) for marker in markers if str(marker) and str(marker).lower() in route_lower}
    return sorted(hits, key=str.lower)


def summarize_all_post_click_http_requests(
    events: list[dict],
    config: dict,
    *,
    limit: int = FULL_INVENTORY_LIMIT,
) -> dict:
    if limit < 1 or limit > FULL_INVENTORY_LIMIT:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_FULL_INVENTORY_BAD_LIMIT")

    dedup: dict[tuple[str, str, str], dict] = {}
    non_http_count = 0
    empty_method_count = 0

    for event in events:
        method = str(event.get("method", "")).upper().strip()
        resource_type = str(event.get("resource_type", "Other")) or "Other"
        sanitized = sanitize_intercepted_url(str(event.get("url", "")))
        if sanitized is None:
            non_http_count += 1
            continue
        if not method:
            empty_method_count += 1
            method = "UNKNOWN"

        route = sanitized["route_without_query"]
        parsed = urlparse(route)
        key = (method, resource_type, route)
        if key not in dedup:
            hits = _marker_hits(route, config)
            static = _static_asset(route, resource_type)
            dedup[key] = {
                "method": method,
                "resource_type": resource_type,
                "scheme": parsed.scheme,
                "host": parsed.hostname or "",
                "same_origin_fnde": parsed.hostname == "www.fnde.gov.br",
                "route_without_query": route,
                "query_keys": list(sanitized["query_keys"]),
                "query_present": bool(sanitized["query_present"]),
                "likely_static_asset": static,
                "marker_hits": hits,
                "potential_export_shape": bool(hits) or not static,
                "occurrences": 0,
                "network_sent": False,
                "intercepted_before_network": True,
            }
        else:
            dedup[key]["query_keys"] = sorted(set(dedup[key]["query_keys"]).union(sanitized["query_keys"]))
            dedup[key]["query_present"] = bool(dedup[key]["query_present"] or sanitized["query_present"])
        dedup[key]["occurrences"] += 1

    ordered = [dedup[key] for key in sorted(dedup)]
    if len(ordered) > limit:
        raise SiopeRuntimeRouteProbeError(
            "STOP_SIOPE_RUNTIME_FULL_INVENTORY_TRUNCATION_REQUIRED",
            diagnostics={
                "unique_route_shape_count": len(ordered),
                "inventory_limit": limit,
                "network_sent": False,
            },
        )

    resource_event_counts = Counter()
    method_event_counts = Counter()
    host_event_counts = Counter()
    for item in ordered:
        occurrences = int(item["occurrences"])
        resource_event_counts[item["resource_type"]] += occurrences
        method_event_counts[item["method"]] += occurrences
        host_event_counts[item["host"]] += occurrences

    potential = [item for item in ordered if item["potential_export_shape"]]
    marker_shapes = [item for item in ordered if item["marker_hits"]]
    non_static = [item for item in ordered if not item["likely_static_asset"]]

    return {
        "http_event_count": sum(int(item["occurrences"]) for item in ordered),
        "unique_route_shape_count": len(ordered),
        "non_http_event_count": non_http_count,
        "empty_method_count": empty_method_count,
        "inventory_limit": limit,
        "inventory_truncated": False,
        "resource_type_event_counts": dict(sorted(resource_event_counts.items())),
        "method_event_counts": dict(sorted(method_event_counts.items())),
        "host_event_counts": dict(sorted(host_event_counts.items())),
        "non_static_shape_count": len(non_static),
        "marker_shape_count": len(marker_shapes),
        "potential_export_shape_count": len(potential),
        "request_inventory": ordered,
        "potential_export_shapes": potential,
    }


def diagnose_full_runtime_inventory(config: dict, *, runtime=None) -> dict:
    runtime = runtime or SystemChromeCdpRuntime()
    raw = runtime.run_probe(config)

    required_true = (
        "page_verified",
        "artifact_declared",
        "export_control_found",
        "click_executed",
        "post_click_interception_active",
        "browser_download_denied",
    )
    if any(raw.get(key) is not True for key in required_true):
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_FULL_INVENTORY_RUNTIME_CONTRACT")
    if raw.get("candidate_route_network_sent") is not False:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_FULL_INVENTORY_NETWORK_SENT")

    events = list(raw.get("intercepted_requests") or [])
    summary = summarize_all_post_click_http_requests(events, config)
    diagnostics = {
        "post_click_aborted_request_count": int(raw.get("post_click_aborted_request_count", 0)),
        "cross_origin_initial_aborted_count": int(raw.get("cross_origin_initial_aborted_count", 0)),
        **summary,
    }
    if diagnostics["post_click_aborted_request_count"] < 1:
        raise SiopeRuntimeRouteProbeError(
            "STOP_SIOPE_RUNTIME_FULL_INVENTORY_NO_POST_CLICK_REQUESTS",
            diagnostics=diagnostics,
        )
    if diagnostics["http_event_count"] < 1:
        raise SiopeRuntimeRouteProbeError(
            "STOP_SIOPE_RUNTIME_FULL_INVENTORY_NO_HTTP_REQUESTS",
            diagnostics=diagnostics,
        )

    if diagnostics["marker_shape_count"] == 1:
        evidence_status = "ONE_MARKER_BOUND_ROUTE_SHAPE_OBSERVED_NOT_SENT"
        next_gate = "M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0"
    elif diagnostics["potential_export_shape_count"] >= 1:
        evidence_status = "FULL_POST_CLICK_HTTP_INVENTORY_OBSERVED_REVIEW_REQUIRED"
        next_gate = "M7_SIOPE_RUNTIME_CONTROL_TARGET_DIAGNOSTICS_0_8_0"
    else:
        evidence_status = "ONLY_STATIC_POST_CLICK_HTTP_SHAPES_OBSERVED"
        next_gate = "M7_SIOPE_RUNTIME_CONTROL_TARGET_DIAGNOSTICS_0_8_0"

    return {
        "status": "PASS_M7_SIOPE_EXPORT_RUNTIME_FULL_INVENTORY_GATE",
        "gate_id": "M7_SIOPE_EXPORT_RUNTIME_FULL_INVENTORY_GATE_0_8_0",
        "software_version": config["software_version"],
        "diagnostic_status": evidence_status,
        "browser_backend": config["browser_backend"],
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "browser_automation_performed": True,
        "click_executed": True,
        "post_click_interception_active": True,
        "browser_download_denied": True,
        "candidate_route_network_sent": False,
        "diagnostics": diagnostics,
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
        "next_gate": next_gate,
    }
