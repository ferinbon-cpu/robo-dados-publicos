from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_bronze_drive_persistence_review import (  # noqa: E402
    DrivePersistenceReviewError,
    load_json,
    review,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_bronze_drive_persistence_review.json"


def main() -> int:
    try:
        result = review(load_json(CONFIG), root=ROOT)
    except DrivePersistenceReviewError as exc:
        print(json.dumps({
            "status": str(exc),
            "network_called": False,
            "drive_readback_design_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 19
    except Exception as exc:
        print(json.dumps({
            "status": "STOP_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_REVIEW_UNEXPECTED",
            "error_type": type(exc).__name__,
            "network_called": False,
            "drive_readback_design_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, ensure_ascii=False, sort_keys=True))
        return 20
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
