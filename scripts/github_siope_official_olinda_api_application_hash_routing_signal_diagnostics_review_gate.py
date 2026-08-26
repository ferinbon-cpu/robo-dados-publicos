from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_signal_diagnostics_review import load_json, run_review

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_signal_diagnostics_review.json"

def main() -> int:
    config = load_json(CONFIG)
    evidence_path = ROOT / config["evidence_path"]
    result = run_review(config, load_json(evidence_path), evidence_path=evidence_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
