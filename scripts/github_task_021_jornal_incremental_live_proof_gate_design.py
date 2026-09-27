#!/usr/bin/env python3
"""Fail-closed structural/semantic T0 gate for TASK 021."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    contract = load("config/jornal_incremental_live_proof_gate.v1.json")
    evidence = load("docs/evidence/TASK_021_JORNAL_INCREMENTAL_LIVE_PROOF_GATE_DESIGN_0.8.0.json")
    task020_contract = load("config/jornal_incremental_recurrence_readiness.v1.json")
    task020_evidence = load("docs/evidence/TASK_020_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN_0.8.0.json")
    closure = load("docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_CLOSURE_0.8.0.json")
    auth = contract.get("authorizations", {})
    checkpoint = contract.get("checkpoint", {})
    bounds = contract.get("network_bounds_for_future_separately_authorized_proof", {})
    effects = evidence.get("effects", {})
    release = evidence.get("release_boundary", {})
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    task020_gate = subprocess.run(
        [sys.executable, str(ROOT / "scripts/github_task_020_jornal_incremental_recurrence_readiness_design_gate.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    task021_workflows = list((ROOT / ".github/workflows").glob("*task-021*"))
    required_false = {
        "live_incremental_proof_authorized", "source_network_authorized",
        "workflow_dispatch_authorized", "future_batch_execution_authorized",
        "document_download_authorized", "drive_read_authorized",
        "drive_write_authorized", "processing_authorized",
        "reconciliation_authorized", "publication_authorized",
        "checkpoint_advance_authorized", "schedule_authorized",
        "recurrence_authorized", "automatic_retry_authorized",
        "task_018_authorization_reuse_authorized",
    }
    checks = {
        "task020_present_and_pass": task020_gate.returncode == 0 and task020_evidence.get("status") == "PASS_INCREMENTAL_RECURRENCE_READINESS_DESIGN_OFFLINE",
        "task020_proposal_only_unchanged": task020_contract.get("continuation_semantics", {}).get("planner_output_is_proposal_only") is True and task020_contract.get("continuation_semantics", {}).get("checkpoint_advance") == "ONLY_AFTER_ALL_PROPOSED_NEW_ITEMS_COMPLETE_DOWNSTREAM_AND_FINAL_READBACK",
        "task018_closed_consumed": closure.get("status") == "CLOSED_SUCCESS_AUTHORIZATION_CONSUMED" and closure.get("one_shot", {}).get("single_execution_attempt_remaining") is False,
        "task018_no_schedule_recurrence_retry": all(closure.get("one_shot", {}).get(k) is False for k in ("schedule_authorized", "recurrence_authorized", "retry_authorized")),
        "contract_t0_fixed_source": contract.get("tier") == "T0_OFFLINE_DESIGN" and contract.get("source_id") == "LIMEIRA_JORNAL_OFICIAL" and contract.get("future_capability") == "BOUNDED_DISCOVERY_READ_ONLY",
        "all_authorizations_false": required_false.issubset(auth) and all(auth.get(k) is False for k in required_false),
        "future_bounds_fail_closed": bounds.get("host_allowlist") == ["www.limeira.sp.gov.br"] and bounds.get("https_required") is True and bounds.get("max_discovery_pages") == 8 and bounds.get("max_http_gets") == 8 and bounds.get("timeout_seconds") == 20 and bounds.get("max_response_bytes_per_page") == 2000000 and bounds.get("automatic_retries") == 0 and bounds.get("redirect_to_non_allowlisted_host") is False and bounds.get("dynamic_pagination_beyond_ceiling") is False and bounds.get("required_discovery_status") == "PASS_DISCOVERY" and bounds.get("max_new_items") == task020_contract.get("bounds", {}).get("max_new_items_per_cycle") and bounds.get("document_downloads") == 0,
        "real_checkpoint_formally_blocked": checkpoint.get("task_018_closure_contains_all_12_identities") is False and checkpoint.get("canonical_real_snapshot_status") == "BLOCKED_NOT_PINNED" and checkpoint.get("synthetic_fixture_is_operational_authority") is False and checkpoint.get("missing_or_insufficient_policy") == "STOP_REAL_CHECKPOINT_NOT_PINNED",
        "offline_evidence": evidence.get("status") == "PASS_INCREMENTAL_LIVE_PROOF_GATE_DESIGN_OFFLINE" and evidence.get("authorization", {}).get("live_proof_executed") is False and evidence.get("authorization", {}).get("live_proof_authorized") is False,
        "zero_remote_effects": len(effects) >= 12 and all(value == 0 for value in effects.values()),
        "no_task021_live_workflow": not task021_workflows,
        "offline_ci_integration": "python scripts/github_task_021_jornal_incremental_live_proof_gate_design.py" in ci,
        "release_boundary": release == {"active": "0.7.0", "candidate": "0.8.0", "B1": "PENDING", "B2": "PENDING", "B3": "PENDING", "gold_2025": "UNKNOWN/BLOCKED"},
        "all_required_stops_documented": all(stop in (ROOT / "docs/tasks/CODEX_TASK_021_JORNAL_INCREMENTAL_LIVE_PROOF_GATE_DESIGN.md").read_text(encoding="utf-8") for stop in ("STOP_DISCOVERY_NOT_COMPLETE", "STOP_KNOWN_ITEM_MISSING", "STOP_KNOWN_ITEM_DRIFT", "STOP_DUPLICATE_EDITION", "STOP_NON_MONOTONIC_NEW_ITEM", "STOP_NEW_ITEM_BOUND_EXCEEDED", "STOP_BAD_ITEM_CONTRACT", "STOP_LIVE_PROOF_NOT_AUTHORIZED", "STOP_TASK_018_AUTHORIZATION_REUSE", "STOP_REAL_CHECKPOINT_NOT_PINNED")),
    }
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"status": "PASS" if not failed else "STOP", "checks": checks, "failed_checks": failed}, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
