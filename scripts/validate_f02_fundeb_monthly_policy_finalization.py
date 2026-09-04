#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.automation.f02_fundeb_monthly_policy_finalization import (  # noqa: E402
    F02FundebMonthlyPolicyFinalizationStop,
    validate_repository_state,
)


def main() -> int:
    try:
        result = validate_repository_state(ROOT)
    except F02FundebMonthlyPolicyFinalizationStop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
