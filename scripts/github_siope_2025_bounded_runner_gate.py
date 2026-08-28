#!/usr/bin/env python3
"""Exercise the TASK 003 bounded runner with fake transport only."""

from __future__ import annotations

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
from scripts.run_siope_2025_bounded_offline import run_cli  # noqa: E402

CONFIG = ROOT / "config" / "siope_2025_bounded_runner.v1.json"
DESIGN = ROOT / "config" / "siope_2025_readonly_discovery_design.v1.json"
FIXTURE = ROOT / "tests" / "fixtures" / "siope_2025_readonly_discovery" / "p6_exact_schema.json"
PASS = "PASS_SIOPE_2025_BOUNDED_RUNNER_GATE_T0"


def validate_gate() -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    try:
        run_bounded(runner_config=config, design=design)
    except Siope2025BoundedRunnerError as exc:
        if str(exc) != STOP_LIVE_NOT_AUTHORIZED:
            raise
    else:
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_LIVE_GUARD_MISSING")

    result = run_bounded(
        runner_config=config,
        design=design,
        transport=FakeSiope2025Transport(fixture),
    )
    if result["fake_request_count"] != 7 or result["source_get_count"] != 0:
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_GATE_COUNT")
    if result["network_called"] or result["drive_called"] or result["response_persisted"] or result["publication"]:
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_GATE_EFFECT")
    if result["annual_closure_status"] != "UNKNOWN" or result["promote_2025_to_proven"]:
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_GATE_PROMOTION")
    if any(status != "UNKNOWN" for status in result["metric_statuses"].values()):
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_GATE_METRIC")

    plan_only = run_cli(fixture_name=None)
    if plan_only["status"] != "PASS_SIOPE_2025_PLAN_ONLY_T0" or plan_only["source_get_count"] != 0:
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_PLAN_ONLY")
    try:
        run_cli(fixture_name=None, live=True)
    except Siope2025BoundedRunnerError as exc:
        if str(exc) != STOP_LIVE_NOT_AUTHORIZED:
            raise
    else:
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_CLI_LIVE_GUARD_MISSING")

    evidence = result["observation_evidence"]
    if evidence["source_get_count"] != 0 or evidence["drive_write_count"] != 0 or evidence["publication"]:
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_EVIDENCE_EFFECT")
    if evidence["any_metric_proven"] or evidence["annual_closure_status"] != "UNKNOWN":
        raise Siope2025BoundedRunnerError("STOP_SIOPE_2025_BOUNDED_RUNNER_EVIDENCE_PROMOTION")

    return {
        "status": PASS,
        "runner_status": result["status"],
        "fake_request_count": result["fake_request_count"],
        "source_get_count": 0,
        "live_guard": STOP_LIVE_NOT_AUTHORIZED,
        "network_called": False,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "runtime_execution_authorized": False,
        "live_execution_authorized": False,
    }


def main() -> int:
    try:
        result = validate_gate()
    except (OSError, ValueError, Siope2025BoundedRunnerError) as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
