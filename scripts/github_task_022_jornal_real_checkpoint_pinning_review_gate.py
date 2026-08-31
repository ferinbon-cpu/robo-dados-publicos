#!/usr/bin/env python3
"""Fail-closed T0 gate for the TASK 022 historical checkpoint review."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def run_gate(path: str) -> bool:
    return subprocess.run([sys.executable, str(ROOT / path)], cwd=ROOT, capture_output=True, text=True).returncode == 0


def main() -> int:
    contract = load("config/jornal_real_checkpoint_pinning_review.v1.json")
    evidence = load("docs/evidence/TASK_022_JORNAL_REAL_CHECKPOINT_PINNING_REVIEW_0.8.0.json")
    closure = load("docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_CLOSURE_0.8.0.json")
    task020 = load("docs/evidence/TASK_020_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN_0.8.0.json")
    task021 = load("docs/evidence/TASK_021_JORNAL_INCREMENTAL_LIVE_PROOF_GATE_DESIGN_0.8.0.json")
    discovery = load("config/limeira_sources_discovery.json")
    auth = contract.get("authorizations", {})
    audit = evidence.get("audit", {})
    effects = evidence.get("effects", {})
    reconciliation = evidence.get("task_018_reconciliation", {})
    release = evidence.get("release_boundary", {})
    journal = {row.get("source_id"): row for row in discovery.get("surfaces", [])}.get("LIMEIRA_JORNAL_OFICIAL", {})
    required_false = {
        "source_network_authorized", "drive_read_authorized", "drive_write_authorized",
        "document_download_from_source_authorized", "workflow_dispatch_authorized",
        "processing_authorized", "downstream_authorized", "publication_authorized",
        "checkpoint_advance_authorized", "future_batch_execution_authorized",
        "schedule_authorized", "recurrence_authorized", "automatic_retry_authorized",
        "task_018_rerun_authorized", "live_proof_authorized",
    }
    snapshot = ROOT / "docs/evidence/TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_0.8.0.json"
    checks = {
        "task018_closure_present_consumed": closure.get("status") == "CLOSED_SUCCESS_AUTHORIZATION_CONSUMED" and closure.get("one_shot", {}).get("single_execution_attempt_remaining") is False,
        "task018_identity_reconciled": reconciliation == {
            "run_id": closure.get("execution", {}).get("run_id"),
            "batch_id": closure.get("one_shot", {}).get("batch_id"),
            "execution_head_sha": closure.get("execution", {}).get("head_sha"),
            "closure_status": closure.get("status"),
            "batch_status": closure.get("outcome", {}).get("status"),
            "discovered": closure.get("outcome", {}).get("discovered"),
            "processed": closure.get("outcome", {}).get("processed"),
            "checkpoint_remaining": closure.get("outcome", {}).get("checkpoint_remaining"),
            "item_local_failures": closure.get("outcome", {}).get("item_local_failures"),
            "authorization_consumed": True,
            "task_018_rerun_authorized": False,
        } and reconciliation.get("processed") == 12 and reconciliation.get("checkpoint_remaining") == 0 and reconciliation.get("item_local_failures") == 0,
        "task020_pass": task020.get("status") == "PASS_INCREMENTAL_RECURRENCE_READINESS_DESIGN_OFFLINE" and run_gate("scripts/github_task_020_jornal_incremental_recurrence_readiness_design_gate.py"),
        "task021_design_pass_unchanged": task021.get("status") == "PASS_INCREMENTAL_LIVE_PROOF_GATE_DESIGN_OFFLINE" and task021.get("checkpoint_assessment", {}).get("real_checkpoint_status") == "BLOCKED_NOT_PINNED" and run_gate("scripts/github_task_021_jornal_incremental_live_proof_gate_design.py"),
        "contract_t0": contract.get("task") == "TASK_022" and contract.get("tier") == "T0_OFFLINE" and contract.get("source_id") == "LIMEIRA_JORNAL_OFICIAL",
        "all_operational_authorizations_false": required_false.issubset(auth) and all(auth.get(key) is False for key in required_false),
        "explicit_insufficient_stop": contract.get("decision") == evidence.get("status") == "STOP_REAL_CHECKPOINT_EVIDENCE_INSUFFICIENT" and contract.get("real_checkpoint_status") == evidence.get("real_checkpoint_status") == "BLOCKED_NOT_PINNED" and evidence.get("item_count") == 0 and evidence.get("live_proof_authorized") is False,
        "no_false_snapshot": not snapshot.exists(),
        "artifact_audit_truthful": audit.get("historical_github_artifact_reads") == 0 and audit.get("historical_artifact", {}).get("artifact_read_attempted") is True and audit.get("historical_artifact", {}).get("artifact_read_completed") is False and audit.get("historical_artifact", {}).get("fallback_to_source_or_drive_performed") is False,
        "identity_gap_explicit": audit.get("properties_missing_for_each_item") == ["edition", "publication_date", "document_url", "source_id", "logical_key"] and audit.get("reconstruction_by_assumed_sequence_performed") is False and audit.get("synthetic_fixture_used_as_operational_authority") is False,
        "zero_effects": len(effects) == 12 and all(value == 0 for value in effects.values()),
        "source_and_release_boundaries": journal.get("status") == "LIVE_VALIDATED" and journal.get("production_collection_enabled") is False and release == {"active": "0.7.0", "candidate": "0.8.0", "B1": "PENDING", "B2": "PENDING", "B3": "PENDING", "gold_2025": "UNKNOWN/BLOCKED"},
        "ci_integration": "python scripts/github_task_022_jornal_real_checkpoint_pinning_review_gate.py" in (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8"),
    }
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"status": "PASS_TASK_022_BLOCKED_REVIEW" if not failed else "STOP", "decision": evidence.get("status"), "checks": checks, "failed_checks": failed}, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
