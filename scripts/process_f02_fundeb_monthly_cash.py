#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash import (  # noqa: E402
    load_and_validate_global_policy,
    load_manifest,
    load_pinned_authorization,
    run_monthly_series,
    validate_offline_telemetry,
)

CONTRACT = ROOT / "config/f02_fundeb_monthly_cash_series.v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline monthly FUNDEB cash/balance series.")
    parser.add_argument("--manifest", required=True, help="Repository-relative source manifest JSON.")
    parser.add_argument("--authorization", required=True, help="Repository-relative authorization JSON.")
    parser.add_argument("--authorization-sha256", required=True)
    args = parser.parse_args()

    load_and_validate_global_policy(root=ROOT)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    manifest = load_manifest(root=ROOT, relative_path=args.manifest)
    authorization = load_pinned_authorization(
        root=ROOT,
        relative_path=args.authorization,
        expected_sha256=args.authorization_sha256,
    )
    result, telemetry = run_monthly_series(
        contract,
        manifest,
        root=ROOT,
        authorization=authorization,
    )
    validate_offline_telemetry(telemetry)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
