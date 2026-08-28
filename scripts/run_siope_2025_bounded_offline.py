#!/usr/bin/env python3
"""Safe offline CLI for TASK 003; it never provides a live transport."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_2025_bounded_runner import (  # noqa: E402
    STOP_LIVE_NOT_AUTHORIZED,
    Siope2025BoundedRunnerError,
    run_bounded,
)
from robo_dados_publicos.sources.siope_2025_fake_transport import FakeSiope2025Transport  # noqa: E402
from robo_dados_publicos.sources.siope_2025_request_plan import (  # noqa: E402
    materialize_request_plan,
    sanitized_plan_evidence,
)

CONFIG = ROOT / "config" / "siope_2025_bounded_runner.v1.json"
DESIGN = ROOT / "config" / "siope_2025_readonly_discovery_design.v1.json"
FIXTURES = ROOT / "tests" / "fixtures" / "siope_2025_readonly_discovery"
ALLOWED_FIXTURES = {"no_periods.json", "p6_exact_schema.json", "periods_without_p6.json"}


def _load_contracts() -> tuple[dict, dict]:
    return (
        json.loads(CONFIG.read_text(encoding="utf-8")),
        json.loads(DESIGN.read_text(encoding="utf-8")),
    )


def run_cli(*, fixture_name: str | None, live: bool = False, output: Path | None = None) -> dict:
    if live:
        raise Siope2025BoundedRunnerError(STOP_LIVE_NOT_AUTHORIZED)
    config, design = _load_contracts()

    if fixture_name is None:
        plan = materialize_request_plan(design)
        result = {
            "status": "PASS_SIOPE_2025_PLAN_ONLY_T0",
            "source_get_count": 0,
            "live_execution_authorized": False,
            "drive_read_count": 0,
            "drive_write_count": 0,
            "publication": False,
            "request_plan_evidence": sanitized_plan_evidence(plan, executed_ordinals=[]),
        }
    else:
        if fixture_name not in ALLOWED_FIXTURES:
            raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_FIXTURE_NOT_ALLOWED")
        fixture = json.loads((FIXTURES / fixture_name).read_text(encoding="utf-8"))
        result = run_bounded(
            runner_config=config,
            design=design,
            transport=FakeSiope2025Transport(fixture),
        )

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", choices=sorted(ALLOWED_FIXTURES))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run_cli(fixture_name=args.fixture, live=args.live, output=args.output)
    except (OSError, ValueError, Siope2025BoundedRunnerError) as exc:
        print(exc)
        return 13
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
