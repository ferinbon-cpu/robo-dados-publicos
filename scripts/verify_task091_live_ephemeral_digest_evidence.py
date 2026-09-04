#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TASK_BLOB = "6c0af7b97bb3897bf1a6226210fccb608d0bfe1e"
EXPECTED_PAYLOAD_BLOB = "24728709af56bf0a1654c1725755a2a60b3e83da"
EXPECTED_CLOSURE_BLOB = "d6df832cc98a5f1ca41d2a908a587526e3aaf90d"
EXPECTED_AUTH_BLOB = "703da9fefb8b13544802b7dced3b256deafefab7"
EXPECTED_EXECUTED_WORKFLOW_BLOB = "1e354d9c9129f9c3ac4ba1e3bf80947301c7616c"
EXPECTED_PRE_RUN_CONTRACT_BLOB = "143bad34650ac1707df96875312ef8e3ed749189"
EXPECTED_REDACTED_PAYLOAD_SELF_HASH = "1d6adfd5b698c6d217352675050c3dcaf5427d8ecd25984a26b933c3d9737d0e"
EXPECTED_REMOTE_ID_SHA256 = "c4ddf384c210c0189c8c6da932de27cdaa70f810d026060736f10c76ed99dfc5"
EXPECTED_SOURCE_SHA256 = "44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c"
EXPECTED_SOURCE_BYTES = 17615179


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(obj, dict), f"STOP_TASK091_JSON_OBJECT_REQUIRED_{path.name}")
    return obj


def _payload_self_hash(payload: dict) -> str:
    copy = dict(payload)
    copy.pop("evidence_payload_sha256_without_self_hash", None)
    raw = json.dumps(copy, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run(root: str | Path = ROOT) -> dict:
    root = Path(root)
    task_path = root / "docs/tasks/CODEX_TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST.md"
    payload_path = root / "docs/evidence/TASK_091_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"
    closure_path = root / "docs/evidence/TASK_091_LIVE_EPHEMERAL_DRIVE_DIGEST_CLOSURE_0.8.0.json"
    auth_path = root / "docs/evidence/TASK_091_OWNER_AUTHORIZATION_0.8.0.json"
    live_workflow = root / ".github/workflows/task-091-live-ephemeral-drive-digest.yml"

    _require(not live_workflow.exists(), "STOP_TASK091_LIVE_WORKFLOW_STILL_PRESENT")

    task_bytes = task_path.read_bytes()
    payload_bytes = payload_path.read_bytes()
    closure_bytes = closure_path.read_bytes()
    auth_bytes = auth_path.read_bytes()

    _require(git_blob_sha(task_bytes) == EXPECTED_TASK_BLOB, "STOP_TASK091_TASK_BLOB")
    _require(git_blob_sha(payload_bytes) == EXPECTED_PAYLOAD_BLOB, "STOP_TASK091_PAYLOAD_BLOB")
    _require(git_blob_sha(closure_bytes) == EXPECTED_CLOSURE_BLOB, "STOP_TASK091_CLOSURE_BLOB")
    _require(git_blob_sha(auth_bytes) == EXPECTED_AUTH_BLOB, "STOP_TASK091_AUTH_BLOB")

    task = task_bytes.decode("utf-8")
    payload = json.loads(payload_bytes)
    closure = json.loads(closure_bytes)
    auth = json.loads(auth_bytes)

    _require("Fresh owner instruction: **2026-09-04 — `prossiga`**." in task, "STOP_TASK091_OWNER_AUTH")
    _require("remote-id SHA-256" in task, "STOP_TASK091_REDACTION_MARKER")
    _require(EXPECTED_REMOTE_ID_SHA256 in task, "STOP_TASK091_REMOTE_ID_HASH")
    _require(EXPECTED_SOURCE_SHA256 in task, "STOP_TASK091_SOURCE_SHA_TASK")
    _require(str(EXPECTED_SOURCE_BYTES) in task, "STOP_TASK091_SOURCE_BYTES_TASK")
    _require("No retry is authorized." in task, "STOP_TASK091_NO_RETRY_TASK")
    _require("complete live workflow source is not retained" in task.lower(), "STOP_TASK091_WORKFLOW_ARCHIVAL_POLICY")

    _require(payload["source"]["remote_id_redacted"] is True, "STOP_TASK091_PAYLOAD_REMOTE_ID_REDACTION")
    _require(payload["source"]["remote_id_sha256"] == EXPECTED_REMOTE_ID_SHA256, "STOP_TASK091_PAYLOAD_REMOTE_ID_HASH")
    _require(payload["source"]["expected_sha256"] == EXPECTED_SOURCE_SHA256, "STOP_TASK091_PAYLOAD_SOURCE_SHA")
    _require(payload["source"]["expected_bytes"] == EXPECTED_SOURCE_BYTES, "STOP_TASK091_PAYLOAD_SOURCE_BYTES")
    _require(_payload_self_hash(payload) == EXPECTED_REDACTED_PAYLOAD_SELF_HASH, "STOP_TASK091_PAYLOAD_SELF_HASH")
    _require(payload["evidence_payload_sha256_without_self_hash"] == EXPECTED_REDACTED_PAYLOAD_SELF_HASH, "STOP_TASK091_PAYLOAD_SELF_HASH_FIELD")
    _require(payload["status"] == "STOP_TASK091_LIVE_DRIVE_TO_EPHEMERAL_DIGEST", "STOP_TASK091_PAYLOAD_STATUS")
    _require(payload["reason"] == "RuntimeError:STOP_TASK091_HISTORICAL_COUNT_DRIFT", "STOP_TASK091_STOP_REASON")
    _require(payload["request_count"] == 2, "STOP_TASK091_REQUEST_COUNT")
    _require(payload["ephemeral_cleanup_verified"] is True, "STOP_TASK091_CLEANUP")

    expected_requests = [
        {"ordinal": 1, "method": "POST", "host": "oauth2.googleapis.com", "route_class": "OAUTH_TOKEN_EXCHANGE"},
        {"ordinal": 2, "method": "GET", "host": "www.googleapis.com", "route_class": "EXACT_DRIVE_MEDIA_GET"},
    ]
    _require(payload["requests"] == expected_requests, "STOP_TASK091_REQUEST_TRACE")
    _require(payload["authorization"]["single_use"] is True, "STOP_TASK091_PAYLOAD_SINGLE_USE")
    _require(payload["authorization"]["retry_authorized"] is False, "STOP_TASK091_PAYLOAD_RETRY")
    _require(payload["authorization"]["future_execution_authorized"] is False, "STOP_TASK091_PAYLOAD_FUTURE")

    archival = closure["archival_policy"]
    _require(archival["protected_main_target"] == "SQUASH_FINAL_REDACTED_TREE_ONLY", "STOP_TASK091_SQUASH_POLICY")
    _require(archival["full_live_workflow_source_in_final_tree"] is False, "STOP_TASK091_FULL_WORKFLOW_RETAINED")
    _require(archival["remote_identifier_in_final_tree"] is False, "STOP_TASK091_REMOTE_ID_RETAINED")
    _require(closure["prospective_authorization"]["pre_run_contract_blob_sha"] == EXPECTED_PRE_RUN_CONTRACT_BLOB, "STOP_TASK091_PRE_RUN_BLOB")
    _require(closure["execution"]["executed_workflow_blob_sha"] == EXPECTED_EXECUTED_WORKFLOW_BLOB, "STOP_TASK091_EXECUTED_WORKFLOW_BLOB")
    _require(closure["execution"]["run_id"] == 33873064071, "STOP_TASK091_RUN_ID")
    _require(closure["execution"]["job_id"] == 101023430264, "STOP_TASK091_JOB_ID")
    _require(closure["execution"]["second_run_observed"] is False, "STOP_TASK091_SECOND_RUN")
    _require(closure["source"]["remote_id_redacted"] is True, "STOP_TASK091_CLOSURE_REMOTE_ID_REDACTION")
    _require(closure["source"]["remote_id_sha256"] == EXPECTED_REMOTE_ID_SHA256, "STOP_TASK091_CLOSURE_REMOTE_ID_HASH")
    _require(closure["source"]["source_identity_gate_passed_before_stop"] is True, "STOP_TASK091_SOURCE_GATE")
    _require(closure["live_transport"]["guarded_request_count"] == 2, "STOP_TASK091_GUARDED_REQUEST_COUNT")
    _require(closure["live_transport"]["drive_media_gets"] == 1, "STOP_TASK091_DRIVE_GET_COUNT")
    _require(closure["live_transport"]["drive_metadata_list_search_requests"] == 0, "STOP_TASK091_DRIVE_DISCOVERY_COUNT")
    _require(closure["live_transport"]["drive_mutating_requests"] == 0, "STOP_TASK091_DRIVE_MUTATION")
    _require(closure["digest"]["pass_status_gate_before_stop"] is True, "STOP_TASK091_DIGEST_STATUS_GATE")
    _require(closure["digest"]["input_count_one_and_candidate_file_count_four_gate_passed_before_stop"] is True, "STOP_TASK091_DIGEST_FILE_GATE")
    _require(closure["digest"]["derived_candidates_persisted_remotely"] is False, "STOP_TASK091_DERIVED_PERSISTENCE")
    _require(closure["digest"]["derived_candidates_uploaded_as_artifact"] is False, "STOP_TASK091_DERIVED_ARTIFACT")
    _require(closure["digest"]["observed_counts_captured"] is False, "STOP_TASK091_OBSERVED_COUNTS_OVERCLAIM")
    _require(closure["digest"]["root_cause_status"] == "UNRESOLVED", "STOP_TASK091_ROOT_CAUSE_OVERCLAIM")
    _require(closure["artifact"]["durable_record_is_exact_original_payload"] is False, "STOP_TASK091_ARTIFACT_REDACTION_SEMANTICS")
    _require(closure["artifact"]["durable_redacted_record_self_hash"] == EXPECTED_REDACTED_PAYLOAD_SELF_HASH, "STOP_TASK091_REDACTED_RECORD_HASH")
    _require(closure["result"] == "STOP_TASK091_DIGEST_PROVEN_EPHEMERAL_HISTORICAL_COUNT_DRIFT_UNRESOLVED", "STOP_TASK091_CLOSURE_RESULT")
    for key, value in closure["hard_boundaries"].items():
        _require(value == 0, f"STOP_TASK091_HARD_BOUNDARY_{key.upper()}")

    _require(auth["authorization_type"] == "PROSPECTIVE_SINGLE_USE_OWNER_INSTRUCTION", "STOP_TASK091_AUTH_TYPE")
    _require(auth["issued_before_execution"] is True, "STOP_TASK091_AUTH_TIMING")
    _require(auth["owner_instruction"] == "2026-09-04: prossiga", "STOP_TASK091_AUTH_INSTRUCTION")
    _require(auth["pre_run_contract_blob_sha"] == EXPECTED_PRE_RUN_CONTRACT_BLOB, "STOP_TASK091_AUTH_PRE_RUN_BLOB")
    _require(auth["remote_target_redacted_in_final_tree"] is True, "STOP_TASK091_AUTH_REMOTE_REDACTION")
    _require(auth["consumed_by"]["run_id"] == 33873064071, "STOP_TASK091_AUTH_RUN")
    _require(auth["status"] == "CONSUMED_SINGLE_USE_NO_RETRY", "STOP_TASK091_AUTH_STATUS")
    _require(all(value is False for value in auth["exclusions"].values()), "STOP_TASK091_AUTH_EXCLUSION_ENABLED")

    # Final-tree safety scan: do not republish operational secret names or the raw remote ID.
    scan_paths = [task_path, payload_path, closure_path, auth_path]
    scan_text = "\n".join(path.read_text(encoding="utf-8") for path in scan_paths)
    forbidden_fragments = tuple(
        "_".join(parts)
        for parts in (
            ("GOOGLE", "DRIVE", "CLIENT", "SECRET"),
            ("GOOGLE", "DRIVE", "REFRESH", "TOKEN"),
            ("GOOGLE", "DRIVE", "CLIENT", "ID"),
        )
    )
    for fragment in forbidden_fragments:
        _require(fragment not in scan_text, f"STOP_TASK091_SENSITIVE_REFERENCE_{fragment}")

    return {
        "status": "PASS_TASK091_REDACTED_LIVE_DIGEST_EVIDENCE_OFFLINE",
        "run_id": 33873064071,
        "request_count": 2,
        "drive_media_gets": 1,
        "digest_passed_before_historical_comparison": True,
        "candidate_file_count_gate_passed": True,
        "historical_count_drift": True,
        "root_cause_status": "UNRESOLVED",
        "remote_identifier_redacted": True,
        "full_live_workflow_source_retained": False,
        "retry_authorized": False,
        "future_execution_authorized": False,
        "live_workflow_present": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_TASK091_REDACTED_LIVE_DIGEST_EVIDENCE_OFFLINE", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        raise SystemExit(91)
