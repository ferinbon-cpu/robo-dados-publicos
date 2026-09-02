#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.loa_journal_numeric_table_validation import validate_evidence

EVIDENCE = ROOT / "docs/evidence/TASK_038_LOA_JOM_NUMERIC_TABLE_VISUAL_VALIDATION_0.8.0.json"

def main() -> int:
    result = validate_evidence(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    print(result["status"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
