from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_ws_public_discovery import (
    SiopeWsPublicDiscoveryError,
    discover_ws_public_surface,
    load_ws_public_discovery_config,
)

CONFIG = ROOT / "config" / "source_expansion.siope_ws_public_discovery_design.json"


def _emit(result: dict, output: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")


def _closed(status: str, *, reason: str | None = None, diagnostics: dict | None = None) -> dict:
    out = {
        "status": status,
        "network_method": "GET_ONLY",
        "endpoint_candidate_network_sent": False,
        "form_submission": False,
        "captcha_bypass": False,
        "authentication_performed": False,
        "credentials_captured": False,
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
    parser.add_argument("--output")
    args = parser.parse_args()
    config = load_ws_public_discovery_config(CONFIG)
    if args.dry_run:
        _emit(_closed("PASS_M7_SIOPE_WS_PUBLIC_DISCOVERY_DRY_RUN"), args.output)
        return 0
    try:
        result = discover_ws_public_surface(config)
    except SiopeWsPublicDiscoveryError as exc:
        _emit(
            _closed(
                "STOP_M7_SIOPE_WS_PUBLIC_DISCOVERY_GATE",
                reason=str(exc),
                diagnostics=exc.diagnostics,
            ),
            args.output,
        )
        return 33
    except Exception:
        _emit(
            _closed(
                "STOP_M7_SIOPE_WS_PUBLIC_DISCOVERY_GATE",
                reason="STOP_SIOPE_WS_PUBLIC_DISCOVERY_UNEXPECTED_RUNTIME_ERROR",
            ),
            args.output,
        )
        return 33
    _emit(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
