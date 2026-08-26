from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_live_validation import (  # noqa: E402
    SiopeClientLimeiraLiveValidationError,
    run_validation,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_live_validation.json"


def _write(path: str | None, payload: dict) -> None:
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise SiopeClientLimeiraLiveValidationError("STOP_M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_CONFIG_OBJECT_REQUIRED")
        result = validate_config(config) if args.dry_run else run_validation(config)
        _write(args.output, result)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, SiopeClientLimeiraLiveValidationError) as exc:
        result = {"status": str(exc), "request_count": int(getattr(exc, "request_count", 0) or 0)}
        _write(args.output, result)
        print(json.dumps(result, sort_keys=True))
        return 13


if __name__ == "__main__":
    raise SystemExit(main())
