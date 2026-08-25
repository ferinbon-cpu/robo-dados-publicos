from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_signature_diagnostics_review import load_json as load_review_json, run_review  # noqa: E402
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_structural_binding_diagnostics_design import load_json, run_design  # noqa: E402
from robo_dados_publicos.sources.siope_official_olinda_api_resource_contract_design import design_resource_contract  # noqa: E402

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_structural_binding_diagnostics_design.json"
SIGNATURE_REVIEW_CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_signature_diagnostics_review.json"
RESOURCE_CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_resource_contract_design.json"
SERVICE_REVIEW_CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_service_discovery_review.json"


def _signature_review() -> dict:
    config = load_review_json(SIGNATURE_REVIEW_CONFIG)
    evidence = load_review_json(ROOT / config["evidence_path"])
    return run_review(config, evidence)


def _resource_design() -> dict:
    config = load_json(RESOURCE_CONFIG)
    service_review_config = load_json(SERVICE_REVIEW_CONFIG)
    service_evidence = load_json(ROOT / service_review_config["evidence_path"])
    from robo_dados_publicos.sources.siope_official_olinda_api_service_discovery_review import run_review as run_service_review  # noqa: E402

    service_review = run_service_review(service_review_config, service_evidence)
    research = load_json(ROOT / config["public_research_evidence_path"])
    return design_resource_contract(config, service_review, research)


def run_gate() -> dict:
    config = load_json(CONFIG)
    return run_design(config, _signature_review(), _resource_design())


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
