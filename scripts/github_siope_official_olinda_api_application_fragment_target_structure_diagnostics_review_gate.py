from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_target_structure_diagnostics_review import (
    load_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_fragment_target_structure_diagnostics_review.json"


def main() -> int:
    config = load_json(CONFIG)
    evidence_path = ROOT / config["evidence_path"]
    result = run_review(config, load_json(evidence_path), evidence_path=evidence_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
