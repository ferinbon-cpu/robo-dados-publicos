from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_single_year_pilot import (  # noqa: E402
    HistoricalParameterizedSingleYearPilotError,
    run_pilot,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_parameterized_single_year_pilot.json"
OUT = ROOT / "siope-client-limeira-historical-parameterized-single-year-pilot-evidence/result.json"
STOP = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_SINGLE_YEAR_PILOT"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        result = run_pilot(config, root=ROOT)
    except (HistoricalParameterizedSingleYearPilotError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        result = {
            "status": STOP,
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "batch_live_authorized": False,
            "retry_authorized": False,
            "pagination_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }
        OUT.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return 13
    OUT.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
