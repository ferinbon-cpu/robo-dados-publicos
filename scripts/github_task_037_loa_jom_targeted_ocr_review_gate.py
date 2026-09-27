#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.loa_journal_targeted_ocr_review import validate_evidence

EVIDENCE = ROOT / "docs/evidence/TASK_037_LOA_JOM_TARGETED_OCR_REVIEW_0.8.0.json"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    result = validate_evidence(evidence)
    print(result["status"])
    print("TASK037_PAGES=" + ",".join(str(page) for page in result["pages"]))
    print(f"TASK037_OCR_TEXT_CHARS_TOTAL={result['ocr_text_chars_total']}")
    print("TASK037_NUMERIC_TABLE_REVIEW_PAGES=480,481")
    print(f"TASK037_F01_STATUS={result['f01_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
