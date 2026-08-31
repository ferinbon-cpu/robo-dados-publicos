#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 020 Jornal incremental readiness."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.journal.incremental_readiness import plan_incremental_readiness


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def item(edition: int, day: int) -> dict:
    return {
        "edition": edition,
        "publication_date": f"2026-08-{day:02d}",
        "document_url": f"https://www.limeira.sp.gov.br/jornaloficial/edicao/{edition}.pdf",
        "source_id": f"LIMEIRA_JO_{edition:05d}",
        "logical_key": f"limeira/jornal_oficial/edicao/{edition}",
    }


def main() -> int:
    evidence = load_json(
        "docs/evidence/TASK_020_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN_0.8.0.json"
    )
    contract = load_json("config/jornal_incremental_recurrence_readiness.v1.json")
    task019 = load_json(
        "docs/evidence/TASK_019_POST_BOOTSTRAP_OPERATIONAL_REVIEW_0.8.0.json"
    )
    closure = load_json(
        "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_CLOSURE_0.8.0.json"
    )
    policy = load_json("config/automation_policy.v1.json")
    discovery = load_json("config/limeira_sources_discovery.json")
    task_text = (
        ROOT / "docs/tasks/CODEX_TASK_020_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN.md"
    ).read_text(encoding="utf-8")

    journal = {
        row.get("source_id"): row for row in discovery.get("surfaces", [])
    }.get("LIMEIRA_JORNAL_OFICIAL", {})
    task018_policy = {
        row.get("id"): row for row in policy.get("gates", [])
    }.get("TASK_018_FULL_OPERATIONAL_BOOTSTRAP", {})

    baseline = [item(7310, 10), item(7311, 11)]
    no_change = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PASS_DISCOVERY",
        discovered_items=baseline,
        max_new_items=8,
    )
    append_only = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PASS_DISCOVERY",
        discovered_items=baseline + [item(7312, 12)],
        max_new_items=8,
    )
    partial = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED",
        discovered_items=baseline,
        max_new_items=8,
    )
    missing = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PASS_DISCOVERY",
        discovered_items=[baseline[1]],
        max_new_items=8,
    )
    drifted = [dict(x) for x in baseline]
    drifted[0]["document_url"] = "https://www.limeira.sp.gov.br/jornaloficial/drift.pdf"
    drift = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PASS_DISCOVERY",
        discovered_items=drifted,
        max_new_items=8,
    )
    duplicate = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PASS_DISCOVERY",
        discovered_items=baseline + [dict(baseline[-1])],
        max_new_items=8,
    )
    old_new = item(7309, 9)
    non_monotonic = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PASS_DISCOVERY",
        discovered_items=[old_new] + baseline,
        max_new_items=8,
    )
    too_many = plan_incremental_readiness(
        checkpoint_status="COMPLETE",
        checkpoint_items=baseline,
        discovery_status="PASS_DISCOVERY",
        discovered_items=baseline + [item(7312 + i, 12 + i) for i in range(9)],
        max_new_items=8,
    )

    release = evidence.get("release_boundary", {})
    operational = evidence.get("operational_state", {})
    continuation = contract.get("continuation_semantics", {})
    activation = contract.get("recurrence_activation", {})
    effects = evidence.get("effects_of_task_020", {})

    checks = {
        "task019_points_to_task020": task019.get("next_actions", {}).get("engineering_track")
        == "TASK_020_T0_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN"
        and task019.get("next_actions", {}).get("task_020_remote_effects_authorized") is False,
        "task018_closed_and_consumed": closure.get("status")
        == "CLOSED_SUCCESS_AUTHORIZATION_CONSUMED"
        and closure.get("one_shot", {}).get("single_execution_attempt_remaining") is False,
        "journal_stays_live_validated_disabled": journal.get("status") == "LIVE_VALIDATED"
        and journal.get("production_collection_enabled") is False,
        "policy_default_block": policy.get("default_decision") == "BLOCK"
        and policy.get("policy_invariants", {}).get("future_batch_execution_authorized") is False,
        "task018_policy_still_one_shot": task018_policy.get("auto_allowed") is False
        and task018_policy.get("schedule") is False
        and task018_policy.get("recurrence") is False
        and task018_policy.get("future_batch_execution_authorized") is False,
        "t2_t3_still_blocked": policy.get("tiers", {}).get("T2_CREATE_ONLY", {}).get("auto_execution")
        == "BLOCKED"
        and policy.get("tiers", {}).get("T3_MUTATING_OR_PUBLICATION", {}).get("auto_execution")
        == "BLOCKED",
        "contract_is_t0": contract.get("task") == "TASK_020"
        and contract.get("tier") == "T0_OFFLINE"
        and contract.get("source_id") == "LIMEIRA_JORNAL_OFICIAL",
        "activation_remains_false": activation.get("readiness_design_only") is True
        and activation.get("recurrence_authorized") is False
        and activation.get("schedule_authorized") is False
        and activation.get("cadence_selected") is False
        and activation.get("future_batch_execution_authorized") is False
        and activation.get("automatic_t2_authorized") is False
        and activation.get("automatic_t3_authorized") is False,
        "continuation_is_atomic": continuation.get("planner_output_is_proposal_only") is True
        and continuation.get("checkpoint_advance")
        == "ONLY_AFTER_ALL_PROPOSED_NEW_ITEMS_COMPLETE_DOWNSTREAM_AND_FINAL_READBACK"
        and continuation.get("partial_or_systemic_failure")
        == "KEEP_PREVIOUS_COMPLETED_CHECKPOINT_UNCHANGED"
        and continuation.get("partial_checkpoint_commit") is False
        and continuation.get("automatic_retry") is False,
        "no_change_semantics": no_change.get("status") == "NO_CHANGE_IDEMPOTENT"
        and no_change.get("new_item_count") == 0
        and no_change.get("remote_effects_authorized") is False,
        "append_only_semantics": append_only.get("status") == "NEW_ITEMS_APPEND_ONLY"
        and append_only.get("new_item_count") == 1
        and append_only.get("new_items", [])[0].get("edition") == 7312
        and append_only.get("checkpoint_candidate", {}).get("advance_allowed") is False,
        "partial_discovery_stops": partial.get("status") == "STOP_DISCOVERY_NOT_COMPLETE",
        "missing_known_item_stops": missing.get("status") == "STOP_KNOWN_ITEM_MISSING",
        "known_item_drift_stops": drift.get("status") == "STOP_KNOWN_ITEM_DRIFT",
        "duplicate_stops": duplicate.get("status") == "STOP_DUPLICATE_EDITION",
        "non_monotonic_stops": non_monotonic.get("status") == "STOP_NON_MONOTONIC_NEW_ITEM",
        "bound_exceeded_stops": too_many.get("status") == "STOP_NEW_ITEM_BOUND_EXCEEDED",
        "evidence_status": evidence.get("status")
        == "PASS_INCREMENTAL_RECURRENCE_READINESS_DESIGN_OFFLINE"
        and evidence.get("tier") == "T0_OFFLINE",
        "operational_not_promoted": operational.get("recurrence_readiness")
        == "INCREMENTAL_DECISION_SEMANTICS_OFFLINE_PROVEN_ONLY"
        and operational.get("recurrence_authorized") is False
        and operational.get("schedule_authorized") is False
        and operational.get("live_incremental_execution_authorized") is False,
        "release_boundary_preserved": release.get("active") == "0.7.0"
        and release.get("candidate") == "0.8.0"
        and release.get("release_promotion_performed") is False
        and release.get("B1") == "PENDING"
        and release.get("B2") == "PENDING"
        and release.get("B3") == "PENDING"
        and release.get("gold_2025") == "UNKNOWN/BLOCKED",
        "zero_effects": effects and all(value == 0 for value in effects.values()),
        "task_doc_forbids_activation": "does **not** select or activate a clock cadence" in task_text
        and "No `schedule`, automatic trigger, or recurrence workflow may be added by this task." in task_text,
    }

    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"status": "PASS" if not failed else "STOP", "checks": checks, "failed_checks": failed}, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
