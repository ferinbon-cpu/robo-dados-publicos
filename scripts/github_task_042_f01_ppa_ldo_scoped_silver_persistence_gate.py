#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_ppa_ldo_scoped_silver_persistence_review import validate_task042_evidence

E42 = ROOT / "docs/evidence/TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"
E41 = ROOT / "docs/evidence/TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW_0.8.0.json"


def main() -> int:
    try:
        evidence = json.loads(E42.read_text(encoding="utf-8"))
        task041 = json.loads(E41.read_text(encoding="utf-8"))
        result = validate_task042_evidence(evidence, task041)
    except Exception as exc:
        print(f"TASK_042_GATE_STOP: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("TASK_042_GATE_PASS: PPA/LDO scoped Silver create-only persistence and readback pinned; Gold/serving/publication remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
