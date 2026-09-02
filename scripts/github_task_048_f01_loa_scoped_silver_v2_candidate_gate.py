#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_loa_scoped_silver_v2_candidate_review import validate_task048_evidence

E48 = ROOT / "docs/evidence/TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"
E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E40 = ROOT / "docs/evidence/TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


def main() -> int:
    result = validate_task048_evidence(
        json.loads(E48.read_text(encoding="utf-8")),
        json.loads(E45.read_text(encoding="utf-8")),
        json.loads(E40.read_text(encoding="utf-8")),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
