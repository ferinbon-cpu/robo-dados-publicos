from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_public_get_runtime_cdp_direct import (
    SystemChromeCdpPublicGetRuntimeDirect,
)
from robo_dados_publicos.sources.siope_public_get_runtime_route_diagnostics import (
    SiopePublicGetRuntimeRouteDiagnosticsError,
    load_public_get_runtime_route_diagnostics_config,
    probe_public_get_runtime_routes,
)

CONFIG = ROOT / "config" / "source_expansion.siope_public_get_runtime_route_diagnostics_gate.json"


def _emit(result: dict, output: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")


def _closed(status: str, *, reason: str | None = None, diagnostics: dict | None = None) -> dict:
    result = {
        "status": status,
        "initial_document_network_sent": False,
        "pilot_limeira_values_sent": False,
        "dynamic_candidate_network_sent": False,
        "form_submission": False,
        "captcha_bypass": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "request_body_persisted": False,
        "response_body_persisted": False,
        "query_values_persisted": False,
        "head_request_performed": False,
        "artifact_downloaded": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
    if reason:
        result["stop_reason"] = reason
    if diagnostics:
        result["diagnostics"] = diagnostics
        if isinstance(diagnostics.get("initial_document_network_sent"), bool):
            result["initial_document_network_sent"] = diagnostics["initial_document_network_sent"]
        if isinstance(diagnostics.get("dynamic_candidate_network_sent"), bool):
            result["dynamic_candidate_network_sent"] = diagnostics["dynamic_candidate_network_sent"]
        if isinstance(diagnostics.get("browser_download_denied"), bool):
            result["browser_download_denied"] = diagnostics["browser_download_denied"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    config = load_public_get_runtime_route_diagnostics_config(CONFIG)
    if args.dry_run:
        _emit(_closed("PASS_M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_DRY_RUN"), args.output)
        return 0

    try:
        result = probe_public_get_runtime_routes(
            config,
            runtime=SystemChromeCdpPublicGetRuntimeDirect(),
        )
    except SiopePublicGetRuntimeRouteDiagnosticsError as exc:
        _emit(
            _closed(
                "STOP_M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS",
                reason=str(exc),
                diagnostics=exc.diagnostics,
            ),
            args.output,
        )
        return 35
    except Exception:
        _emit(
            _closed(
                "STOP_M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS",
                reason="STOP_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_UNEXPECTED_RUNTIME_ERROR",
            ),
            args.output,
        )
        return 35

    _emit(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
