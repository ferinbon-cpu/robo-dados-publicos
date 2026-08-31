#!/usr/bin/env python3
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.operational import OperationalCycle


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        result = OperationalCycle.from_file(ROOT / "config/operational_cycle.limeira_pilot.v1.json").run(
            Path(raw) / "cycle", started_at="2026-08-31T00:00:00+00:00"
        )
    effects = result["effects"]
    expected = {"network_requests": 0, "drive_reads": 0, "drive_writes": 0, "source_collection": 0, "live_reconciliation": 0}
    passed = result["status"] == "PASS" and effects == expected
    print(json.dumps({"gate": "TASK_017_OPERATIONAL_CYCLE_OFFLINE", "status": "PASS" if passed else "FAIL", "effects": effects}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
