from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_bronze_single_record_capture import (  # noqa: E402
    Historical2022P6BronzeCaptureError,
    capture,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_bronze_single_record_capture.json"
DEFAULT_OUTPUT = "siope-client-limeira-historical-2022-p6-bronze-single-record-capture-evidence"


def _write_result(out: Path, result: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _cleanup_partial_data(out: Path) -> None:
    (out / "record.json").unlink(missing_ok=True)
    (out / "manifest.json").unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    out = ROOT / args.output_dir
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        if args.dry_run:
            result = validate_config(config)
        else:
            result = capture(config, output_dir=out)
            _write_result(out, result)
    except (OSError, ValueError, KeyError, Historical2022P6BronzeCaptureError) as exc:
        _cleanup_partial_data(out)
        result = {
            "status": str(exc),
            "request_count": getattr(exc, "request_count", 0),
            "single_historical_record_capture_authorized": False,
            "historical_collection_authorized": False,
            "drive_persistence_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
            "bronze_record_persisted": False,
            "bronze_manifest_persisted": False,
        }
        if not args.dry_run:
            _write_result(out, result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 44
    except Exception as exc:
        _cleanup_partial_data(out)
        result = {
            "status": "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE_UNEXPECTED",
            "error_type": type(exc).__name__,
            "request_count": 0,
            "single_historical_record_capture_authorized": False,
            "historical_collection_authorized": False,
            "drive_persistence_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
            "bronze_record_persisted": False,
            "bronze_manifest_persisted": False,
        }
        if not args.dry_run:
            _write_result(out, result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 45
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
