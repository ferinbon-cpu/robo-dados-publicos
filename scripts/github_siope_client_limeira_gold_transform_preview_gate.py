from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_gold_transform_preview import (  # noqa: E402
    GoldTransformPreviewError,
    build_preview,
    load_json,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_gold_transform_preview.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_json(CONFIG)
        if args.dry_run:
            result = validate_config(config)
        else:
            _, result = build_preview(config, root=ROOT)
    except GoldTransformPreviewError as exc:
        print(json.dumps({
            "status": str(exc),
            "network_called": False,
            "drive_write_count": 0,
            "gold_payload_persisted": False,
            "gold_persistence_authorized": False,
            "gold_remote_write_authorized": False,
            "compliance_claims_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 31
    except Exception as exc:
        print(json.dumps({
            "status": "STOP_M7_SIOPE_CLIENT_LIMEIRA_GOLD_TRANSFORM_PREVIEW_UNEXPECTED",
            "error_type": type(exc).__name__,
            "network_called": False,
            "drive_write_count": 0,
            "gold_payload_persisted": False,
            "gold_persistence_authorized": False,
            "gold_remote_write_authorized": False,
            "compliance_claims_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 32
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
