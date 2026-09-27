from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_full_schema_readonly_validation_review import (  # noqa: E402
    load_json,
    run_review,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_full_schema_readonly_validation_review.json"
EVIDENCE = ROOT / "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_RUN_1_0.8.0.json"


def main() -> int:
    result = run_review(load_json(CONFIG), load_json(EVIDENCE), evidence_path=EVIDENCE)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
