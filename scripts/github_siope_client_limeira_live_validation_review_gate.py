from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_live_validation_review import (  # noqa: E402
    SiopeClientLimeiraLiveValidationReviewError,
    load_json,
    run_review,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_live_validation_review.json"


def main() -> int:
    try:
        config = load_json(CONFIG)
        evidence_path = ROOT / config["pinned_evidence_path"]
        evidence = load_json(evidence_path)
        print(json.dumps(run_review(config, evidence, evidence_path=evidence_path), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, SiopeClientLimeiraLiveValidationReviewError) as exc:
        print(json.dumps({"status": str(exc)}, sort_keys=True))
        return 13


if __name__ == "__main__":
    raise SystemExit(main())
