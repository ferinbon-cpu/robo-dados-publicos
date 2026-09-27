from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_silver_single_record_transform_preview import (  # noqa: E402
    SilverTransformPreviewError,
    load_json,
    preview,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_silver_single_record_transform_preview.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = load_json(CONFIG)
        result = validate_config(config) if args.dry_run else preview(config, root=ROOT)
    except (SilverTransformPreviewError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 22
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
