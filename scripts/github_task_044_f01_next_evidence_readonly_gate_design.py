#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_next_evidence_readonly_gate_design import validate_task044_design

E44 = ROOT / "docs/evidence/TASK_044_F01_NEXT_EVIDENCE_READONLY_GATE_DESIGN_0.8.0.json"
E43 = ROOT / "docs/evidence/TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION_0.8.0.json"


def main() -> int:
    try:
        e44 = json.loads(E44.read_text(encoding="utf-8"))
        e43 = json.loads(E43.read_text(encoding="utf-8"))
        result = validate_task044_design(e44, e43)
    except Exception as exc:
        print(f"TASK_044_GATE_STOP: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("TASK_044_GATE_PASS: next evidence gate designed only; future bounded existing-custody read still requires fresh owner authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
