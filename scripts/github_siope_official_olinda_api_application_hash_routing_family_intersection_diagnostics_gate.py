from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_locality_diagnostics_review as review
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics_design as design
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics as live

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics.json"


def _design() -> dict:
    live_config = live.load_json(CONFIG)
    design_config = design.load_json(ROOT / live_config["design_config_path"])
    review_config = review.load_json(ROOT / design_config["locality_review_config_path"])
    evidence_path = ROOT / review_config["evidence_path"]
    review_result = review.run_review(review_config, review.load_json(evidence_path), evidence_path=evidence_path)
    return design.run_design(design_config, review_result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    config = live.load_json(CONFIG)
    result = (
        live.dry_run(config, _design())
        if args.dry_run
        else live.run_hash_routing_family_intersection_diagnostics(config, _design())
    )
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
