from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_design import load_json, run_design  # noqa: E402
from scripts.github_siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_review_gate import run_gate as run_prior_review  # noqa: E402

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_design.json"


def run_gate() -> dict:
    return run_design(load_json(CONFIG), run_prior_review())


def main() -> int:
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
