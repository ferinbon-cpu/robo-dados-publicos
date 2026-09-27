from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_silver_drive_persistence import (  # noqa: E402
    HistoricalSilverDrivePersistenceError,
    load_json,
    persist,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_silver_drive_persistence.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = load_json(CONFIG)
    if args.dry_run:
        result = validate_config(config, root=ROOT)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    try:
        result = persist(config, root=ROOT)
    except HistoricalSilverDrivePersistenceError as exc:
        print(json.dumps({
            "status": str(exc),
            "network_called": True,
            "source_network_called": False,
            "drive_write_count": 0,
            "silver_payload_persisted": False,
            "historical_collection_authorized": False,
            "gold_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 23
    except Exception as exc:
        print(json.dumps({
            "status": "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_PERSISTENCE_UNEXPECTED",
            "error_type": type(exc).__name__,
            "network_called": True,
            "source_network_called": False,
            "drive_write_count": 0,
            "silver_payload_persisted": False,
            "historical_collection_authorized": False,
            "gold_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 24
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
