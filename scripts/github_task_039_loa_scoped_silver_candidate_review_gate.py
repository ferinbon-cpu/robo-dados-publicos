#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.loa_scoped_silver_candidate_review import validate_candidate

E39 = ROOT / "docs/evidence/TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW_0.8.0.json"
E36 = ROOT / "docs/evidence/TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST_0.8.0.json"
E37 = ROOT / "docs/evidence/TASK_037_LOA_JOM_TARGETED_OCR_REVIEW_0.8.0.json"
E38 = ROOT / "docs/evidence/TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION_0.8.0.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    result = validate_candidate(load(E39), load(E36), load(E37), load(E38))
    print(result["status"])
    print(f"TASK039_CANDIDATE_SHA256={result['candidate_payload_sha256']}")
    print(f"TASK039_READINESS={result['readiness']}")
    print(f"TASK039_F01_STATUS={result['f01_status']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
