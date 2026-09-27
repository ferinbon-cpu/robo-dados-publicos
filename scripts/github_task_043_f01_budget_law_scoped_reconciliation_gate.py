#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_budget_law_scoped_reconciliation import validate_task043_evidence

E43 = ROOT / "docs/evidence/TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION_0.8.0.json"
E39 = ROOT / "docs/evidence/TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW_0.8.0.json"
E41 = ROOT / "docs/evidence/TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW_0.8.0.json"
E42 = ROOT / "docs/evidence/TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    try:
        result = validate_task043_evidence(_load(E43), _load(E39), _load(E41), _load(E42))
    except Exception as exc:
        print(f"TASK_043_GATE_STOP: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("TASK_043_GATE_PASS: scoped PPA-LDO-LOA reconciliation reviewed; 2720 continuity is not financial identity; 2690 remains review-blocked; EITI remains insufficient")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
