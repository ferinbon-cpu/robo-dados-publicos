from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_bronze_single_record_capture import (  # noqa: E402
    capture,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_bronze_single_record_capture.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir", default="siope-client-limeira-bronze-single-record-capture-evidence")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if args.dry_run:
        result = validate_config(config)
    else:
        out = ROOT / args.output_dir
        result = capture(config, output_dir=out)
        (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
