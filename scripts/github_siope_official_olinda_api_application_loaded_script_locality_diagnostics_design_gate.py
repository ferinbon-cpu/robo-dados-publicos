from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_global_relation_diagnostics_review import load_json as load_review_json, run_review
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_locality_diagnostics_design import load_json, run_design

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_locality_diagnostics_design.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    review_config = load_review_json(ROOT / config["global_relation_review_config_path"])
    evidence_path = ROOT / review_config["evidence_path"]
    evidence = load_review_json(evidence_path)
    review = run_review(review_config, evidence, evidence_path=evidence_path)
    return run_design(config, review)


if __name__ == "__main__":
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
