from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_eiti_granular_execution_source_selection import validate_task051_evidence

E51 = ROOT / "docs/evidence/TASK_051_F01_EITI_GRANULAR_EXECUTION_SOURCE_SELECTION_0.8.0.json"
E49 = ROOT / "docs/evidence/TASK_049_F01_EITI_ACTION_LINKAGE_CLOSURE_REVIEW_0.8.0.json"
E50 = ROOT / "docs/evidence/TASK_050_F01_LOA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    result = validate_task051_evidence(load(E51), load(E49), load(E50))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
