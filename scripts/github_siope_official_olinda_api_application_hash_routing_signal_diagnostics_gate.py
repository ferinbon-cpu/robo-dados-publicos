from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_target_structure_diagnostics_review import (
    load_json as load_review_json,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_signal_diagnostics_design import (
    load_json as load_design_json,
    run_design,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_signal_diagnostics import (
    SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError,
    dry_run,
    load_json,
    run_hash_routing_signal_diagnostics,
)

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_signal_diagnostics.json"


def _prerequisites(config: dict) -> tuple[dict, dict]:
    design_config = load_design_json(ROOT / config["design_config_path"])
    review_config = load_review_json(ROOT / design_config["prerequisite_review_config_path"])
    evidence_path = ROOT / review_config["evidence_path"]
    review = run_review(review_config, load_review_json(evidence_path), evidence_path=evidence_path)
    return design_config, run_design(design_config, review)


def _write(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    print(text)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    config = load_json(CONFIG)
    try:
        _, design = _prerequisites(config)
        result = dry_run(config, design) if args.dry_run else run_hash_routing_signal_diagnostics(config, design)
        _write(result, args.output)
        return 0
    except Exception as exc:
        diagnostics = getattr(exc, "diagnostics", {}) if isinstance(exc, SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError) else {}
        result = {
            "status": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS",
            "error_code": str(exc).split(":")[0][:240],
            "candidate_shapes": diagnostics.get("candidate_shapes", []),
            "blocked_shapes": diagnostics.get("blocked_shapes", []),
            "safety": {
                "dynamic_candidate_network_sent": False,
                "pilot_limeira_values_sent": False,
                "resource_get_authorized": False,
                "collection_authorized": False,
                "processing_authorized": False,
                "recurrence_authorized": False,
                "schedule_enabled": False
            }
        }
        _write(result, args.output)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
