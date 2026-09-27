from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_locality_diagnostics_review as review
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics_design as gate

REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_locality_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics_design.json"


def main() -> int:
    review_config = review.load_json(REVIEW_CONFIG)
    evidence_path = ROOT / review_config["evidence_path"]
    review_result = review.run_review(review_config, review.load_json(evidence_path), evidence_path=evidence_path)
    result = gate.run_design(gate.load_json(DESIGN_CONFIG), review_result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
