from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_target_structure_diagnostics_review import (
    load_json as load_review_json,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_signal_diagnostics_design import (
    load_json,
    run_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_signal_diagnostics_design.json"


def main() -> int:
    config = load_json(CONFIG)
    review_config_path = ROOT / config["prerequisite_review_config_path"]
    review_config = load_review_json(review_config_path)
    evidence_path = ROOT / review_config["evidence_path"]
    review_result = run_review(review_config, load_review_json(evidence_path), evidence_path=evidence_path)
    print(json.dumps(run_design(config, review_result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
