from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_locality_diagnostics_review import load_json, run_review

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_locality_diagnostics_review.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    evidence_path = ROOT / config["evidence_path"]
    evidence = load_json(evidence_path)
    return run_review(config, evidence, evidence_path=evidence_path)


if __name__ == "__main__":
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
