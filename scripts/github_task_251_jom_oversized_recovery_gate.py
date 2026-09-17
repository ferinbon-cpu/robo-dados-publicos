#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

from robo_dados_publicos.research.task251_jom_7323_7324_oversized_recovery import (
    Task251Stop,
    validate_offline_carrier,
)


def main() -> int:
    try:
        result = validate_offline_carrier()
    except (Task251Stop, KeyError, TypeError, ValueError) as exc:
        print(f"TASK251_GATE_STOP={exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status") == "PASS_TASK251_OFFLINE_CARRIER" else 1


if __name__ == "__main__":
    sys.exit(main())
