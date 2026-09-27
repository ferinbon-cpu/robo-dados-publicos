#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.f02_known_family_bundle import (  # noqa: E402
    load_json,
    load_pinned_runtime_authorization,
    load_runtime_manifest,
    run_known_family_bundle,
)

DEFAULT_ADAPTER = ROOT / "config/f02_known_family_bundle_adapter.v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run an authorized offline reusable F02 known-family bundle."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Repository-relative runtime manifest path.",
    )
    parser.add_argument(
        "--authorization",
        required=True,
        help="Repository-relative runtime owner/orchestrator authorization JSON.",
    )
    parser.add_argument(
        "--authorization-sha256",
        required=True,
        help="Exact SHA-256 of the runtime authorization JSON bytes.",
    )
    args = parser.parse_args()

    manifest = load_runtime_manifest(root=ROOT, relative_path=args.manifest)
    authorization = load_pinned_runtime_authorization(
        root=ROOT,
        relative_path=args.authorization,
        expected_sha256=args.authorization_sha256,
    )
    result, telemetry = run_known_family_bundle(
        load_json(DEFAULT_ADAPTER),
        manifest,
        root=ROOT,
        authorization=authorization,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    if telemetry["remote_effects"] != 0 or telemetry["gold_authorized"]:
        raise RuntimeError("STOP_F02_KNOWN_BUNDLE_UNEXPECTED_EFFECT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
