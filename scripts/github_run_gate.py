#!/usr/bin/env python3
"""Run the persistent command once and enforce every current-runtime criterion."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.qa.github_gate import evaluate_live_payload
from robo_dados_publicos.release import RELEASE_STATUS, SOFTWARE_VERSION
from robo_dados_publicos.sources.inventory import load_source_inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-config")
    args = parser.parse_args()
    command = [sys.executable, "main.py", "run", "--auth", "oauth-env"]
    source_expectation = None
    if args.source_config:
        inventory = load_source_inventory(ROOT / args.source_config)
        if len(inventory.enabled) != 1:
            print(json.dumps({"status": "STOP_SOURCE_GATE_INVENTORY_COUNT"}, indent=2))
            return 8
        source = inventory.enabled[0]
        if not source.expected_sha256 or source.expected_bytes is None or not source.expected_content_types:
            print(json.dumps({"status": "STOP_SOURCE_GATE_IMMUTABLE_CONTRACT_REQUIRED"}, indent=2))
            return 8
        source_expectation = {
            "source_id": source.source_id,
            "expected_sha256": source.expected_sha256,
            "expected_bytes": source.expected_bytes,
            "expected_content_types": source.expected_content_types,
        }
        command.extend(["--source-config", args.source_config])

    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        print(proc.stdout, end="")
        print(proc.stderr, file=sys.stderr, end="")
        return proc.returncode
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "STOP_INVALID_RUNTIME_JSON", "error": str(exc)}, indent=2))
        return 6

    gate = evaluate_live_payload(
        payload,
        source_expectation=source_expectation,
        expected_version=SOFTWARE_VERSION,
        expected_status=RELEASE_STATUS,
    )
    evidence = {
        **gate,
        "software_version": payload.get("software_version"),
        "release_status": payload.get("release_status"),
        "run_id": payload.get("run_id"),
        "started_at": payload.get("started_at"),
        "finished_at": payload.get("finished_at"),
        "state_source": payload.get("state_source"),
        "state_remote_mode": (payload.get("state_remote") or {}).get("mode"),
        "append_only_log_created": bool((payload.get("log_remote") or {}).get("id")),
        "remote_identifiers_exposed": False,
        "source_collection": payload.get("source_collection"),
        "secret_values_exposed": False,
    }
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if gate["status"].startswith("PASS_GITHUB_") else 7


if __name__ == "__main__":
    raise SystemExit(main())
