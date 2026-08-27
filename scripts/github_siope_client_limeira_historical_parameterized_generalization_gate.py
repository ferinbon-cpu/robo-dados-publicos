from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_parameterized_generalization import (
    HistoricalParameterizedGeneralizationError,
    load_json,
    review,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_parameterized_generalization.json"
OUTPUT_DIR = ROOT / "siope-client-limeira-historical-parameterized-generalization-evidence"
OUTPUT = OUTPUT_DIR / "result.json"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = review(load_json(CONFIG), root=ROOT)
    except (HistoricalParameterizedGeneralizationError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "status": "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_PARAMETERIZED_GENERALIZATION",
            "error": str(exc),
            "network_called": False,
            "drive_called": False,
        }
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 13
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
