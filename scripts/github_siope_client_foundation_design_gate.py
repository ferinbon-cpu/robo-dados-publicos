from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_foundation_design import (  # noqa: E402
    SiopeClientFoundationDesignError,
    run_design,
)

CONFIG = ROOT / "config/source_expansion.siope_client_foundation_design.json"


def main() -> int:
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise SiopeClientFoundationDesignError("STOP_M7_SIOPE_CLIENT_FOUNDATION_DESIGN_CONFIG_OBJECT_REQUIRED")
        print(json.dumps(run_design(config), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, SiopeClientFoundationDesignError) as exc:
        print(json.dumps({"status": str(exc)}, sort_keys=True))
        return 13


if __name__ == "__main__":
    raise SystemExit(main())
