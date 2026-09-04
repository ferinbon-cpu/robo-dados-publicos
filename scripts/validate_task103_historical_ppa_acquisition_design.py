#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.research.eiti_historical_ppa_acquisition import (
    HistoricalPpaAcquisitionDesignStop,
    load_and_validate_acquisition_design,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/eiti_historical_ppa_primary_acquisition.v1.json"


def main() -> int:
    try:
        result = load_and_validate_acquisition_design(CONTRACT)
    except (OSError, ValueError, HistoricalPpaAcquisitionDesignStop) as exc:
        print(
            json.dumps(
                {
                    "status": "STOP_TASK103_HISTORICAL_PPA_ACQUISITION_DESIGN_OFFLINE",
                    "error": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 103

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
