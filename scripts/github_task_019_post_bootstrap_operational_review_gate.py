#!/usr/bin/env python3
"""Fail-closed offline gate for TASK 019 post-bootstrap review."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    review = load_json(
        "docs/evidence/TASK_019_POST_BOOTSTRAP_OPERATIONAL_REVIEW_0.8.0.json"
    )
    closure = load_json(
        "docs/evidence/TASK_018_FULL_OPERATIONAL_BOOTSTRAP_CLOSURE_0.8.0.json"
    )
    policy = load_json("config/automation_policy.v1.json")
    bootstrap = load_json("config/operational_bootstrap.full.v1.json")
    discovery = load_json("config/limeira_sources_discovery.json")
    status_text = (ROOT / "STATUS_0.8.0.md").read_text(encoding="utf-8")
    task_text = (
        ROOT / "docs/tasks/CODEX_TASK_019_POST_BOOTSTRAP_OPERATIONAL_REVIEW.md"
    ).read_text(encoding="utf-8")

    gates = {x.get("id"): x for x in policy.get("gates", [])}
    task018_policy = gates.get("TASK_018_FULL_OPERATIONAL_BOOTSTRAP", {})
    surfaces = {x.get("source_id"): x for x in discovery.get("surfaces", [])}
    journal = surfaces.get("LIMEIRA_JORNAL_OFICIAL", {})
    outcome = closure.get("outcome", {})
    publication = closure.get("publication", {})
    one_shot = closure.get("one_shot", {})
    release = review.get("release_boundary", {})
    conclusions = review.get("operational_conclusions", {})
    next_actions = review.get("next_actions", {})
    effects = review.get("effects_of_task_019", {})

    checks = {
        "review_status": review.get("status")
        == "PASS_POST_BOOTSTRAP_OPERATIONAL_REVIEW_OFFLINE",
        "review_tier": review.get("tier") == "T0_OFFLINE",
        "closure_status": closure.get("status")
        == "CLOSED_SUCCESS_AUTHORIZATION_CONSUMED",
        "run_identity": closure.get("execution", {}).get("run_id") == 33392616951
        and closure.get("execution", {}).get("github_run_attempt") == 1
        and closure.get("execution", {}).get("conclusion") == "success",
        "batch_identity": one_shot.get("batch_id") == "BATCH-CBBF70ADCA619C9C",
        "batch_complete": outcome.get("status") == "COMPLETE"
        and outcome.get("discovered") == 12
        and outcome.get("processed") == 12
        and outcome.get("item_local_failures") == 0
        and outcome.get("checkpoint_remaining") == 0,
        "publication_final": publication.get("status")
        == "PUBLISHED_CREATE_ONLY_READBACK_VERIFIED"
        and publication.get("manifest_written_last") is True
        and publication.get("final_readback_verified") is True,
        "one_shot_consumed": one_shot.get("single_execution_attempt_remaining")
        is False
        and one_shot.get("retry_authorized") is False
        and one_shot.get("second_execution_authorized") is False,
        "journal_stays_live_validated": journal.get("status") == "LIVE_VALIDATED"
        and journal.get("production_collection_enabled") is False
        and conclusions.get("jornal_oficial_source_status") == "LIVE_VALIDATED"
        and conclusions.get("recurrence_eligibility") == "NOT_PROMOTED_BY_TASK_019",
        "task018_policy_still_manual": task018_policy.get("auto_allowed") is False
        and task018_policy.get("schedule") is False
        and task018_policy.get("recurrence") is False
        and task018_policy.get("future_batch_execution_authorized") is False,
        "policy_default_block": policy.get("default_decision") == "BLOCK"
        and policy.get("policy_invariants", {}).get("future_batch_execution_authorized")
        is False,
        "t2_t3_still_human_gated": policy.get("tiers", {})
        .get("T2_CREATE_ONLY", {})
        .get("auto_execution")
        == "BLOCKED"
        and policy.get("tiers", {})
        .get("T3_MUTATING_OR_PUBLICATION", {})
        .get("auto_execution")
        == "BLOCKED",
        "bootstrap_scope_frozen": bootstrap.get("schedule") is False
        and bootstrap.get("recurrence") is False
        and bootstrap.get("automatic_retry") is False
        and bootstrap.get("release_boundary", {}).get("B1") == "PENDING"
        and bootstrap.get("release_boundary", {}).get("B2") == "PENDING"
        and bootstrap.get("release_boundary", {}).get("B3") == "PENDING",
        "release_boundary_preserved": release.get("active") == "0.7.0"
        and release.get("candidate") == "0.8.0"
        and release.get("closed_annual_series") == "2016-2024"
        and release.get("year_2025") == "PROVEN_STRUCTURAL_RECENT"
        and release.get("S1_NUM_POPU") == "NOT_PROVEN"
        and release.get("S2_FINANCIAL_ALIAS_BRIDGE") == "NOT_PROVEN"
        and release.get("annual_closure_status") == "UNKNOWN"
        and release.get("semantic_comparability_status") == "UNKNOWN"
        and release.get("gold_2025") == "UNKNOWN/BLOCKED"
        and release.get("year_2026") == "UNPROVEN_CURRENT_YEAR"
        and release.get("B1") == "PENDING"
        and release.get("B2") == "PENDING"
        and release.get("B3") == "PENDING",
        "canonical_status_matches": "0.7.0 ACTIVE" in status_text
        and "0.8.0 CANDIDATE" in status_text
        and "B1" in status_text
        and "B2" in status_text
        and "B3" in status_text,
        "next_actions_separated": next_actions.get("release_track")
        == "WAIT_AUTHORITATIVE_FNDE_B1_B2_B3_RESPONSES_AND_USE_OFFLINE_RESPONSE_INTAKE_GATE"
        and next_actions.get("engineering_track")
        == "TASK_020_T0_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN"
        and next_actions.get("task_020_remote_effects_authorized") is False,
        "task_doc_explicit_no_recurrence_promotion": "no `RECURRENCE_ELIGIBLE` promotion"
        in task_text
        and "TASK_020_T0_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN"
        in task_text,
        "zero_remote_effects": all(int(effects.get(k, -1)) == 0 for k in (
            "source_network",
            "drive_reads",
            "drive_writes",
            "publication_writes",
            "workflow_dispatch",
            "retry",
            "cleanup",
            "release_promotion",
            "semantic_promotion_2025",
        )),
    }

    failed = sorted(k for k, ok in checks.items() if not ok)
    result = {
        "gate": "TASK_019_POST_BOOTSTRAP_OPERATIONAL_REVIEW",
        "status": "PASS" if not failed else "STOP_TASK_019_REVIEW_DRIFT",
        "checks": checks,
        "failed_checks": failed,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
