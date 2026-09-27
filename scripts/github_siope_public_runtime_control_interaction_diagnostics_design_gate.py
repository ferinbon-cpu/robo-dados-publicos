from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_public_runtime_control_interaction_diagnostics_design import (  # noqa: E402
    load_json,
    validate_design,
)

DESIGN = ROOT / "config" / "source_expansion.siope_public_runtime_control_interaction_diagnostics_design.json"
CONTRACT_REVIEW = ROOT / "config" / "source_expansion.siope_public_runtime_route_contract_review.json"


def run_gate() -> dict:
    return validate_design(load_json(DESIGN), load_json(CONTRACT_REVIEW))


def main() -> int:
    print(json.dumps(run_gate(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
