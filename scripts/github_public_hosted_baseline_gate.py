#!/usr/bin/env python3
"""Deterministic fail-closed gate for the hosted GitHub public-readiness baseline.

This gate deliberately performs no network requests. It validates the pinned
exhaustive hosted-surface audit, the exact manual review of the only two opaque
historical artifacts, the post-baseline PR-only closure evidence, and the current
source of every workflow that could have produced post-baseline CI.

The full hosted scanner remains available for future explicit re-baselining, but
ordinary PR CI does not repeatedly download >1,000 historical Actions log archives.
"""
from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "evidence" / "PUBLIC_READINESS_HOSTED_BASELINE_0.8.0.json"
INCREMENTAL = ROOT / "docs" / "evidence" / "PUBLIC_READINESS_POST_BASELINE_INCREMENTAL_0.8.0.json"
ALLOWLIST = ROOT / "config" / "public_hosted_surface_allowlist.v1.json"

EXPECTED_BASELINE = {
    "workflow_run_id": 33164350655,
    "workflow_job_id": 98826093420,
    "audit_artifact_id": 9682995025,
    "audit_artifact_digest": "sha256:5960b6292ef385e0c54410a9e7491f625d27ff132e758eab9193da56fe1cd28f",
    "audit_head_sha": "7a00af42e20437388d76520a38e6547a0a7a0dac",
    "incremental_overlap_cutoff_utc": "2026-08-28T10:44:00Z",
}
EXPECTED_HOSTED_COUNTS = {
    "metadata_text_records_scanned": 336,
    "completed_actions_runs_considered": 1146,
    "completed_actions_runs_scanned": 1146,
    "completed_actions_runs_unavailable_or_expired": 0,
    "nonexpired_artifacts_considered": 104,
    "nonexpired_artifacts_scanned": 104,
    "expired_artifacts_skipped": 0,
    "artifact_text_entries_scanned": 136,
    "artifact_opaque_entries_for_review": 2,
    "blocker_count": 0,
    "review_count_before_manual_binary_review": 2,
}
EXPECTED_PDFS = {
    "9670498410": {
        "entry": "product/report.pdf",
        "bytes": 21854,
        "sha256": "1e66378b20b0662f21557ab0b3011ad07b61e89c9879bd8c31a783b4a7221b77",
    },
    "9672319372": {
        "entry": "product/report.pdf",
        "bytes": 21854,
        "sha256": "31aadfd44448061aefcbc76903e3f910f14b7f8b6e46ae60dbfdc683143225d9",
    },
}
EXPECTED_WORKFLOWS = {
    ".github/workflows/public-readiness-audit.yml",
    ".github/workflows/ci-offline.yml",
    ".github/workflows/ci-m7-olinda-hash-routing-signal.yml",
    ".github/workflows/ci-m7-olinda-fragment-target-structure.yml",
    ".github/workflows/ci-m7-olinda-loaded-script-signatures.yml",
}
FORBIDDEN_WORKFLOW_PATTERNS = {
    "PULL_REQUEST_TARGET": re.compile(r"(?m)^\s*pull_request_target\s*:"),
    "WRITE_ALL": re.compile(r"(?mi)^\s*permissions\s*:\s*write-all\s*$"),
    "SECRETS_INHERIT": re.compile(r"(?i)secrets\s*:\s*inherit"),
    "ACTIONS_SECRET_REFERENCE": re.compile(r"\$\{\{\s*secrets\."),
    "DRIVE_READONLY_SECRET_NAME": re.compile(r"GOOGLE_DRIVE_READONLY_(?:CLIENT_ID|CLIENT_SECRET|REFRESH_TOKEN)"),
    "DRIVE_BROAD_SECRET_NAME": re.compile(r"GOOGLE_DRIVE_(?:CLIENT_ID|CLIENT_SECRET|REFRESH_TOKEN)"),
}


class HostedBaselineGateError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise HostedBaselineGateError(code)


def _load(path: Path) -> dict:
    _require(path.is_file(), f"STOP_HOSTED_BASELINE_FILE_MISSING_{path.name}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HostedBaselineGateError(f"STOP_HOSTED_BASELINE_JSON_INVALID_{path.name}") from exc
    _require(isinstance(payload, dict), f"STOP_HOSTED_BASELINE_SHAPE_{path.name}")
    return payload


def _validate_baseline(baseline: dict, allowlist: dict) -> None:
    pinned = baseline.get("baseline") or {}
    for key, value in EXPECTED_BASELINE.items():
        _require(pinned.get(key) == value, f"STOP_HOSTED_BASELINE_PIN_{key.upper()}")
    scan = pinned.get("hosted_scan") or {}
    for key, value in EXPECTED_HOSTED_COUNTS.items():
        _require(scan.get(key) == value, f"STOP_HOSTED_BASELINE_COUNT_{key.upper()}")

    resolution = baseline.get("baseline_resolution") or {}
    _require(resolution.get("credential_or_secret_blockers") == 0, "STOP_HOSTED_BASELINE_SECRET_BLOCKER")
    _require(resolution.get("unresolved_binary_reviews") == 0, "STOP_HOSTED_BASELINE_BINARY_REVIEW")
    _require(resolution.get("secret_values_exposed") is False, "STOP_HOSTED_BASELINE_SECRET_EXPOSURE")
    _require(resolution.get("ready_as_historical_baseline") is True, "STOP_HOSTED_BASELINE_NOT_READY")

    reviews = baseline.get("manual_binary_reviews") or []
    review_by_id = {str(item.get("artifact_id")): item for item in reviews if isinstance(item, dict)}
    allow_entries = allowlist.get("entries") or []
    allow_by_id = {str(item.get("resource_id")): item for item in allow_entries if isinstance(item, dict)}
    _require(set(review_by_id) == set(EXPECTED_PDFS), "STOP_HOSTED_BASELINE_PDF_REVIEW_SET")
    _require(set(allow_by_id) == set(EXPECTED_PDFS), "STOP_HOSTED_BASELINE_PDF_ALLOWLIST_SET")
    for artifact_id, expected in EXPECTED_PDFS.items():
        for source, prefix in ((review_by_id[artifact_id], "REVIEW"), (allow_by_id[artifact_id], "ALLOWLIST")):
            _require(str(source.get("entry")) == expected["entry"], f"STOP_HOSTED_{prefix}_ENTRY_{artifact_id}")
            _require(source.get("bytes") == expected["bytes"], f"STOP_HOSTED_{prefix}_BYTES_{artifact_id}")
            _require(str(source.get("sha256")) == expected["sha256"], f"STOP_HOSTED_{prefix}_SHA_{artifact_id}")


def _validate_incremental(incremental: dict) -> None:
    _require(incremental.get("baseline_cutoff_utc") == EXPECTED_BASELINE["incremental_overlap_cutoff_utc"], "STOP_POST_BASELINE_CUTOFF")
    snapshot = incremental.get("snapshot") or {}
    _require(snapshot.get("captured_for_pr") == 168, "STOP_POST_BASELINE_PR")
    _require(snapshot.get("audit_branch") == "public-readiness-audit", "STOP_POST_BASELINE_BRANCH")
    total = snapshot.get("actions_runs_created_at_or_after_cutoff")
    _require(isinstance(total, int) and total >= 35, "STOP_POST_BASELINE_RUN_TOTAL")
    _require(snapshot.get("actions_pull_request_runs_created_at_or_after_cutoff") == total, "STOP_POST_BASELINE_NON_PR_RUN")
    _require(snapshot.get("actions_audit_branch_runs_created_at_or_after_cutoff") == total, "STOP_POST_BASELINE_OUTSIDE_BRANCH")
    _require(snapshot.get("non_pull_request_runs") == 0, "STOP_POST_BASELINE_NON_PR_COUNT")
    _require(snapshot.get("runs_outside_audit_branch") == 0, "STOP_POST_BASELINE_OUTSIDE_BRANCH_COUNT")
    _require(snapshot.get("pr_comments_after_baseline_review") == 0, "STOP_POST_BASELINE_COMMENTS")

    closure = incremental.get("closure_evidence") or {}
    required_true = (
        "all_post_baseline_runs_are_pull_request_runs",
        "all_post_baseline_runs_are_on_public_readiness_audit_branch",
        "pr_168_has_no_conversation_comments",
        "current_workflow_sources_reviewed",
    )
    for key in required_true:
        _require(closure.get(key) is True, f"STOP_POST_BASELINE_CLOSURE_{key.upper()}")
    required_false = (
        "pull_request_target_present",
        "secrets_inherit_present",
        "write_all_present",
        "drive_or_source_credentials_present_in_post_baseline_workflow_set",
        "live_drive_or_source_execution_present_in_post_baseline_workflow_set",
    )
    for key in required_false:
        _require(closure.get(key) is False, f"STOP_POST_BASELINE_CLOSURE_{key.upper()}")

    workflow_rows = incremental.get("post_baseline_workflow_set") or []
    workflow_paths = {str(item.get("path")) for item in workflow_rows if isinstance(item, dict)}
    _require(workflow_paths == EXPECTED_WORKFLOWS, "STOP_POST_BASELINE_WORKFLOW_SET")
    for row in workflow_rows:
        _require(row.get("repository_secrets_used") is False, "STOP_POST_BASELINE_WORKFLOW_SECRET")
        _require(row.get("drive_credentials_used") is False, "STOP_POST_BASELINE_WORKFLOW_DRIVE")
        _require(row.get("source_collection_live") is False, "STOP_POST_BASELINE_WORKFLOW_SOURCE_LIVE")

    resolution = incremental.get("resolution") or {}
    _require(resolution.get("post_baseline_secret_or_credential_finding") is False, "STOP_POST_BASELINE_SECRET_FINDING")
    _require(resolution.get("post_baseline_live_drive_or_source_run") is False, "STOP_POST_BASELINE_LIVE_RUN")
    _require(resolution.get("unresolved_post_baseline_public_surface_review") is False, "STOP_POST_BASELINE_REVIEW")
    _require(resolution.get("ready_for_offline_baseline_gate") is True, "STOP_POST_BASELINE_NOT_READY")


def _validate_current_workflows() -> None:
    for rel in sorted(EXPECTED_WORKFLOWS):
        path = ROOT / rel
        _require(path.is_file(), f"STOP_POST_BASELINE_WORKFLOW_MISSING_{path.name}")
        text = path.read_text(encoding="utf-8", errors="replace")
        _require(re.search(r"(?m)^\s*pull_request\s*:", text) is not None, f"STOP_POST_BASELINE_NO_PR_TRIGGER_{path.name}")
        for code, pattern in FORBIDDEN_WORKFLOW_PATTERNS.items():
            _require(pattern.search(text) is None, f"STOP_POST_BASELINE_{code}_{path.name}")


def run() -> dict:
    baseline = _load(BASELINE)
    incremental = _load(INCREMENTAL)
    allowlist = _load(ALLOWLIST)
    _validate_baseline(baseline, allowlist)
    _validate_incremental(incremental)
    _validate_current_workflows()
    return {
        "status": "PASS_PUBLIC_HOSTED_BASELINE_CLOSURE",
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "baseline_run_id": EXPECTED_BASELINE["workflow_run_id"],
        "baseline_artifact_id": EXPECTED_BASELINE["audit_artifact_id"],
        "historical_hosted_secret_blockers": 0,
        "historical_opaque_reviews_resolved_exactly": 2,
        "post_baseline_non_pr_runs": 0,
        "post_baseline_live_drive_or_source_runs": 0,
        "current_post_baseline_workflows_safe_for_pr": True,
        "network_called": False,
        "secret_values_exposed": False,
        "repository_visibility_change_executed": False,
        "publication_authorized": False,
        "future_batch_execution_authorized": False,
    }


def main() -> int:
    try:
        result = run()
    except Exception as exc:
        print(json.dumps({"status": "STOP_PUBLIC_HOSTED_BASELINE_CLOSURE", "error": str(exc)}, sort_keys=True))
        return 42
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
