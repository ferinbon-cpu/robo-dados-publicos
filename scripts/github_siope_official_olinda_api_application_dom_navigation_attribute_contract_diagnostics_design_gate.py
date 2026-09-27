from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_design import load_json, run_design  # noqa: E402
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_structural_binding_diagnostics_review import run_review  # noqa: E402

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_design.json"
REVIEW_CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_structural_binding_diagnostics_review.json"


def _review() -> dict:
    config = load_json(REVIEW_CONFIG)
    evidence = load_json(ROOT / config["evidence_path"])
    return run_review(config, evidence)


def run_gate() -> dict:
    config = load_json(CONFIG)
    return run_design(config, _review())


def main() -> int:
    print(json.dumps(run_gate(), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
