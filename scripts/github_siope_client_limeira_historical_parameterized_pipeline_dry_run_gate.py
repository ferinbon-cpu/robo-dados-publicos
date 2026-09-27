from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_pipeline_dry_run import (  # noqa: E402
    HistoricalParameterizedPipelineDryRunError,
    load_json,
    review,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_parameterized_pipeline_dry_run.json"
OUT_DIR = ROOT / "siope-client-limeira-historical-parameterized-pipeline-dry-run-evidence"
OUT = OUT_DIR / "result.json"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = review(load_json(CONFIG), root=ROOT)
        code = 0
    except (HistoricalParameterizedPipelineDryRunError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "status": str(exc),
            "network_called": False,
            "drive_called": False,
            "mutation_count": 0,
            "source_get_authorized": False,
            "drive_write_authorized": False,
        }
        code = 13
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
