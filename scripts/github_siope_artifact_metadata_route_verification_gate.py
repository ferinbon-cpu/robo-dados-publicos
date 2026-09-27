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
from robo_dados_publicos.sources.siope_artifact_metadata_route_verification import (
    SiopeArtifactMetadataVerificationError,
    load_artifact_metadata_verification_config,
    verify_artifact_metadata_route,
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
        "raw_metadata_persisted": False,
        "response_body_persisted": False,
        "query_values_persisted": False,
        "request_headers_persisted": False,
        "cookies_persisted": False,
        "download_candidate_requested": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_gate(config_path: str | Path, *, dry_run: bool = False, client=None) -> tuple[dict, int]:
    try:
        if not _identity_ok():
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_RELEASE_IDENTITY")
        path = Path(config_path)
        if not path.is_absolute():
            path = ROOT / path
        config = load_artifact_metadata_verification_config(path)
        if dry_run:
            return {
                "status": "PASS_M7_SIOPE_ARTIFACT_METADATA_ROUTE_VERIFICATION_DRY_RUN",
                "gate_id": config["gate_id"],
                "software_version": config["software_version"],
                "network_called": False,
                "network_method": None,
                **_safety_fields(),
            }, 0
        return verify_artifact_metadata_route(config, client=client), 0
    except SiopeArtifactMetadataVerificationError as exc:
        return {
            "status": "STOP_M7_SIOPE_ARTIFACT_METADATA_ROUTE_VERIFICATION_GATE",
            "reason": str(exc),
            "diagnostics": exc.diagnostics,
            **_safety_fields(),
        }, 28
    except Exception:
        return {
            "status": "STOP_M7_SIOPE_ARTIFACT_METADATA_ROUTE_VERIFICATION_UNEXPECTED",
            **_safety_fields(),
        }, 28


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/source_expansion.siope_artifact_metadata_route_verification_gate.json",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload, code = run_gate(args.config, dry_run=args.dry_run)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
