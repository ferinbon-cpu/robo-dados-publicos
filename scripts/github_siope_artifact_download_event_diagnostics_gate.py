from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_artifact_download_event_diagnostics import diagnose_artifact_download_event
from robo_dados_publicos.sources.siope_artifact_download_runtime_route_probe import load_artifact_download_runtime_route_probe_config
from robo_dados_publicos.sources.siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError

CONFIG = ROOT / "config" / "source_expansion.siope_artifact_download_runtime_route_probe_gate.json"


def _emit(result: dict, output: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")


def _safety(status: str, reason: str | None = None) -> dict:
    out = {
        "status": status,
        "candidate_route_network_sent": False,
        "browser_download_denied": True,
        "artifact_downloaded": False,
        "response_body_captured": False,
        "request_body_captured": False,
        "request_headers_captured": False,
        "cookies_captured": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
    if reason:
        out["stop_reason"] = reason
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    config = load_artifact_download_runtime_route_probe_config(CONFIG)
    if args.dry_run:
        _emit(_safety("PASS_M7_SIOPE_ARTIFACT_DOWNLOAD_EVENT_DIAGNOSTICS_DRY_RUN"), args.output)
        return 0
    try:
        result = diagnose_artifact_download_event(config)
    except SiopeRuntimeRouteProbeError as exc:
        _emit(_safety("STOP_M7_SIOPE_ARTIFACT_DOWNLOAD_EVENT_DIAGNOSTICS_GATE", str(exc)), args.output)
        return 31
    _emit(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
