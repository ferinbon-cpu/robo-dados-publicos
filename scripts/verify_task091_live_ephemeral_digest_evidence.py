#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSURE = ROOT / "docs/evidence/TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST_CLOSURE_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_091_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"
WORKFLOW_SOURCE = ROOT / "docs/evidence/TASK_091_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
TASK_CONTRACT = ROOT / "docs/tasks/CODEX_TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST.md"
LIVE_WORKFLOW = ROOT / ".github/workflows/task-091-live-ephemeral-drive-digest.yml"

EXPECTED_WORKFLOW_BLOB = "1e354d9c9129f9c3ac4ba1e3bf80947301c7616c"
EXPECTED_TASK_BLOB = "143bad34650ac1707df96875312ef8e3ed749189"
EXPECTED_PAYLOAD_SELF_HASH = "7cd575881c2e3ae25b5afff287004738ee85681faf26c35d3a272fb6ba867c90"
EXPECTED_SOURCE_SHA256 = "44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c"
EXPECTED_SOURCE_BYTES = 17615179
EXPECTED_FILE_ID = "1JTpCPj4_rL08RubO5wOVvBHjuwqKWfQ8"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(obj, dict), f"STOP_TASK091_JSON_OBJECT_REQUIRED_{path.name}")
    return obj


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def payload_self_hash(payload: dict) -> str:
    copy = dict(payload)
    observed = copy.pop("evidence_payload_sha256_without_self_hash", None)
    _require(observed is not None, "STOP_TASK091_PAYLOAD_SELF_HASH_MISSING")
    raw = json.dumps(copy, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run() -> dict:
    closure = _load(CLOSURE)
    payload = _load(PAYLOAD)
    workflow_bytes = WORKFLOW_SOURCE.read_bytes()
    workflow = workflow_bytes.decode("utf-8")
    task_bytes = TASK_CONTRACT.read_bytes()
    task = task_bytes.decode("utf-8")

    _require(not LIVE_WORKFLOW.exists(), "STOP_TASK091_LIVE_WORKFLOW_STILL_PRESENT")
    _require(git_blob_sha(workflow_bytes) == EXPECTED_WORKFLOW_BLOB, "STOP_TASK091_WORKFLOW_BLOB")
    _require(git_blob_sha(task_bytes) == EXPECTED_TASK_BLOB, "STOP_TASK091_TASK_BLOB")

    _require("Fresh owner instruction: **2026-09-04 — `prossiga`**." in task, "STOP_TASK091_OWNER_AUTH")
    _require("retry" in task.lower() and "does not authorize retry" in task, "STOP_TASK091_RETRY_BOUNDARY")
    _require(EXPECTED_FILE_ID in task, "STOP_TASK091_TASK_FILE_ID")
    _require(str(EXPECTED_SOURCE_BYTES) in task, "STOP_TASK091_TASK_BYTES")
    _require(EXPECTED_SOURCE_SHA256 in task, "STOP_TASK091_TASK_SHA")
    _require("READY_FOR_ONE_OWNER_AUTHORIZED_LIVE_RUN" in task, "STOP_TASK091_TASK_READY_MARKER")

    _require(payload_self_hash(payload) == EXPECTED_PAYLOAD_SELF_HASH, "STOP_TASK091_PAYLOAD_SELF_HASH")
    _require(payload["evidence_payload_sha256_without_self_hash"] == EXPECTED_PAYLOAD_SELF_HASH, "STOP_TASK091_PAYLOAD_SELF_HASH_FIELD")
    _require(payload["status"] == "STOP_TASK091_LIVE_DRIVE_TO_EPHEMERAL_DIGEST", "STOP_TASK091_PAYLOAD_STATUS")
    _require(payload["reason"] == "RuntimeError:STOP_TASK091_HISTORICAL_COUNT_DRIFT", "STOP_TASK091_STOP_REASON")
    _require(payload["request_count"] == 2, "STOP_TASK091_REQUEST_COUNT")
    _require(payload["authorization"]["single_use"] is True, "STOP_TASK091_SINGLE_USE")
    _require(payload["authorization"]["retry_authorized"] is False, "STOP_TASK091_RETRY_AUTH")
    _require(payload["authorization"]["future_execution_authorized"] is False, "STOP_TASK091_FUTURE_AUTH")
    _require(payload["ephemeral_cleanup_verified"] is True, "STOP_TASK091_CLEANUP")

    expected_requests = [
        {"ordinal": 1, "method": "POST", "host": "oauth2.googleapis.com", "route_class": "OAUTH_TOKEN_EXCHANGE"},
        {"ordinal": 2, "method": "GET", "host": "www.googleapis.com", "route_class": "EXACT_DRIVE_MEDIA_GET"},
    ]
    _require(payload["requests"] == expected_requests, "STOP_TASK091_REQUEST_TRACE")
    _require(payload["source"]["drive_file_id"] == EXPECTED_FILE_ID, "STOP_TASK091_FILE_ID")
    _require(payload["source"]["expected_bytes"] == EXPECTED_SOURCE_BYTES, "STOP_TASK091_SOURCE_BYTES")
    _require(payload["source"]["expected_sha256"] == EXPECTED_SOURCE_SHA256, "STOP_TASK091_SOURCE_SHA")

    _require("permissions:\n  contents: read" in workflow, "STOP_TASK091_WORKFLOW_PERMISSION")
    _require("persist-credentials: false" in workflow, "STOP_TASK091_WORKFLOW_GIT_CREDENTIALS")
    _require("ordinal > 2" in workflow, "STOP_TASK091_REQUEST_BUDGET")
    _require('client.get(FILE_ID, source_path)' in workflow, "STOP_TASK091_EXACT_GET_CALL")
    _require('parsed.netloc == "www.googleapis.com"' in workflow, "STOP_TASK091_DRIVE_HOST_GUARD")
    _require('parsed.netloc == "oauth2.googleapis.com"' in workflow, "STOP_TASK091_OAUTH_HOST_GUARD")
    _require('path: ${{ runner.temp }}/task091/evidence/result.json' in workflow, "STOP_TASK091_ARTIFACT_PATH")
    for forbidden in (
        "workflow_dispatch:",
        "schedule:",
        "repository_dispatch:",
        "workflow_call:",
        "client.put(",
        "client.delete(",
        "client.replace_content(",
        "client.list_children(",
        "client.metadata(",
    ):
        _require(forbidden not in workflow, f"STOP_TASK091_WORKFLOW_FORBIDDEN_{forbidden.rstrip(':').upper()}")

    order = [
        'if download["bytes"] != EXPECTED_BYTES:',
        'if download["sha256"] != EXPECTED_SHA256:',
        'result = run_ephemeral_digest(',
        'if result["status"] != "PASS_EPHEMERAL_RUNTIME_DIGEST_NOT_PERSISTED":',
        'if result["input_count"] != 1 or result["candidate_file_count"] != 4:',
        'if observed_counts != EXPECTED_COUNTS:',
        'raise RuntimeError("STOP_TASK091_HISTORICAL_COUNT_DRIFT")',
    ]
    positions = [workflow.index(marker) for marker in order]
    _require(positions == sorted(positions), "STOP_TASK091_GATE_ORDER")

    _require(closure["execution"]["run_id"] == 33873064071, "STOP_TASK091_CLOSURE_RUN")
    _require(closure["execution"]["job_id"] == 101023430264, "STOP_TASK091_CLOSURE_JOB")
    _require(closure["execution"]["head_sha"] == "0c777c647cefaacc9d1daba35c1cded42109c120", "STOP_TASK091_CLOSURE_HEAD")
    _require(closure["execution"]["executed_workflow_blob_sha"] == EXPECTED_WORKFLOW_BLOB, "STOP_TASK091_CLOSURE_WORKFLOW_BLOB")
    _require(closure["execution"]["second_run_observed"] is False, "STOP_TASK091_SECOND_RUN")
    _require(closure["source"]["source_identity_gate_passed_before_stop"] is True, "STOP_TASK091_SOURCE_GATE")
    _require(closure["live_transport"]["drive_media_gets"] == 1, "STOP_TASK091_DRIVE_GET_COUNT")
    _require(closure["live_transport"]["drive_mutating_requests"] == 0, "STOP_TASK091_DRIVE_MUTATION")
    _require(closure["digest"]["pass_status_gate_before_stop"] is True, "STOP_TASK091_DIGEST_STATUS_GATE")
    _require(closure["digest"]["input_count_one_and_candidate_file_count_four_gate_passed_before_stop"] is True, "STOP_TASK091_DIGEST_FILE_GATE")
    _require(closure["digest"]["derived_candidates_persisted_remotely"] is False, "STOP_TASK091_DERIVED_PERSISTENCE")
    _require(closure["digest"]["derived_candidates_uploaded_as_artifact"] is False, "STOP_TASK091_DERIVED_ARTIFACT")
    _require(closure["digest"]["observed_counts_captured"] is False, "STOP_TASK091_OBSERVED_COUNTS_CLAIM")
    _require(closure["digest"]["root_cause_status"] == "UNRESOLVED", "STOP_TASK091_ROOT_CAUSE_OVERCLAIM")
    _require(closure["result"] == "STOP_TASK091_DIGEST_PROVEN_EPHEMERAL_HISTORICAL_COUNT_DRIFT_UNRESOLVED", "STOP_TASK091_CLOSURE_RESULT")

    for key, value in closure["hard_boundaries"].items():
        _require(value == 0, f"STOP_TASK091_HARD_BOUNDARY_{key.upper()}")

    return {
        "status": "PASS_TASK091_LIVE_EPHEMERAL_DIGEST_EVIDENCE_OFFLINE",
        "run_id": closure["execution"]["run_id"],
        "request_count": payload["request_count"],
        "drive_media_gets": closure["live_transport"]["drive_media_gets"],
        "digest_passed_before_historical_comparison": True,
        "candidate_file_count_gate_passed": True,
        "historical_count_drift": True,
        "root_cause_status": "UNRESOLVED",
        "retry_authorized": False,
        "future_execution_authorized": False,
        "live_workflow_present": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_TASK091_LIVE_EPHEMERAL_DIGEST_EVIDENCE_OFFLINE", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        raise SystemExit(91)
