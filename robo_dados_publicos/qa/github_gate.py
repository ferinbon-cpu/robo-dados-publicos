"""Validation contract for persistent GitHub Actions runtime runs."""

from __future__ import annotations


def evaluate_live_payload(
    payload: dict,
    source_expectation: dict | None = None,
    *,
    expected_version: str = "0.6.0",
    expected_status: str = "CANDIDATE",
) -> dict:
    """Return explicit gate checks without guessing around missing evidence."""

    checks = {
        "runtime_status_pass": payload.get("status") == "PASS",
        "software_version_match": payload.get("software_version") == expected_version,
        "release_status_match": payload.get("release_status") == expected_status,
        "state_source_remote_existing": payload.get("state_source") == "REMOTE_EXISTING",
        "state_remote_replaced": (payload.get("state_remote") or {}).get("mode") == "REPLACED",
        "append_only_log_created": bool((payload.get("log_remote") or {}).get("id")),
        "append_only_log_named": str((payload.get("log_remote") or {}).get("name", "")).startswith("ROBO_RUN_"),
    }
    pass_status = "PASS_GITHUB_LIVE_GATE"
    stop_status = "STOP_GITHUB_LIVE_GATE"
    if source_expectation:
        collection = payload.get("source_collection") or {}
        results = collection.get("results") or []
        source_result = next(
            (item for item in results if item.get("source_id") == source_expectation.get("source_id")),
            {},
        )
        checks.update({
            "source_mode_enabled": payload.get("mode") == "SOURCE_COLLECTION_ENABLED",
            "source_collection_pass": collection.get("status") == "PASS",
            "one_enabled_source": (collection.get("inventory") or {}).get("enabled") == 1,
            "expected_source_present": bool(source_result),
            "source_downloaded_new": source_result.get("status") == "DOWNLOADED_NEW",
            "source_remote_created": bool(source_result.get("remote_id")),
            "source_sha256_match": source_result.get("sha256") == source_expectation.get("expected_sha256"),
            "source_bytes_match": source_result.get("bytes") == source_expectation.get("expected_bytes"),
            "source_content_type_match": source_result.get("content_type") in source_expectation.get("expected_content_types", ()),
        })
        pass_status = "PASS_GITHUB_SOURCE_COLLECTION_GATE"
        stop_status = "STOP_GITHUB_SOURCE_COLLECTION_GATE"
    return {
        "status": pass_status if all(checks.values()) else stop_status,
        "checks": checks,
    }
