from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_public_runtime_control_inventory import (  # noqa: E402
    SiopePublicRuntimeControlInventoryError,
    inventory_public_runtime_controls,
    load_json,
)

CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_control_inventory_gate.json"


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
        "dom_interaction_performed": False,
        "form_submission": False,
        "control_values_captured": False,
        "option_text_captured": False,
        "option_values_captured": False,
        "html_captured": False,
        "free_text_captured": False,
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
        "route_synthesized_or_guessed": False,
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
        if isinstance(diagnostics.get("browser_download_denied"), bool):
            result["browser_download_denied"] = diagnostics["browser_download_denied"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    config = load_json(CONFIG)
    public_config = load_json(ROOT / config["public_runtime_config_path"])
    design_config = load_json(ROOT / config["design_config_path"])
    if args.dry_run:
        from robo_dados_publicos.sources.siope_public_runtime_control_inventory import validate_inventory_config
        validate_inventory_config(config, public_config, design_config)
        _emit(_closed("PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_DRY_RUN"), args.output)
        return 0

    try:
        result = inventory_public_runtime_controls(config, public_config, design_config)
    except SiopePublicRuntimeControlInventoryError as exc:
        _emit(
            _closed(
                "STOP_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY",
                reason=str(exc),
                diagnostics=exc.diagnostics,
            ),
            args.output,
        )
        return 36
    except Exception:
        _emit(
            _closed(
                "STOP_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY",
                reason="STOP_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_UNEXPECTED_RUNTIME_ERROR",
            ),
            args.output,
        )
        return 36

    _emit(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
