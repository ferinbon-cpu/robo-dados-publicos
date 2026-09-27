#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.product.siope_historical_publication_review import (
    SiopeHistoricalPublicationReviewError,
    review_publication,
)


def main() -> int:
    try:
        result = review_publication(root=ROOT)
    except SiopeHistoricalPublicationReviewError as exc:
        print(
            json.dumps(
                {
                    "status": str(exc),
                    "network_called": False,
                    "drive_reads": 0,
                    "drive_writes": 0,
                    "publication_performed": False,
                    "publication_authorized": False,
                    "secret_values_exposed": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 17

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
