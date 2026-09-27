from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_signal_diagnostics_review import load_json as load_review_json, run_review
from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_locality_diagnostics_design import load_json, run_design

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_locality_diagnostics_design.json"

def _review() -> dict:
    design_config = load_json(CONFIG)
    review_config_path = ROOT / design_config["hash_routing_review_config_path"]
    review_config = load_review_json(review_config_path)
    evidence_path = ROOT / review_config["evidence_path"]
    return run_review(review_config, load_review_json(evidence_path), evidence_path=evidence_path)

def main() -> int:
    result = run_design(load_json(CONFIG), _review())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
