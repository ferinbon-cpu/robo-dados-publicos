from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_public_indexed_get_contract import (
    SiopePublicIndexedGetContractError,
    load_public_indexed_get_contract_config,
    verify_public_indexed_get_contract,
)

CONFIG = ROOT / "config" / "source_expansion.siope_public_indexed_get_contract_gate.json"


def _emit(result: dict, output: str | None) -> None:
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")


def _closed(
    status: str,
    *,
    reason: str | None = None,
    diagnostics: dict | None = None,
    network_called: bool = False,
    indexed_example_query_sent: bool = False,
) -> dict:
    result = {
        "status": status,
        "network_called": network_called,
        "network_method": "GET_ONLY",
        "indexed_example_query_sent": indexed_example_query_sent,
        "pilot_limeira_values_sent": False,
        "form_submission": False,
        "captcha_bypass": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "response_body_persisted": False,
        "query_values_persisted": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
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
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    config = load_public_indexed_get_contract_config(CONFIG)
    if args.dry_run:
        _emit(_closed("PASS_M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_DRY_RUN"), args.output)
        return 0
    try:
        result = verify_public_indexed_get_contract(config)
    except SiopePublicIndexedGetContractError as exc:
        _emit(
            _closed(
                "STOP_M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_GATE",
                reason=str(exc),
                diagnostics=exc.diagnostics,
                network_called=exc.network_called,
                indexed_example_query_sent=exc.indexed_example_query_sent,
            ),
            args.output,
        )
        return 34
    except Exception:
        _emit(
            _closed(
                "STOP_M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_GATE",
                reason="STOP_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_UNEXPECTED_RUNTIME_ERROR",
                network_called=True,
            ),
            args.output,
        )
        return 34
    _emit(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
