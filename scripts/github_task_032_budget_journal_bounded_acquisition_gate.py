#!/usr/bin/env python3
"""Fail-closed offline review gate for TASK 032 acquisition implementation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.budget_journal_bounded_acquisition import (
    load_contract,
    validate_live_authorization,
)


def main() -> int:
    contract = load_contract(ROOT / "config/budget_laws_journal_bounded_acquisition.v1.json")
    evidence = json.loads((ROOT / "docs/evidence/TASK_032_BUDGET_JOURNAL_BOUNDED_ACQUISITION_0.8.0.json").read_text(encoding="utf-8"))
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    missing_auth = validate_live_authorization(None, expected_sha="0" * 40)
    limits = contract["limits"]
    prohibited = contract["prohibited"]
    checks = {
        "mode_offline_default": contract["mode"] == "T0_OFFLINE_IMPLEMENTATION_LIVE_DISABLED_BY_DEFAULT",
        "exact_editions": [x["edition"] for x in contract["documents"]] == [7024, 7119, 7127],
        "exact_page_counts": [x["expected_pages"] for x in contract["documents"]] == [79, 107, 631],
        "exact_limits": (limits["source_gets"], limits["drive_inventory_requests"], limits["drive_creates"], limits["drive_readbacks"]) == (3, 1, 3, 3),
        "no_retry_or_pagination": limits["automatic_retry"] is False and limits["pagination_expansion"] is False and limits["alternate_url_discovery"] is False,
        "all_sources_before_write": contract["prewrite"]["all_three_sources_must_validate_before_inventory"] is True,
        "all_names_absent_before_write": contract["prewrite"]["all_three_target_names_must_be_absent_before_first_write"] is True,
        "readback_required": all(contract["readback"].values()),
        "all_downstream_prohibited": all(prohibited.values()),
        "live_auth_absent_is_stop": missing_auth["status"] == "STOP_TASK_032_LIVE_NOT_AUTHORIZED",
        "evidence_no_live": evidence["live_execution_performed"] is False and evidence["drive_mutation_performed"] is False and evidence["source_hashes_known"] is False,
        "ci_gate_present": "python scripts/github_task_032_budget_journal_bounded_acquisition_gate.py" in ci,
    }
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"status": "PASS_TASK_032_BOUNDED_ACQUISITION_IMPLEMENTATION_OFFLINE" if not failed else "STOP", "checks": checks, "failed_checks": failed}, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
