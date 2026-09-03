#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.reconciliation.bounded_query_guard import (  # noqa: E402
    BoundedQueryGuard,
    validate_resolver_status,
)

EVIDENCE = ROOT / "docs/evidence/TASK_086_BOUNDED_NEXT_CONTRACT_QUERY_0.8.0.json"
PAYLOAD = ROOT / "docs/evidence/TASK_086_LIVE_ARTIFACT_PAYLOAD_0.8.0.json"
WORKFLOW_SOURCE = ROOT / "docs/evidence/TASK_086_HISTORICAL_LIVE_WORKFLOW_SOURCE_0.8.0.txt"
TASK_CONTRACT = ROOT / "docs/tasks/CODEX_TASK_086_BOUNDED_NEXT_CONTRACT_QUERY.md"
EXPECTED_HOST = "serv42.limeira.sp.gov.br"
EXPECTED_CANONICAL_SHA256 = "80cd4dd6ffe018eb3cd019e6b453d750265dd0199bb288ba077ee58fa4955f61"
EXPECTED_ARTIFACT_DIGEST = "sha256:27bdf72489ed68deecc21d7a09d2c17a5328c2a2a88d9951b9af2468e39da797"
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
    payload = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(payload, dict), f"STOP_TASK086_JSON_OBJECT_REQUIRED_{path.name}")
    return payload


def canonical_sha256(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run() -> dict:
    evidence = _load(EVIDENCE)
    payload = _load(PAYLOAD)
    workflow_source = WORKFLOW_SOURCE.read_text(encoding="utf-8")
    task_contract = TASK_CONTRACT.read_text(encoding="utf-8")

    _require(evidence.get("schema") == "TASK_086_BOUNDED_NEXT_CONTRACT_QUERY_EVIDENCE_V1", "STOP_TASK086_EVIDENCE_SCHEMA")
    _require(evidence.get("live_run", {}).get("run_id") == 33788639843, "STOP_TASK086_RUN_ID")
    _require(evidence.get("live_run", {}).get("job_id") == 100759492906, "STOP_TASK086_JOB_ID")
    _require(evidence.get("live_run", {}).get("head_sha") == "53f214ab64bdd1d475811586ea062362ae6d2ae3", "STOP_TASK086_RUN_HEAD")
    _require(evidence.get("artifact", {}).get("id") == 9906411493, "STOP_TASK086_ARTIFACT_ID")
    _require(evidence.get("artifact", {}).get("digest") == EXPECTED_ARTIFACT_DIGEST, "STOP_TASK086_ARTIFACT_DIGEST")
    _require(evidence.get("authorization", {}).get("consumed") is True, "STOP_TASK086_AUTHORIZATION_NOT_CONSUMED")
    _require(evidence.get("authorization", {}).get("retry_authorized") is False, "STOP_TASK086_RETRY_ENABLED")
    _require(evidence.get("authorization", {}).get("future_execution_authorized") is False, "STOP_TASK086_FUTURE_EXECUTION_ENABLED")

    observed_sha = canonical_sha256(payload)
    _require(observed_sha == EXPECTED_CANONICAL_SHA256, "STOP_TASK086_CANONICAL_SHA256")
    _require(evidence.get("live_run", {}).get("result_canonical_sha256") == observed_sha, "STOP_TASK086_EVIDENCE_PAYLOAD_SHA_MISMATCH")

    _require(payload.get("selected_task_id") == "RECTASK_6600049d5284824e9a0a44a6", "STOP_TASK086_SELECTED_TASK")
    _require(payload.get("pre_run_task_contract_sha") == "6ce5e4b9cc8f7c20d18f383a67ae82d2993e84ec", "STOP_TASK086_TASK_CONTRACT_SHA")
    _require("RECTASK_6600049d5284824e9a0a44a6" in task_contract, "STOP_TASK086_TASK_CONTRACT_ID_MISSING")
    _require("Maximum three HTTP requests total" in task_contract, "STOP_TASK086_TASK_CONTRACT_BUDGET_MISSING")
    _require("No future execution is authorized" in task_contract, "STOP_TASK086_TASK_CONTRACT_FUTURE_BLOCK_MISSING")

    max_requests = payload.get("max_http_requests")
    requests = payload.get("requests") or []
    _require(max_requests == 3, "STOP_TASK086_PAYLOAD_MAX_REQUESTS")
    _require(payload.get("request_count") == len(requests) == 3, "STOP_TASK086_REQUEST_COUNT")

    guard = BoundedQueryGuard(EXPECTED_HOST, max_requests)
    for expected_ordinal, row in enumerate(requests, start=1):
        _require(row.get("ordinal") == expected_ordinal, "STOP_TASK086_REQUEST_ORDINAL")
        params = {name: "<redacted>" for name in row.get("submitted_field_names") or []}
        observed = guard.authorize(
            f"https://{row.get('host')}{row.get('path')}",
            method=str(row.get("method") or ""),
            params=params,
        )
        _require(observed == row, "STOP_TASK086_REQUEST_REPLAY_MISMATCH")

    result = payload.get("resolver_result") or {}
    validate_resolver_status(str(result.get("status")), ALLOWED_STATUSES)
    _require(result.get("status") == "NO_MATCH", "STOP_TASK086_EXPECTED_NO_MATCH")
    _require(result.get("candidates") == [], "STOP_TASK086_CANDIDATES_NOT_EMPTY")
    _require(payload.get("candidate_summaries") == [], "STOP_TASK086_CANDIDATE_SUMMARIES_NOT_EMPTY")
    _require((result.get("evidence") or {}).get("form_discovery", {}).get("status") == "PASS_FORM_DISCOVERY", "STOP_TASK086_FORM_DISCOVERY")
    _require((result.get("evidence") or {}).get("submission", {}).get("autosubmit_relay", {}).get("status") == "PASS_PROVEN_AUTOSUBMIT_RELAY", "STOP_TASK086_RELAY_DISCOVERY")
    _require((result.get("evidence") or {}).get("submission", {}).get("relay_followup", {}).get("table_rows") == 16, "STOP_TASK086_RESULT_TABLE_NOT_INTERPRETABLE")

    boundaries = payload.get("hard_boundaries") or {}
    for key in (
        "contract_identity_assertions",
        "drive_reads",
        "drive_writes",
        "financial_identity_assertions",
        "publications",
        "queue_writes",
        "serving_writes",
        "state_registry_writes",
    ):
        _require(boundaries.get(key) == 0, f"STOP_TASK086_REMOTE_EFFECT_{key.upper()}")

    _require("permissions:\n  contents: read" in workflow_source, "STOP_TASK086_WORKFLOW_PERMISSION")
    _require('ALLOWED_HOST = "serv42.limeira.sp.gov.br"' in workflow_source, "STOP_TASK086_WORKFLOW_HOST_ALLOWLIST")
    _require("MAX_REQUESTS = 3" in workflow_source, "STOP_TASK086_WORKFLOW_REQUEST_BUDGET")
    _require("STOP_TASK086_HTTP_BUDGET_EXCEEDED" in workflow_source, "STOP_TASK086_WORKFLOW_BUDGET_STOP")
    _require("STOP_TASK086_ORIGIN_OUTSIDE_ALLOWLIST" in workflow_source, "STOP_TASK086_WORKFLOW_ORIGIN_STOP")
    for forbidden in ("schedule:", "workflow_run:", "pull_request_target:", "contents: write", "pull-requests: write", "secrets: inherit"):
        _require(forbidden not in workflow_source, f"STOP_TASK086_WORKFLOW_FORBIDDEN_{forbidden.rstrip(':').upper()}")

    return {
        "status": "PASS_TASK086_BOUNDED_QUERY_EVIDENCE_OFFLINE",
        "canonical_sha256": observed_sha,
        "request_count": len(requests),
        "allowed_host": EXPECTED_HOST,
        "resolver_status": result.get("status"),
        "candidate_count": len(result.get("candidates") or []),
        "artifact_digest": EXPECTED_ARTIFACT_DIGEST,
        "future_execution_authorized": False,
    }


def main() -> int:
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_TASK086_BOUNDED_QUERY_EVIDENCE_OFFLINE", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 86
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
