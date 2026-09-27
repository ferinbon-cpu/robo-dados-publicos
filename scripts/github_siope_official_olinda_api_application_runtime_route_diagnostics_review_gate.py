from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_runtime_route_diagnostics_review import (  # noqa: E402
    load_json,
    review,
)

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_runtime_route_diagnostics_review.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    evidence = load_json(ROOT / config["evidence_path"])
    return review(config, evidence)


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
