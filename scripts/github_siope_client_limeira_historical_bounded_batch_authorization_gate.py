from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_client_limeira_historical_bounded_batch_authorization import (  # noqa: E402
    HistoricalBoundedBatchAuthorizationError,
    run_bounded_batch,
)

CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_bounded_batch_authorization.json"
OUT = ROOT / "siope-client-limeira-historical-bounded-batch-authorization-evidence/result.json"
STOP = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_BOUNDED_BATCH_AUTHORIZATION"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        result = run_bounded_batch(config, root=ROOT)
    except (HistoricalBoundedBatchAuthorizationError, OSError, ValueError, KeyError) as exc:
        result = {"status": STOP, "error": str(exc)}
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(result["status"])
        print(result["error"], file=sys.stderr)
        return 13
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
