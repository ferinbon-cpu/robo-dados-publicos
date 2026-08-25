from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_runtime_route_diagnostics_design import (  # noqa: E402
    design_application_route_diagnostics,
    load_json,
)

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_runtime_route_diagnostics_design.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    resource_design = load_json(ROOT / config["resource_contract_design_path"])
    return design_application_route_diagnostics(config, resource_design)


def main() -> int:
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
