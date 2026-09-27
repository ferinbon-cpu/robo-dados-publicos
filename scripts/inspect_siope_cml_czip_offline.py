#!/usr/bin/env python3
"""Inspect one explicitly supplied local SIOPE outer metadata package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from robo_dados_publicos.sources.siope_cml_codec import CodecError, decode_outer_metadata_package


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, help="explicit path to a local outer ZIP")
    args = parser.parse_args()
    try:
        result = decode_outer_metadata_package(args.package)
    except CodecError as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
