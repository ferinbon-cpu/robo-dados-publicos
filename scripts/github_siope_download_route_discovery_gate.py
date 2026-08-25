#!/usr/bin/env python3
"""Manual read-only discovery of an explicit Antonieta download route candidate."""

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
from robo_dados_publicos.sources.siope_download_route_discovery import (
    SiopeDownloadRouteDiscoveryError,
    discover_download_route,
    load_download_route_discovery_config,
)

# The canonical release NEXT_ACTION remains the broad M7 route-discovery stage
# until a concrete acquisition route is proven. This is a subordinate read-only gate.
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
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_RELEASE_IDENTITY")
        path = Path(config_path)
        if not path.is_absolute():
            path = ROOT / path
        config = load_download_route_discovery_config(path)
        if dry_run:
            return {
                "status": "PASS_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_DRY_RUN",
                "gate_id": config["gate_id"],
                "software_version": config["software_version"],
                "page_get": 1,
                "declared_scripts_get_max": config["max_scripts"],
                "artifact_downloaded": False,
                "head_request_performed": False,
                "form_submission": False,
                "captcha_bypass": False,
                "network_called": False,
                "remote_writes": "NONE",
                "collection_authorized": False,
                "processing_authorized": False,
                "recurrence_authorized": False,
                "schedule_enabled": False,
            }, 0
        return discover_download_route(config), 0
    except SiopeDownloadRouteDiscoveryError as exc:
        return {
            "status": "STOP_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_GATE",
            "reason": str(exc),
            "remote_writes": "NONE",
            "artifact_downloaded": False,
            "head_request_performed": False,
            "form_submission": False,
            "captcha_bypass": False,
            "collection_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, 19
    except Exception:
        return {
            "status": "STOP_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_UNEXPECTED",
            "remote_writes": "NONE",
            "artifact_downloaded": False,
            "head_request_performed": False,
            "form_submission": False,
            "captcha_bypass": False,
            "collection_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
        }, 19


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/source_expansion.siope_download_route_discovery_gate.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload, code = run_gate(args.config, dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
