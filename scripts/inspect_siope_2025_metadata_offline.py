#!/usr/bin/env python3
"""Inspect an already-local metadata artifact; this command has no network code."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_2025_metadata_inspector import InspectionError, dumps, inspect


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    try:
        print(dumps(inspect(args.artifact)), end="")
    except InspectionError as exc:
        print(exc)
        return 13
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
