#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.reconciliation.rollout import (  # noqa: E402
    ReconciliationRolloutError,
    select_next_ready_task,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select one next READY_SEARCH task from exact pinned reconciliation-plan bytes.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--target-source", required=True)
    parser.add_argument("--exclude-task-id", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        result = select_next_ready_task(
            Path(args.plan).read_bytes(),
            expected_sha256=args.expected_sha256,
            target_source=args.target_source,
            consumed_task_ids=args.exclude_task_id,
        )
        exit_code = 0
    except (OSError, ReconciliationRolloutError) as exc:
        result = {"status": "STOP_RECONCILIATION_NEXT_TASK_SELECTION", "error": str(exc)}
        exit_code = 13

    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
