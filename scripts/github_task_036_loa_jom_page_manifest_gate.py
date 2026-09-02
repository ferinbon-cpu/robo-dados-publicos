#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.loa_journal_page_manifest import (
    EXPECTED_ACTION_INDEX_SHA256,
    action_code_index_sha256,
    validate_evidence,
)


EVIDENCE = ROOT / "docs/evidence/TASK_036_LOA_JOM_PAGE_INDEXED_CANDIDATE_MANIFEST_0.8.0.json"
ACTION_INDEX = ROOT / "docs/evidence/TASK_036_LOA_JOM_ACTION_CODE_INDEX_0.8.0.json"


def main() -> int:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    action_index = json.loads(ACTION_INDEX.read_text(encoding="utf-8"))
    actual_hash = action_code_index_sha256(action_index)
    print(f"TASK036_ACTION_INDEX_SHA256_ACTUAL={actual_hash}")
    print(f"TASK036_ACTION_INDEX_SHA256_EXPECTED={EXPECTED_ACTION_INDEX_SHA256}")
    result = validate_evidence(evidence, action_index)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
