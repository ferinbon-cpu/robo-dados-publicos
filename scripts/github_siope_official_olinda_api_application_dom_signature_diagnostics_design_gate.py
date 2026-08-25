from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_signature_diagnostics_design import load_json, run_design  # noqa: E402
from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_tolerant_route_diagnostics_review import run_review  # noqa: E402
from robo_dados_publicos.sources.siope_official_olinda_api_resource_contract_design import run_design as run_resource_design  # noqa: E402

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_signature_diagnostics_design.json"


def run_gate() -> dict:
    config = load_json(CONFIG)
    fragment_review_config = load_json(ROOT / config["fragment_route_review_config_path"])
    fragment_evidence = load_json(ROOT / fragment_review_config["evidence_path"])
    fragment_review = run_review(fragment_review_config, fragment_evidence)

    resource_config = load_json(ROOT / config["resource_contract_design_config_path"])
    service_review_config = load_json(ROOT / resource_config["service_review_config_path"])
    service_evidence = load_json(ROOT / service_review_config["evidence_path"])
    from robo_dados_publicos.sources.siope_official_olinda_api_service_discovery_review import run_review as run_service_review
    service_review = run_service_review(service_review_config, service_evidence)
    research = load_json(ROOT / resource_config["research_path"])
    resource_design = run_resource_design(resource_config, service_review, research)
    return run_design(config, fragment_review, resource_design)


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
