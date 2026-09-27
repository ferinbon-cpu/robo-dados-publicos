from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_full_schema_readonly_validation import (  # noqa: E402
    SiopeClientLimeiraHistorical2023P6FullSchemaReadonlyValidationError,
    run_validation,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_full_schema_readonly_validation.json"


def _load_config() -> dict:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("CONFIG_OBJECT_REQUIRED")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        config = _load_config()
        result = validate_config(config) if args.dry_run else run_validation(config)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        SiopeClientLimeiraHistorical2023P6FullSchemaReadonlyValidationError,
    ) as exc:
        result = {
            "status": str(exc),
            "historical_collection_authorized": False,
            "collection_authorized": False,
            "persistence_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
            "response_body_persisted": False,
            "record_values_persisted": False,
        }
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 37


if __name__ == "__main__":
    raise SystemExit(main())
