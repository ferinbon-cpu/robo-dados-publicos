from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_gold_drive_readback_verification import (  # noqa: E402
    HistoricalGoldDriveReadbackVerificationError,
    load_json,
    validate_config,
    verify_readback,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_gold_drive_readback_verification.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = load_json(CONFIG)
    if args.dry_run:
        try:
            result = validate_config(config, root=ROOT)
        except HistoricalGoldDriveReadbackVerificationError as exc:
            print(json.dumps({
                "status": str(exc),
                "network_called": False,
                "source_network_called": False,
                "drive_network_called": False,
                "drive_write_count": 0,
                "historical_collection_authorized": False,
                "remote_file_id_persisted": False,
                "compliance_claims_authorized": False,
                "processing_authorized": False,
                "recurrence_authorized": False,
                "schedule_enabled": False,
            }, ensure_ascii=False, sort_keys=True))
            return 33
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    try:
        result = verify_readback(config, root=ROOT)
    except HistoricalGoldDriveReadbackVerificationError as exc:
        print(json.dumps({
            "status": str(exc),
            "network_called": True,
            "source_network_called": False,
            "drive_write_count": 0,
            "historical_collection_authorized": False,
            "remote_file_id_persisted": False,
            "compliance_claims_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 34
    except Exception as exc:
        print(json.dumps({
            "status": "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_VERIFICATION_UNEXPECTED",
            "error_type": type(exc).__name__,
            "network_called": True,
            "source_network_called": False,
            "drive_write_count": 0,
            "historical_collection_authorized": False,
            "remote_file_id_persisted": False,
            "compliance_claims_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 35
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
