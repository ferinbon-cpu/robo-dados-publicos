from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_public_runtime_action_control_semantics_diagnostics_design import (  # noqa: E402
    load_json,
    validate_design,
)

CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_action_control_semantics_diagnostics_design.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    review = load_json(ROOT / config["prerequisite_review_config_path"])
    public = load_json(ROOT / config["public_runtime_config_path"])
    return validate_design(config, review, public)


def main() -> int:
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
