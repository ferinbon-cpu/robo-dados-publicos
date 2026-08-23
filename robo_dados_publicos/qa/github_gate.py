"""Validation contract for the first persistent GitHub Actions run."""

from __future__ import annotations


def evaluate_live_payload(payload: dict) -> dict:
    """Return explicit gate checks without guessing around missing evidence."""

    checks = {
        "runtime_status_pass": payload.get("status") == "PASS",
        "candidate_version_0_5_9": payload.get("software_version") == "0.5.9",
        "release_status_candidate": payload.get("release_status") == "CANDIDATE",
        "state_source_remote_existing": payload.get("state_source") == "REMOTE_EXISTING",
        "state_remote_replaced": (payload.get("state_remote") or {}).get("mode") == "REPLACED",
        "append_only_log_created": bool((payload.get("log_remote") or {}).get("id")),
        "append_only_log_named": str((payload.get("log_remote") or {}).get("name", "")).startswith("ROBO_RUN_"),
    }
    return {
        "status": "PASS_GITHUB_LIVE_GATE" if all(checks.values()) else "STOP_GITHUB_LIVE_GATE",
        "checks": checks,
    }
