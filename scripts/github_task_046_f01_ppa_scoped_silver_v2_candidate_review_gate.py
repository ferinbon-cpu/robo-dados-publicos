#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_ppa_scoped_silver_v2_candidate_review import validate_task046_evidence

E46 = ROOT / "docs/evidence/TASK_046_F01_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"
E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E42 = ROOT / "docs/evidence/TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


def main() -> int:
    result = validate_task046_evidence(
        json.loads(E46.read_text(encoding="utf-8")),
        json.loads(E45.read_text(encoding="utf-8")),
        json.loads(E42.read_text(encoding="utf-8")),
    )
    print(f"TASK046_STATUS={result['status']}")
    print(f"TASK046_CANDIDATE_SHA256={result['candidate_sha256']}")
    print(f"TASK046_TARGET_NAME={result['target_name']}")
    print(f"TASK046_REMOTE_WRITE_AUTHORIZED={str(result['remote_write_authorized']).lower()}")
    print(f"TASK046_EITI_FINANCIAL_IDENTITY={result['eiti_financial_identity']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
