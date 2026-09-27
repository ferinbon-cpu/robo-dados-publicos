#!/usr/bin/env python3
"""Offline-only gate for the 0.8.0 controlled source expansion design."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)
from robo_dados_publicos.sources.expansion import SourceExpansionError, load_source_expansion_gate

EXPECTED_NEXT_ACTION = "M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0"


def run_gate(config_path: str | Path) -> tuple[dict, int]:
    try:
        if not (
            SOFTWARE_VERSION == "0.8.0"
            and RELEASE_STATUS == "CANDIDATE"
            and ACTIVE_VALIDATED_VERSION == "0.7.0"
            and CURRENT_CANDIDATE_VERSION == "0.8.0"
            and NEXT_ACTION == EXPECTED_NEXT_ACTION
        ):
            raise SourceExpansionError("SOURCE_EXPANSION_RELEASE_IDENTITY")
        path = Path(config_path)
        if not path.is_absolute():
            path = ROOT / path
        gate = load_source_expansion_gate(path)
        return gate.summary(), 0
    except SourceExpansionError as exc:
        return {
            "status": "STOP_M7_SOURCE_EXPANSION_DESIGN_GATE",
            "reason": str(exc),
            "network_called": False,
            "remote_writes": "NONE",
        }, 17
    except Exception:
        return {
            "status": "STOP_M7_SOURCE_EXPANSION_DESIGN_UNEXPECTED",
            "network_called": False,
            "remote_writes": "NONE",
        }, 17


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="config/source_expansion.siope_limeira_0_8_0.json",
    )
    args = parser.parse_args()
    payload, code = run_gate(args.config)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
