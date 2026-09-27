from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_bounded_batch_source_probe import (  # noqa: E402
    ERROR,
    HistoricalBoundedBatchSourceProbeError,
    run_source_probe,
    validate_config,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_bounded_batch_source_probe.json"
DEFAULT_OUT = ROOT / "siope-client-limeira-historical-bounded-batch-source-probe-evidence/result.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        result = validate_config(config, root=ROOT) if args.dry_run else run_source_probe(config, root=ROOT)
    except (HistoricalBoundedBatchSourceProbeError, OSError, ValueError, KeyError) as exc:
        result = {"status": ERROR, "error": str(exc), "drive_called": False, "drive_write_count": 0}
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(result["status"])
        return 13

    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0 if result["status"].startswith("PASS_") else 13


if __name__ == "__main__":
    raise SystemExit(main())
