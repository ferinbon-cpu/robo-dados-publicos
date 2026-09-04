#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from robo_dados_publicos.reconciliation.bounded_query_guard import (
    BoundedQueryGuard,
    validate_resolver_status,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_089_BOUNDED_NEXT_EXECUTABLE_CONTRACT_QUERY_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_089_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"
WORKFLOW_SOURCE = ROOT / "docs/evidence/TASK_089_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
TASK_CONTRACT = ROOT / "docs/tasks/CODEX_TASK_089_BOUNDED_NEXT_EXECUTABLE_CONTRACT_QUERY.md"
AUTH = ROOT / "docs/evidence/TASK_089_OWNER_AUTHORIZATION_0.8.0.json"
CHAIN = ROOT / "docs/evidence/TASK_089_PRE_RUN_GATE_CHAIN_0.8.0.json"
POLICY = ROOT / "config/automation_policy.v1.json"
LIVE_WORKFLOW = ROOT / ".github/workflows/task-089-contract-resolver-live-once.yml"

EXPECTED_HOST = "serv42.limeira.sp.gov.br"
EXPECTED_CANONICAL_SHA256 = "9a18afe974028d969f58f885524a24a85b631eca4ddd88ddcc7e6ba556d199de"
EXPECTED_WORKFLOW_BLOB = "c5741a55a14e98736475ae271975963dd18d9691"
EXPECTED_TASK_BLOB = "7e568df40a2eda20e25da1ba3c2c27f18558ee83"
EXPECTED_ARTIFACT_DIGEST = "sha256:dc4fbe266c8bb3a8db09502e7098ef76fa88912bf10e7bcce8f8ac90c2bacca2"
ALLOWED_STATUSES = {
    "MATCH_CANDIDATE",
    "NO_MATCH",
    "STOP_CONTRACT_FORM_UNPROVEN",
    "STOP_MISSING_CONTRACT_OR_SUPPLIER_KEY",
    "STOP_CONTRACT_RELAY_ORIGIN_UNPROVEN",
    "STOP_CONTRACT_RESULT_SCHEMA_UNPROVEN",
}


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(obj, dict), f"STOP_TASK089_JSON_OBJECT_REQUIRED_{path.name}")
    return obj


def canonical_sha256(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def run() -> dict:
    evidence = _load(EVIDENCE)
    payload = _load(PAYLOAD)
    auth = _load(AUTH)
    chain = _load(CHAIN)
    policy = _load(POLICY)
    workflow_bytes = WORKFLOW_SOURCE.read_bytes()
    workflow_source = workflow_bytes.decode("utf-8")
    task_bytes = TASK_CONTRACT.read_bytes()
    task_contract = task_bytes.decode("utf-8")

    _require(not LIVE_WORKFLOW.exists(), "STOP_TASK089_LIVE_WORKFLOW_STILL_PRESENT")
    _require(git_blob_sha(workflow_bytes) == EXPECTED_WORKFLOW_BLOB, "STOP_TASK089_HISTORICAL_WORKFLOW_BLOB")
    _require(git_blob_sha(task_bytes) == EXPECTED_TASK_BLOB, "STOP_TASK089_TASK_CONTRACT_BLOB")
    _require(chain["live_workflow"]["original_blob_sha"] == EXPECTED_WORKFLOW_BLOB, "STOP_TASK089_CHAIN_WORKFLOW_BLOB")
    _require(chain["preserved_source"]["blob_sha"] == EXPECTED_WORKFLOW_BLOB, "STOP_TASK089_CHAIN_HISTORICAL_BLOB")
    _require(chain["preserved_source"]["exact_blob_match_to_executed_workflow"] is True, "STOP_TASK089_CHAIN_BLOB_IDENTITY")
    _require(chain["task_contract"]["commit_sha"] == "a1efbc2960012cc7fcda456beaf2f100e4fcfdbc", "STOP_TASK089_PRE_RUN_CONTRACT_COMMIT")
    _require(chain["task_contract"]["blob_sha"] == EXPECTED_TASK_BLOB, "STOP_TASK089_PRE_RUN_CONTRACT_BLOB")

    _require("Fresh owner authorization is the user's 2026-09-04 instruction `Prossiga e registre no drive`" in task_contract, "STOP_TASK089_PRE_RUN_OWNER_AUTH_MISSING")
    _require("Maximum three HTTP requests total" in task_contract, "STOP_TASK089_PRE_RUN_BUDGET_MISSING")
    _require("No future execution is authorized by this task" in task_contract, "STOP_TASK089_PRE_RUN_FUTURE_BLOCK_MISSING")
    _require("The live gate is single-use" in task_contract, "STOP_TASK089_PRE_RUN_SINGLE_USE_MISSING")

    _require(auth["authorization_source"]["issued_before_execution"] is True, "STOP_TASK089_OWNER_AUTH_NOT_PROSPECTIVE")
    _require(auth["authorization_source"]["instruction"] == "Prossiga e registre no drive", "STOP_TASK089_OWNER_INSTRUCTION")
    _require(auth["status"] == "CONSUMED_SINGLE_READ_ONLY_STATEFUL_QUERY", "STOP_TASK089_AUTH_NOT_CONSUMED")
    _require(auth["exclusions"]["retry"] is False, "STOP_TASK089_RETRY_ENABLED")
    _require(auth["exclusions"]["future_execution"] is False, "STOP_TASK089_FUTURE_EXECUTION_ENABLED")
    _require(auth["consumed_by"]["run_id"] == 33867790494, "STOP_TASK089_AUTH_RUN")

    observed_sha = canonical_sha256(payload)
    _require(observed_sha == EXPECTED_CANONICAL_SHA256, "STOP_TASK089_CANONICAL_SHA256")
    _require(evidence["live_run"]["result_canonical_sha256"] == observed_sha, "STOP_TASK089_EVIDENCE_PAYLOAD_SHA")
    _require(evidence["artifact"]["digest"] == EXPECTED_ARTIFACT_DIGEST, "STOP_TASK089_ARTIFACT_DIGEST")
    _require(payload["pre_run_task_contract_sha"] == "a1efbc2960012cc7fcda456beaf2f100e4fcfdbc", "STOP_TASK089_PAYLOAD_PRE_RUN_CONTRACT")
    _require(payload["selected_task_id"] == "RECTASK_bf460d6fbffa22124902553f", "STOP_TASK089_SELECTED_TASK")

    requests = payload["requests"]
    _require(payload["max_http_requests"] == 3, "STOP_TASK089_MAX_REQUESTS")
    _require(payload["request_count"] == len(requests) == 3, "STOP_TASK089_REQUEST_COUNT")
    guard = BoundedQueryGuard(EXPECTED_HOST, 3)
    for ordinal, row in enumerate(requests, start=1):
        _require(row["ordinal"] == ordinal, "STOP_TASK089_REQUEST_ORDINAL")
        params = {name: "<redacted>" for name in row.get("submitted_field_names", [])}
        replayed = guard.authorize(
            f"https://{row['host']}{row['path']}",
            method=row["method"],
            params=params,
        )
        _require(replayed == row, "STOP_TASK089_REQUEST_REPLAY")

    result = payload["resolver_result"]
    validate_resolver_status(result["status"], ALLOWED_STATUSES)
    _require(result["status"] == "NO_MATCH", "STOP_TASK089_EXPECTED_NO_MATCH")
    _require(result["candidates"] == [], "STOP_TASK089_CANDIDATES")
    _require(payload["candidate_summaries"] == [], "STOP_TASK089_CANDIDATE_SUMMARIES")
    _require(result["evidence"]["form_discovery"]["status"] == "PASS_FORM_DISCOVERY", "STOP_TASK089_FORM_DISCOVERY")
    _require(result["evidence"]["submission"]["autosubmit_relay"]["status"] == "PASS_PROVEN_AUTOSUBMIT_RELAY", "STOP_TASK089_RELAY")
    _require(result["evidence"]["submission"]["relay_followup"]["table_rows"] == 19, "STOP_TASK089_TABLE_ROWS")

    for key, value in payload["hard_boundaries"].items():
        _require(value == 0, f"STOP_TASK089_REMOTE_EFFECT_{key.upper()}")

    _require("permissions:\n  contents: read" in workflow_source, "STOP_TASK089_WORKFLOW_PERMISSION")
    _require("persist-credentials: false" in workflow_source, "STOP_TASK089_WORKFLOW_CREDENTIAL_PERSISTENCE")
    _require('ALLOWED_HOST = "serv42.limeira.sp.gov.br"' in workflow_source, "STOP_TASK089_WORKFLOW_HOST")
    _require("MAX_REQUESTS = 3" in workflow_source, "STOP_TASK089_WORKFLOW_BUDGET")
    for forbidden in ("schedule:", "workflow_run:", "pull_request_target:", "contents: write", "pull-requests: write", "secrets: inherit"):
        _require(forbidden not in workflow_source, f"STOP_TASK089_WORKFLOW_FORBIDDEN_{forbidden.rstrip(':').upper()}")

    t1 = policy["tiers"]["T1_REMOTE_READONLY"]
    _require("Auto execution requires" in t1["description"], "STOP_TASK089_T1_AUTO_SEMANTICS_DRIFT")
    _require(evidence["governance_interpretation"]["automation_policy_auto_execution_promoted"] is False, "STOP_TASK089_AUTO_PROMOTION")
    _require(evidence["governance_interpretation"]["future_remote_execution_authorized"] is False, "STOP_TASK089_FUTURE_REMOTE")
    _require(evidence["execution_record_status"].startswith("RECORDED_TASK089_"), "STOP_TASK089_SELF_PASS_STATUS")
    _require("result" not in evidence, "STOP_TASK089_EVIDENCE_SELF_PASS_FIELD")

    return {
        "status": "PASS_TASK089_BOUNDED_QUERY_EVIDENCE_OFFLINE",
        "canonical_sha256": observed_sha,
        "workflow_blob_sha": EXPECTED_WORKFLOW_BLOB,
        "task_contract_blob_sha": EXPECTED_TASK_BLOB,
        "request_count": len(requests),
        "resolver_status": result["status"],
        "candidate_count": 0,
        "future_execution_authorized": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_TASK089_BOUNDED_QUERY_EVIDENCE_OFFLINE", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        raise SystemExit(89)
