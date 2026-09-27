from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_review import load_json as load_review_json, run_review
from robo_dados_publicos.sources.siope_official_olinda_api_application_location_hash_odata_side_diagnostics_design import load_json as load_design_json, run_design
from robo_dados_publicos.sources.siope_official_olinda_api_application_location_hash_odata_side_diagnostics import load_json, dry_run, run_location_hash_odata_side_diagnostics

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_location_hash_odata_side_diagnostics.json"


def _design() -> dict:
    live_config = load_json(CONFIG)
    design_config = load_design_json(ROOT / live_config["design_config_path"])
    review_config = load_review_json(ROOT / design_config["prerequisite_review_config_path"])
    evidence_path = ROOT / review_config["evidence_path"]
    review_result = run_review(review_config, load_review_json(evidence_path), evidence_path=evidence_path)
    return run_design(design_config, review_result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    config = load_json(CONFIG)
    result = dry_run(config, _design()) if args.dry_run else run_location_hash_odata_side_diagnostics(config, _design())
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
