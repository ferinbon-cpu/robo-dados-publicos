from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_review import load_json, run_review
from robo_dados_publicos.sources.siope_official_olinda_api_application_location_hash_odata_side_diagnostics_design import run_design

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_location_hash_odata_side_diagnostics_design.json"
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_review.json"

def main() -> int:
    review_config = load_json(REVIEW_CONFIG)
    evidence_path = ROOT / review_config["evidence_path"]
    review = run_review(review_config, load_json(evidence_path), evidence_path=evidence_path)
    result = run_design(load_json(CONFIG), review)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
