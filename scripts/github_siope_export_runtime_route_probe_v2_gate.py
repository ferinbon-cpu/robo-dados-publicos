#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.release import ACTIVE_VALIDATED_VERSION, CURRENT_CANDIDATE_VERSION, RELEASE_STATUS, SOFTWARE_VERSION
from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError
from robo_dados_publicos.sources.siope_export_runtime_route_probe_v2 import (
    load_runtime_route_probe_v2_config,
    probe_export_runtime_route_v2,
)


def _identity_ok() -> bool:
    return (
        SOFTWARE_VERSION == "0.8.0"
        and RELEASE_STATUS == "CANDIDATE"
        and ACTIVE_VALIDATED_VERSION == "0.7.0"
        and CURRENT_CANDIDATE_VERSION == "0.8.0"
    )


def _safety_fields() -> dict:
    return {
        "candidate_route_network_sent": False,
        "response_body_captured": False,
        "request_body_captured": False,
        "request_headers_captured": False,
        "cookies_captured": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_gate(config_path: str | Path, *, dry_run: bool = False, runtime=None) -> tuple[dict, int]:
    try:
        if not _identity_ok():
            raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_RELEASE_IDENTITY")
        path = Path(config_path)
        if not path.is_absolute():
            path = ROOT / path
        config = load_runtime_route_probe_v2_config(path)
        if dry_run:
            return {
                "status": "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_V2_DRY_RUN",
                "gate_id": config["gate_id"],
                "software_version": config["software_version"],
                "browser_execution": False,
                "click_executed": False,
                "network_called": False,
                "static_asset_allowlist_used": False,
                **_safety_fields(),
            }, 0
        return probe_export_runtime_route_v2(config, runtime=runtime), 0
    except SiopeRuntimeRouteProbeError as exc:
        return {
            "status": "STOP_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_V2_GATE",
            "reason": str(exc),
            "diagnostics": exc.diagnostics,
            **_safety_fields(),
        }, 27
    except Exception:
        return {
            "status": "STOP_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_V2_UNEXPECTED",
            **_safety_fields(),
        }, 27


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/source_expansion.siope_export_runtime_route_probe_v2_gate.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload, code = run_gate(args.config, dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
