#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_eiti_action_linkage_closure_review import validate_task049_evidence

E49 = ROOT / "docs/evidence/TASK_049_F01_EITI_ACTION_LINKAGE_CLOSURE_REVIEW_0.8.0.json"
E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E48 = ROOT / "docs/evidence/TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"


def main() -> int:
    result = validate_task049_evidence(
        json.loads(E49.read_text(encoding="utf-8")),
        json.loads(E45.read_text(encoding="utf-8")),
        json.loads(E48.read_text(encoding="utf-8")),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
