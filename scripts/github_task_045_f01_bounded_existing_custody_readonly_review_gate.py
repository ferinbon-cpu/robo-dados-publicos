#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_bounded_existing_custody_readonly_review import (
    validate_task045_evidence,
)

E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E44 = ROOT / "docs/evidence/TASK_044_F01_NEXT_EVIDENCE_READONLY_GATE_DESIGN_0.8.0.json"
E43 = ROOT / "docs/evidence/TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION_0.8.0.json"


def main() -> int:
    e45 = json.loads(E45.read_text(encoding="utf-8"))
    e44 = json.loads(E44.read_text(encoding="utf-8"))
    e43 = json.loads(E43.read_text(encoding="utf-8"))
    result = validate_task045_evidence(e45, e44, e43)
    print(f"TASK045_STATUS={result['status']}")
    print(f"TASK045_PPA2690_RESOLVED={str(result['ppa_2690_resolved']).lower()}")
    print(f"TASK045_PPA2690_2026_BRL={result['ppa_2690_2026_brl']}")
    print(f"TASK045_LOA2690_2026_BRL={result['loa_2690_2026_brl']}")
    print(f"TASK045_LOA2720_2026_BRL={result['loa_2720_2026_brl']}")
    print(f"TASK045_EITI_FINANCIAL_IDENTITY={result['eiti_financial_identity']}")
    print(f"TASK045_NEW_REMOTE_WRITE={str(result['new_remote_write']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
