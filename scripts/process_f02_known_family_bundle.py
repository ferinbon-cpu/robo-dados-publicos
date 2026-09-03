#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f02_known_family_bundle import (  # noqa: E402
    load_json,
    run_known_family_bundle,
)

DEFAULT_ADAPTER = ROOT / "config/f02_known_family_bundle_adapter.v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an offline reusable F02 known-family bundle.")
    parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--output")
    args = parser.parse_args()

    result, telemetry = run_known_family_bundle(
        load_json(args.adapter),
        load_json(args.manifest),
        root=args.root,
    )
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if telemetry["remote_effects"] != 0 or telemetry["gold_authorized"]:
        raise RuntimeError("STOP_F02_KNOWN_BUNDLE_UNEXPECTED_EFFECT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
