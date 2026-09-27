from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_silver_single_record_transform_review import (  # noqa: E402
    HistoricalSilverTransformReviewError,
    load_json,
    review,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_silver_single_record_transform_review.json"


def main() -> int:
    try:
        result = review(load_json(CONFIG), root=ROOT)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, HistoricalSilverTransformReviewError) as exc:
        print(json.dumps({"status": str(exc), "network_called": False}, ensure_ascii=False, sort_keys=True))
        return 22


if __name__ == "__main__":
    raise SystemExit(main())
