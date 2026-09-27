#!/usr/bin/env python3
"""Fail-closed review gate for TASK 029 bounded live LOA probe evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.live_probe_review import review_live_probe


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    contract = load("config/loa_official_equivalence_live_probe_review.v1.json")
    evidence = load("docs/evidence/TASK_029_LOA_OFFICIAL_EQUIVALENCE_LIVE_PROBE_0.8.0.json")
    result = review_live_probe(contract, evidence)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
