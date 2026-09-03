#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.mde_fundeb_gold_preview import (  # noqa: E402
    build_preview,
    load_json,
    validate_config,
)

DEFAULT_CONFIG = ROOT / "config/manual_supervised_ingest_f02_gold_preview.v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline fail-closed F02 Gold preview.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    config = load_json(args.config)
    if args.dry_run:
        print(json.dumps(validate_config(config), sort_keys=True))
        return 0

    candidate, result = build_preview(config, root=ROOT)
    rendered = json.dumps(candidate, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if result["gold_payload_persisted"] or result["drive_write_count"] != 0:
        raise RuntimeError("STOP_F02_GOLD_PREVIEW_UNEXPECTED_EFFECT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
