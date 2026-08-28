#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.product.siope_historical_drive_readonly import describe_gate, run_readonly_gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir")
    parser.add_argument("--generated-at")
    args = parser.parse_args()

    if args.dry_run:
        result = describe_gate(root=ROOT)
    else:
        if not args.output_dir:
            parser.error("--output-dir is required outside --dry-run")
        generated_at = args.generated_at or datetime.now(timezone.utc).isoformat()
        result = run_readonly_gate(
            root=ROOT,
            output_dir=args.output_dir,
            generated_at=generated_at,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
