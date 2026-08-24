#!/usr/bin/env python3
"""Run the first Bronze processing gate and enforce every fail-closed criterion."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.journal.gate import load_journal_processing_gate
from robo_dados_publicos.release import RELEASE_STATUS, SOFTWARE_VERSION


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processing-config", required=True)
    args = parser.parse_args()
    gate = load_journal_processing_gate(ROOT / args.processing_config)
    proc = subprocess.run(
        [
            sys.executable,
            "main.py",
            "journal-process-cloud",
            "--auth",
            "oauth-env",
            "--processing-config",
            args.processing_config,
        ],
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
        print(json.dumps({"status": "STOP_INVALID_PROCESSING_RUNTIME_JSON", "error": str(exc)}, indent=2))
        return 11

    outputs = payload.get("outputs") or []
    checks = {
        "runtime_status_pass": payload.get("status") == "PASS_CLOUD_JOURNAL_PROCESSING_GATE",
        "software_version_match": payload.get("software_version") == SOFTWARE_VERSION,
        "release_status_match": payload.get("release_status") == RELEASE_STATUS,
        "source_checks_pass": bool(payload.get("source_checks")) and all(payload["source_checks"].values()),
        "extractor_checks_pass": bool(payload.get("extractor_checks")) and all(payload["extractor_checks"].values()),
        "artifact_checks_pass": bool(payload.get("artifact_checks")) and all(payload["artifact_checks"].values()),
        "processing_checks_pass": bool(payload.get("processing_checks")) and all(payload["processing_checks"].values()),
        "metrics_match": payload.get("metrics") == gate.expected_metrics(),
        "five_outputs_committed": len(outputs) == 5 and all(x.get("mode") in {"CREATED", "REUSED_IDENTICAL"} for x in outputs),
        "output_identifiers_hidden": bool(outputs) and all(x.get("remote_identifier_exposed") is False for x in outputs),
        "tasks_persisted": payload.get("reconciliation_tasks_persisted") == gate.expected_reconciliation_tasks,
        "origin_network_not_called": payload.get("origin_network_called") is False,
        "state_remote_replaced": (payload.get("state_remote") or {}).get("mode") == "REPLACED",
        "append_only_log_created": (payload.get("append_only_log") or {}).get("created") is True,
        "remote_identifiers_hidden": payload.get("remote_identifiers_exposed") is False,
        "secret_values_hidden": payload.get("secret_values_exposed") is False,
    }
    result = {
        "status": "PASS_GITHUB_JOURNAL_PROCESSING_GATE" if all(checks.values()) else "STOP_GITHUB_JOURNAL_PROCESSING_GATE",
        "checks": checks,
        "software_version": payload.get("software_version"),
        "release_status": payload.get("release_status"),
        "metrics": payload.get("metrics"),
        "outputs": outputs,
        "state_remote_mode": (payload.get("state_remote") or {}).get("mode"),
        "append_only_log_created": (payload.get("append_only_log") or {}).get("created") is True,
        "origin_network_called": False,
        "remote_identifiers_exposed": False,
        "secret_values_exposed": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"].startswith("PASS_GITHUB_") else 12


if __name__ == "__main__":
    raise SystemExit(main())
