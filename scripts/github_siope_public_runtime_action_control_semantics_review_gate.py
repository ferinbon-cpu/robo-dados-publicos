from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_public_runtime_action_control_semantics_review import (  # noqa: E402
    load_json,
    review_action_control_semantics,
)

CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_action_control_semantics_review.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    evidence = load_json(ROOT / config["evidence_path"])
    return review_action_control_semantics(config, evidence)


def main() -> int:
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
