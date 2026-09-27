from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_review import load_json as load_review_json, run_review
from robo_dados_publicos.sources.siope_official_olinda_api_application_loaded_script_signature_diagnostics_design import run_design


def main() -> int:
    design_config = json.loads((ROOT / "config/source_expansion.siope_official_olinda_api_application_loaded_script_signature_diagnostics_design.json").read_text(encoding="utf-8"))
    review_config = load_review_json(ROOT / design_config["navigation_distribution_review_config_path"])
    evidence = load_review_json(ROOT / review_config["evidence_path"])
    review = run_review(review_config, evidence)
    print(json.dumps(run_design(design_config, review), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
