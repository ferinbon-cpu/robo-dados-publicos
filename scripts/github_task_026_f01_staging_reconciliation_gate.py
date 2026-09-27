#!/usr/bin/env python3
"""Fail-closed offline gate for TASK 026 F01 staging reconciliation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.reconciliation import (
    load_reconciliation_contract,
    reconcile_f01_bundle,
)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    contract = load_reconciliation_contract(
        ROOT / "config/manual_supervised_ingest_f01_reconciliation.v1.json"
    )
    fixture = load("tests/fixtures/task_026_f01_staging_reconciliation.json")
    evidence = load("docs/evidence/TASK_026_F01_STAGING_RECONCILIATION_0.8.0.json")
    result = reconcile_f01_bundle(contract, fixture)
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    effects = evidence.get("effects", {})
    auth = evidence.get("authorization", {})
    semantic = evidence.get("semantic_guards", {})

    checks = {
        "base_and_mode": evidence.get("base_sha") == "b80230782d2743c5e04527421016c92013a7f803" and evidence.get("mode") == contract.get("mode") == "T0_OFFLINE_RECONCILIATION",
        "source_task_pinned": evidence.get("source_task") == contract.get("source_task") == "TASK_025_MANUAL_SUPERVISED_INGEST_F01",
        "reconciliation_pass": result.get("status") == "PASS_F01_STAGING_RECONCILED_OFFLINE",
        "not_silver": result.get("promotion") == "BLOCKED_NOT_SILVER" and contract.get("silver_promotion_authorized") is False,
        "loa_blocked": result.get("loa_full_parse") == "BLOCKED" and semantic.get("loa_full_parse") == "BLOCKED",
        "financial_identity_insufficient": result.get("financial_identity") == "EVIDENCIA_INSUFICIENTE" and semantic.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE",
        "derived_only_guard": semantic.get("loa_prior_bridge_is_derived_only") is True and semantic.get("program_bridge_is_financial_identity") is False,
        "zero_effects": effects and all(value in (0, False) for value in effects.values()),
        "bounded_authorization": auth.get("offline_reconciliation") is True and all(auth.get(key) is False for key in ("source_recollection", "ocr_execution", "silver_promotion", "gold_promotion", "serving_promotion", "publication")),
        "release_unchanged": evidence.get("release_boundary", {}).get("0.7.0") == "ACTIVE" and evidence.get("release_boundary", {}).get("0.8.0") == "CANDIDATE" and evidence.get("release_boundary", {}).get("unchanged") is True,
        "ci_gate_present": "python scripts/github_task_026_f01_staging_reconciliation_gate.py" in ci,
    }

    failed = [name for name, ok in checks.items() if not ok]
    status = "PASS_TASK_026_F01_STAGING_RECONCILIATION_OFFLINE" if not failed else "STOP"
    print(json.dumps({"status": status, "checks": checks, "failed_checks": failed}, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
