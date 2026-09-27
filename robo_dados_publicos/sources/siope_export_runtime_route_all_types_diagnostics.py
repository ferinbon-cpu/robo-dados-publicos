from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from .siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    SystemChromeCdpRuntime,
    sanitize_intercepted_url,
)


DIAGNOSTIC_INVENTORY_LIMIT = 128


def summarize_all_http_post_click_requests(
    events: list[dict],
    config: dict,
    *,
    limit: int = DIAGNOSTIC_INVENTORY_LIMIT,
) -> dict:
    if limit < 1 or limit > DIAGNOSTIC_INVENTORY_LIMIT:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_ALL_TYPES_DIAGNOSTICS_BAD_LIMIT")

    allowed_methods = set(config.get("candidate_methods") or ())
    dedup: dict[tuple[str, str, str], dict] = {}
    excluded_non_http = 0
    excluded_method = 0

    for event in events:
        method = str(event.get("method", "")).upper()
        resource_type = str(event.get("resource_type", "Other")) or "Other"
        sanitized = sanitize_intercepted_url(str(event.get("url", "")))
        if sanitized is None:
            excluded_non_http += 1
            continue
        if method not in allowed_methods:
            excluded_method += 1
            continue

        route = sanitized["route_without_query"]
        parsed = urlparse(route)
        key = (method, resource_type, route)
        if key not in dedup:
            dedup[key] = {
                "method": method,
                "resource_type": resource_type,
                "scheme": parsed.scheme,
                "host": parsed.hostname or "",
                "route_without_query": route,
                "query_keys": list(sanitized["query_keys"]),
                "query_present": bool(sanitized["query_present"]),
                "occurrences": 0,
                "network_sent": False,
                "intercepted_before_network": True,
            }
        else:
            dedup[key]["query_keys"] = sorted(
                set(dedup[key]["query_keys"]).union(sanitized["query_keys"])
            )
            dedup[key]["query_present"] = bool(
                dedup[key]["query_present"] or sanitized["query_present"]
            )
        dedup[key]["occurrences"] += 1

    ordered = [dedup[key] for key in sorted(dedup)]
    inventory = ordered[:limit]
    method_counts = Counter(item["method"] for item in ordered)
    resource_type_counts = Counter(item["resource_type"] for item in ordered)
    host_counts = Counter(item["host"] for item in ordered)

    return {
        "eligible_event_count": sum(item["occurrences"] for item in ordered),
        "unique_route_shape_count": len(ordered),
        "inventory_limit": limit,
        "inventory_truncated": len(ordered) > limit,
        "method_shape_counts": dict(sorted(method_counts.items())),
        "resource_type_shape_counts": dict(sorted(resource_type_counts.items())),
        "host_shape_counts": dict(sorted(host_counts.items())),
        "excluded_non_http_count": excluded_non_http,
        "excluded_method_count": excluded_method,
        "request_inventory": inventory,
    }


def diagnose_export_runtime_route_all_types(config: dict, *, runtime=None) -> dict:
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
        raise SiopeRuntimeRouteProbeError(
            "STOP_SIOPE_RUNTIME_ROUTE_ALL_TYPES_DIAGNOSTICS_RUNTIME_CONTRACT"
        )
    if raw.get("candidate_route_network_sent") is not False:
        raise SiopeRuntimeRouteProbeError(
            "STOP_SIOPE_RUNTIME_ROUTE_ALL_TYPES_DIAGNOSTICS_NETWORK_SENT"
        )

    summary = summarize_all_http_post_click_requests(
        list(raw.get("intercepted_requests") or []), config
    )
    diagnostics = {
        "post_click_aborted_request_count": int(raw.get("post_click_aborted_request_count", 0)),
        "cross_origin_initial_aborted_count": int(raw.get("cross_origin_initial_aborted_count", 0)),
        **summary,
    }
    if summary["unique_route_shape_count"] < 1:
        raise SiopeRuntimeRouteProbeError(
            "STOP_SIOPE_RUNTIME_ROUTE_ALL_TYPES_DIAGNOSTICS_NO_ELIGIBLE_REQUESTS",
            diagnostics=diagnostics,
        )

    return {
        "status": "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_ALL_TYPES_DIAGNOSTICS_GATE",
        "gate_id": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_ALL_TYPES_DIAGNOSTICS_GATE_0_8_0",
        "software_version": config["software_version"],
        "diagnostic_status": "ALL_HTTP_GET_POST_ROUTE_SHAPES_OBSERVED_NOT_SENT",
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
        "next_gate": "M7_SIOPE_RUNTIME_ROUTE_EVIDENCE_REVIEW_0_8_0",
    }
