#!/usr/bin/env python3
"""Fail-closed repository gate for the T0 TASK 023 implementation review."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.journal.bounded_live_proof import EXPECTED_INTEGRITY, load_pinned_checkpoint


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def gate(path: str) -> bool:
    return subprocess.run([sys.executable, str(ROOT / path)], cwd=ROOT,
                          capture_output=True, text=True).returncode == 0


def main() -> int:
    config = load("config/jornal_bounded_live_incremental_proof.v1.json")
    evidence = load("docs/evidence/TASK_023_JORNAL_BOUNDED_LIVE_INCREMENTAL_PROOF_IMPLEMENTATION_REVIEW_0.8.0.json")
    fixture = load("tests/fixtures/task_023_synthetic_scenarios.json")
    checkpoint, checkpoint_result = load_pinned_checkpoint(
        ROOT / config.get("checkpoint", {}).get("path", "MISSING")
    )
    auth = config.get("authorization", {})
    boundary = config.get("future_discovery_boundary", {})
    effects = evidence.get("effects", {})
    evidence_auth = evidence.get("authorizations", {})
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    forbidden_workflows = list((ROOT / ".github/workflows").glob("*task-023*"))
    checks = {
        "base_and_tier": evidence.get("base_sha") == "f8fb872ea0bddcc9510363173649afb837c22cf8" and config.get("tier") == evidence.get("tier") == "T0_OFFLINE",
        "real_checkpoint_exact": checkpoint is not None and checkpoint_result.get("status") == "PASS_REAL_CHECKPOINT_PINNED" and checkpoint_result.get("canonical_payload_sha256") == EXPECTED_INTEGRITY and checkpoint.get("item_count") == 12 and checkpoint["items"][-1]["edition"] == 7315,
        "bounded_task021_budget": boundary == {"operation": "BOUNDED_DISCOVERY_READ_ONLY", "minimum_surface": "TASK_021_PINNED_MODERN_DISCOVERY_SURFACE", "max_requests": 8, "max_pages": 8, "max_new_items": 8, "automatic_retry": False, "pagination_expansion": False, "document_downloads": 0},
        "all_capabilities_blocked": auth and all(auth.get(key) is False for key in ("live_incremental_proof_authorized", "synthetic_test_authorization_is_operational", "downstream_authorized", "checkpoint_advance_authorized", "future_batch_execution_authorized", "recurrence_authorized", "schedule_authorized", "automatic_t2", "automatic_t3")),
        "evidence_pass": evidence.get("status") == "PASS_JORNAL_BOUNDED_LIVE_INCREMENTAL_PROOF_IMPLEMENTATION_REVIEW_OFFLINE" and evidence.get("fake_transport_scenarios") == "PASS" and evidence.get("release_boundary_unchanged") is True,
        "zero_effects": len(effects) >= 13 and all(value == 0 for value in effects.values()),
        "evidence_authorizations_false": evidence_auth and all(value is False for value in evidence_auth.values()),
        "task018_not_rerun": evidence.get("task_018_rerun") is False,
        "synthetic_fixture_only": fixture.get("synthetic_test_only") is True and fixture.get("operational_authority") is False and len(fixture.get("scenarios", [])) >= 16,
        "prior_gates_pass": all(gate(path) for path in ("scripts/github_task_020_jornal_incremental_recurrence_readiness_design_gate.py", "scripts/github_task_021_jornal_incremental_live_proof_gate_design.py", "scripts/github_task_022_jornal_real_checkpoint_pinning_review_gate.py")),
        "no_live_workflow": not forbidden_workflows,
        "ci_t0_gate": "python scripts/github_task_023_jornal_bounded_live_incremental_proof_implementation_review_gate.py" in ci,
    }
    failed = [name for name, passed in checks.items() if not passed]
    print(json.dumps({"status": "PASS_JORNAL_BOUNDED_LIVE_INCREMENTAL_PROOF_IMPLEMENTATION_REVIEW_OFFLINE" if not failed else "STOP", "checks": checks, "failed_checks": failed}, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
