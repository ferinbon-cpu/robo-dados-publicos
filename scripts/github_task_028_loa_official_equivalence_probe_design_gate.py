#!/usr/bin/env python3
"""Fail-closed offline gate for TASK 028 official-equivalence probe design."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.official_equivalence import (
    build_probe_plan,
    classify_official_observations,
    evaluate_candidate_proof,
    load_official_equivalence_contract,
)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    contract = load_official_equivalence_contract(
        ROOT / "config/loa_official_equivalence_probe.v1.json"
    )
    fixture = load("tests/fixtures/task_028_loa_official_equivalence_probe.json")
    evidence = load("docs/evidence/TASK_028_LOA_OFFICIAL_EQUIVALENCE_PROBE_DESIGN_0.8.0.json")
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")

    plan = build_probe_plan(contract)
    pdf_only = classify_official_observations(contract, fixture["pdf_only_observations"])
    machine = classify_official_observations(contract, fixture["machine_candidate_observations"])
    proof = evaluate_candidate_proof(
        contract,
        machine["machine_candidates"][0],
        fixture["proofs_complete_synthetic"],
    )
    effects = evidence.get("effects", {})
    auth = evidence.get("authorization", {})
    guards = evidence.get("classification_guards", {})

    checks = {
        "base_and_mode": evidence.get("base_sha") == "b645f1cf69fbf1cead7a7d285e772c06169fd60c" and evidence.get("mode") == contract.get("mode") == "T0_OFFLINE_IMPLEMENTATION_BOUNDARY",
        "source_task": evidence.get("source_task") == contract.get("source_task") == "TASK_027_LOA_REPRODUCIBLE_EXTRACTION_READINESS",
        "bounded_plan": plan.get("status") == "PLANNED_NOT_AUTHORIZED" and len(plan.get("requests", [])) == 3 and plan.get("max_requests") == 6 and plan.get("downloads") == 0,
        "no_absence_inference": pdf_only.get("absence_proven") is False and guards.get("no_candidate_observed_proves_nonexistence") is False,
        "machine_is_candidate_only": machine.get("status") == "MACHINE_READABLE_CANDIDATE_DETECTED_REVIEW_REQUIRED" and machine.get("equivalence_proven") is False and guards.get("machine_readable_candidate_is_equivalence") is False,
        "followup_blocked": machine.get("followup_authorized") is False and guards.get("candidate_followup_requires_separate_authorization") is True,
        "complete_proof_still_separate": proof.get("status") == "CANDIDATE_PROOF_COMPLETE_REQUIRES_SEPARATE_AUTHORIZATION" and proof.get("promotion_authorized") is False,
        "zero_effects": effects and all(value in (0, False) for value in effects.values()),
        "authorization_boundary": auth.get("offline_design") is True and all(auth.get(key) is False for key in ("live_probe", "candidate_followup", "download", "ocr", "drive", "silver", "gold", "serving", "publication")),
        "release_unchanged": evidence.get("release_boundary", {}).get("0.7.0") == "ACTIVE" and evidence.get("release_boundary", {}).get("0.8.0") == "CANDIDATE" and evidence.get("release_boundary", {}).get("unchanged") is True,
        "ci_gate_present": "python scripts/github_task_028_loa_official_equivalence_probe_design_gate.py" in ci,
    }

    failed = [name for name, ok in checks.items() if not ok]
    status = "PASS_TASK_028_LOA_OFFICIAL_EQUIVALENCE_PROBE_DESIGN_OFFLINE" if not failed else "STOP"
    print(json.dumps({"status": status, "checks": checks, "failed_checks": failed}, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
