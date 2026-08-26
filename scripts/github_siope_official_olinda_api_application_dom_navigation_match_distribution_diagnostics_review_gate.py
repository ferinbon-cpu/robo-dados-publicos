from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_review import load_json, run_review


def main() -> int:
    config_path = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_review.json"
    config = load_json(config_path)
    evidence = load_json(ROOT / config["evidence_path"])
    print(json.dumps(run_review(config, evidence), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
