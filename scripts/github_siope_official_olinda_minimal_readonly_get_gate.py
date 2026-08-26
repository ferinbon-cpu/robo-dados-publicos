from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_official_olinda_minimal_readonly_get import (
    SiopeOfficialOlindaMinimalReadonlyGetError,
    load_config,
    run_minimal_get,
    validate_design,
)

CONFIG = ROOT / "config/source_expansion.siope_official_olinda_minimal_readonly_get_design.json"


def _write(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    config = load_config(CONFIG)
    if args.dry_run:
        _write(validate_design(config), args.output)
        return 0
    try:
        result = run_minimal_get(config)
    except SiopeOfficialOlindaMinimalReadonlyGetError as exc:
        _write(
            {
                "status": str(exc),
                "gate_id": config["live_gate_id"],
                "source_id": config["source_id"],
                "software_version": config["software_version"],
                "network_called": bool(exc.network_called),
                "request_count": int(exc.request_count),
                "pilot_limeira_values_sent": False,
                "redirect_followed": False,
                "odata_nextlink_followed": False,
                "response_body_persisted": False,
                "record_values_persisted": False,
                "nextlink_url_persisted": False,
                "query_values_persisted_in_result": False,
                "remote_writes": "NONE",
                "collection_authorized": False,
                "processing_authorized": False,
                "recurrence_authorized": False,
                "schedule_enabled": False,
                "automatic_route_promotion": False,
                "ongoing_resource_get_authorized": False,
            },
            args.output,
        )
        return 13
    _write(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
