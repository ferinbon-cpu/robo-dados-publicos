#!/usr/bin/env python3
"""Validate TASK 009C preparation without network or remote effects."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_2025_metadata_resolved_path_probe import (
    MetadataResolvedPathProbeError,
    validate_preparation_contract,
)

PREP = ROOT / "config" / "siope_2025_metadata_resolved_path_probe_preparation.v1.json"
TEMPLATE = ROOT / "config" / "siope_2025_metadata_resolved_path_probe_authorization.template.v1.json"
POLICY = ROOT / "config" / "automation_policy.v1.json"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"OBJECT_REQUIRED:{path.name}")
    return value


def main() -> int:
    try:
        validate_preparation_contract(_load(PREP), _load(TEMPLATE), _load(POLICY))
    except (MetadataResolvedPathProbeError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 13
    print(json.dumps({
        "status": "PASS_TASK009C_RESOLVED_PATH_PREPARATION_OFFLINE",
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "live_execution_authorized": False,
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "gold_metrics_status": "UNKNOWN"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
