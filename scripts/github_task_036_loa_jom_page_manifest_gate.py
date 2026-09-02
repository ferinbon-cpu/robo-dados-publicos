#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_journal_page_manifest import validate_evidence


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST_0.8.0.json"
ACTION_INDEX = ROOT / "docs/evidence/TASK_036_LOA_JOM_ACTION_CODE_INDEX_0.8.0.json"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    action_index = json.loads(ACTION_INDEX.read_text(encoding="utf-8"))
    result = validate_evidence(evidence, action_index)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
