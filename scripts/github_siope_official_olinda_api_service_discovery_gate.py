from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_api_service_discovery import (  # noqa: E402
    SiopeOfficialOlindaApiServiceDiscoveryError,
    discover_service,
    dry_run,
    load_and_validate_design,
    load_json,
)

CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_service_discovery.json"
_ALLOWED_DIAGNOSTICS = {
    "http_status",
    "content_type",
    "service_document_parseable",
    "collection_name_count",
    "collection_names",
    "candidate_resource_present",
}


def _sanitized_stop(exc: SiopeOfficialOlindaApiServiceDiscoveryError) -> dict:
    diagnostics = {key: value for key, value in exc.diagnostics.items() if key in _ALLOWED_DIAGNOSTICS}
    return {
        "status": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY",
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_0_8_0",
        "error_code": str(exc),
        "network_scope": "EXACT_ONE_GET_OFFICIAL_SERVICE_ROOT_ONLY",
        "pilot_limeira_values_sent": False,
        "request_body_sent": False,
        "redirect_followed": False,
        "service_link_followed": False,
        "raw_response_persisted": False,
        "query_values_persisted": False,
        "authentication_performed": False,
        "captcha_bypass": False,
        "artifact_downloaded": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "diagnostics": diagnostics,
    }


def _write(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    print(text)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    config = load_json(CONFIG)
    design = load_and_validate_design(ROOT, config)
    try:
        result = dry_run(config, design) if args.dry_run else discover_service(config, design)
    except SiopeOfficialOlindaApiServiceDiscoveryError as exc:
        _write(_sanitized_stop(exc), args.output)
        return 1
    except Exception:
        _write(
            {
                "status": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY",
                "gate_id": config.get("gate_id", "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_0_8_0"),
                "error_code": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_UNEXPECTED",
                "pilot_limeira_values_sent": False,
                "raw_response_persisted": False,
                "query_values_persisted": False,
                "remote_writes": "NONE",
                "collection_authorized": False,
                "processing_authorized": False,
                "recurrence_authorized": False,
                "schedule_enabled": False,
            },
            args.output,
        )
        return 1
    _write(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
