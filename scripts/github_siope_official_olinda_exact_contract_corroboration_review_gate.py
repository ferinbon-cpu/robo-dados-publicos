from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.sources.siope_official_olinda_exact_contract_corroboration_review import (
    load_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/source_expansion.siope_official_olinda_exact_contract_corroboration_review.json"


def main() -> int:
    config = load_json(CONFIG)
    evidence_path = ROOT / config["pinned_evidence_path"]
    corroboration_path = ROOT / config["pinned_corroboration_path"]
    result = run_review(
        config,
        load_json(evidence_path),
        evidence_path=evidence_path.relative_to(ROOT),
        corroboration_path=corroboration_path.relative_to(ROOT),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
