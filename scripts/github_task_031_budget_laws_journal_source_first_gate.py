#!/usr/bin/env python3
"""Offline regression gate for TASK 031 Jornal source-first policy."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.budget_journal_source_first import load_budget_journal_source_first


def main() -> int:
    contract = load_budget_journal_source_first(ROOT / "config/budget_laws_journal_source_first.v1.json")
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    checks = {
        "primary_source_jom": contract["decision"]["primary_source"] == "JORNAL_OFICIAL_LIMEIRA_FULL_EDITION_PDF",
        "equivalence_not_blocker": contract["decision"]["full_equivalence_required_before_extraction"] is False,
        "custody_before_extraction": contract["decision"]["journal_full_edition_must_enter_custody_before_extraction"] is True,
        "three_editions": [x["edition"] for x in contract["journal_editions"]] == [7024, 7119, 7127],
        "custody_pending": all(x["custody_status"] == "PENDING_SOURCE_DOWNLOAD" and x["sha256"] is None for x in contract["journal_editions"]),
        "no_promotions": all(value is False for value in contract["promotion"].values()),
        "ci_gate_present": "python scripts/github_task_031_budget_laws_journal_source_first_gate.py" in ci,
    }
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"status": "PASS_TASK_031_SOURCE_FIRST_REGRESSION" if not failed else "STOP", "checks": checks, "failed_checks": failed}, ensure_ascii=False, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
