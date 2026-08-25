from __future__ import annotations

import argparse
import json
from pathlib import Path

from robo_dados_publicos.sources.siope_artifact_download_runtime_route_probe import (
    load_artifact_download_runtime_route_probe_config,
    probe_artifact_download_runtime_route,
)
from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_artifact_download_runtime_route_probe_gate.json"


def _safety(status: str, reason: str | None = None, diagnostics: dict | None = None) -> dict:
    out = {
        "status": status,
        "network_called": False,
        "verified_metadata_network_sent": False,
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
    if reason:
        out["stop_reason"] = reason
    if diagnostics:
        out["diagnostics"] = diagnostics
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = load_artifact_download_runtime_route_probe_config(CONFIG)
    if args.dry_run:
        print(json.dumps(_safety("PASS_M7_SIOPE_ARTIFACT_DOWNLOAD_RUNTIME_ROUTE_PROBE_DRY_RUN"), indent=2, sort_keys=True))
        return 0
    try:
        result = probe_artifact_download_runtime_route(config)
    except SiopeRuntimeRouteProbeError as exc:
        result = _safety(
            "STOP_M7_SIOPE_ARTIFACT_DOWNLOAD_RUNTIME_ROUTE_PROBE_GATE",
            reason=str(exc),
            diagnostics=getattr(exc, "diagnostics", None),
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 29
    result["network_called"] = True
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
