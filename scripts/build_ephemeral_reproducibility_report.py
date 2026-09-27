from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from robo_dados_publicos.manual_ingest.ephemeral_reproducibility import (
    ReproducibilityStop,
    persist_observation_then_compare,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Persist a local ephemeral-digest observation before comparing it "
            "with historical expectations."
        )
    )
    parser.add_argument("--digest-result", required=True)
    parser.add_argument("--historical-expectation", required=True)
    parser.add_argument("--observation-out", required=True)
    parser.add_argument("--report-out", required=True)
    args = parser.parse_args()

    try:
        result = persist_observation_then_compare(
            _load(Path(args.digest_result)),
            _load(Path(args.historical_expectation)),
            observation_path=Path(args.observation_out),
            report_path=Path(args.report_out),
        )
    except (OSError, json.JSONDecodeError, ReproducibilityStop) as exc:
        print(
            json.dumps(
                {
                    "status": "STOP_TASK092_REPRODUCIBILITY_HARDENING",
                    "reason": f"{type(exc).__name__}:{exc}",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 92

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
