#!/usr/bin/env python3
"""Manual read-only SIOPE export request-expression refinement gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)
from robo_dados_publicos.sources.siope_export_request_refinement import (
    SiopeExportRequestRefinementError,
    load_export_request_refinement_config,
    refine_export_request_expressions,
)

EXPECTED_NEXT_ACTION = "M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0"


def _identity_ok() -> bool:
    return (
        SOFTWARE_VERSION == "0.8.0"
        and RELEASE_STATUS == "CANDIDATE"
        and ACTIVE_VALIDATED_VERSION == "0.7.0"
        and CURRENT_CANDIDATE_VERSION == "0.8.0"
        and NEXT_ACTION == EXPECTED_NEXT_ACTION
    )


def _safety_fields() -> dict:
    return {
        "remote_writes": "NONE",
        "candidate_route_requested": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "form_submission": False,
        "browser_automation_performed": False,
        "click_executed": False,
        "captcha_bypass": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_gate(config_path: str | Path, *, dry_run: bool = False) -> tuple[dict, int]:
    try:
        if not _identity_ok():
            raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_RELEASE_IDENTITY")
        path = Path(config_path)
        if not path.is_absolute():
            path = ROOT / path
        config = load_export_request_refinement_config(path)
        if dry_run:
            return {
                "status": "PASS_M7_SIOPE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_DRY_RUN",
                "gate_id": config["gate_id"],
                "software_version": config["software_version"],
                "page_get": 1,
                "declared_scripts_get_max": config["max_scripts"],
                "network_called": False,
                **_safety_fields(),
            }, 0
        return refine_export_request_expressions(config), 0
    except SiopeExportRequestRefinementError as exc:
        return {
            "status": "STOP_M7_SIOPE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_GATE",
            "reason": str(exc),
            "diagnostics": exc.diagnostics,
            **_safety_fields(),
        }, 22
    except Exception:
        return {
            "status": "STOP_M7_SIOPE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_UNEXPECTED",
            **_safety_fields(),
        }, 22


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/source_expansion.siope_export_request_refinement_gate.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload, code = run_gate(args.config, dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
