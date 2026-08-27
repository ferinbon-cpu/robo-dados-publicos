from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_gold_drive_readback_review import (  # noqa: E402
    HistoricalGoldDriveReadbackReviewError,
    review,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_gold_drive_readback_review.json"


def main() -> int:
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        result = review(config, root=ROOT)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, HistoricalGoldDriveReadbackReviewError) as exc:
        print(json.dumps({
            "status": str(exc),
            "network_called": False,
            "historical_collection_authorized": False,
            "processing_authorized": False,
            "compliance_claims_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, sort_keys=True))
        return 38


if __name__ == "__main__":
    raise SystemExit(main())
