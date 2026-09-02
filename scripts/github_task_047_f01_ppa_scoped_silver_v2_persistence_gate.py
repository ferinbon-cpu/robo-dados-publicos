from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f01_ppa_scoped_silver_v2_persistence_review import validate_task047_evidence

E47 = ROOT / "docs/evidence/TASK_047_F01_PPA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_0.8.0.json"
E46 = ROOT / "docs/evidence/TASK_046_F01_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"


def main() -> int:
    e47 = json.loads(E47.read_text(encoding="utf-8"))
    e46 = json.loads(E46.read_text(encoding="utf-8"))
    result = validate_task047_evidence(e47, e46)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
