#!/usr/bin/env python3
"""Manual read-only route discovery gate for SIOPE/FNDE surfaces."""

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
from robo_dados_publicos.sources.siope_route_discovery import (
    SiopeRouteDiscoveryError,
    discover_siope_routes,
    load_route_discovery_config,
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


def run_gate(config_path: str | Path, *, dry_run: bool = False) -> tuple[dict, int]:
    try:
        if not _identity_ok():
            raise SiopeRouteDiscoveryError("STOP_SIOPE_ROUTE_RELEASE_IDENTITY")
        path = Path(config_path)
        if not path.is_absolute():
            path = ROOT / path
        config = load_route_discovery_config(path)
        if dry_run:
            return {
                "status": "PASS_M7_SIOPE_ROUTE_DISCOVERY_DRY_RUN",
                "gate_id": config["gate_id"],
                "software_version": config["software_version"],
                "would_get": 2,
                "allowed_hosts": config["allowed_hosts"],
                "form_submission": False,
                "captcha_bypass": False,
                "artifact_downloaded": False,
                "network_called": False,
                "remote_writes": "NONE",
                "collection_authorized": False,
                "recurrence_authorized": False,
                "schedule_enabled": False,
            }, 0
        return discover_siope_routes(config), 0
    except SiopeRouteDiscoveryError as exc:
        return {
            "status": "STOP_M7_SIOPE_ROUTE_DISCOVERY_GATE",
            "reason": str(exc),
            "remote_writes": "NONE",
            "form_submission": False,
            "captcha_bypass": False,
            "artifact_downloaded": False,
            "collection_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, 18
    except Exception:
        return {
            "status": "STOP_M7_SIOPE_ROUTE_DISCOVERY_UNEXPECTED",
            "remote_writes": "NONE",
            "form_submission": False,
            "captcha_bypass": False,
            "artifact_downloaded": False,
            "collection_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, 18


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/source_expansion.siope_route_discovery_gate.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload, code = run_gate(args.config, dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
