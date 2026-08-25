#!/usr/bin/env python3
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
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)
from robo_dados_publicos.sources.siope_export_runtime_route_probe_design import (
    SiopeRuntimeRouteProbeDesignError,
    load_runtime_route_probe_design,
    validate_runtime_route_probe_design,
)


def _identity_ok() -> bool:
    return (
        SOFTWARE_VERSION == "0.8.0"
        and RELEASE_STATUS == "CANDIDATE"
        and ACTIVE_VALIDATED_VERSION == "0.7.0"
        and CURRENT_CANDIDATE_VERSION == "0.8.0"
    )


def run_gate(path: str | Path) -> tuple[dict, int]:
    try:
        if not _identity_ok():
            raise SiopeRuntimeRouteProbeDesignError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DESIGN_RELEASE_IDENTITY")
        config_path = Path(path)
        if not config_path.is_absolute():
            config_path = ROOT / config_path
        config = load_runtime_route_probe_design(config_path)
        return validate_runtime_route_probe_design(config), 0
    except SiopeRuntimeRouteProbeDesignError as exc:
        return {
            "status": "STOP_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_GATE",
            "reason": str(exc),
            "browser_execution": False,
            "click_executed": False,
            "candidate_route_network_sent": False,
            "artifact_downloaded": False,
            "remote_writes": "NONE",
            "collection_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, 23
    except Exception:
        return {
            "status": "STOP_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_UNEXPECTED",
            "browser_execution": False,
            "click_executed": False,
            "candidate_route_network_sent": False,
            "artifact_downloaded": False,
            "remote_writes": "NONE",
            "collection_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, 23


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/source_expansion.siope_export_runtime_route_probe_design.json",
    )
    args = parser.parse_args()
    payload, code = run_gate(args.config)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
