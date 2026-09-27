#!/usr/bin/env python3
"""Run the first reconciliation gate and expose only sanitized evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.reconciliation.gate import load_reconciliation_execution_gate
from robo_dados_publicos.release import RELEASE_STATUS, SOFTWARE_VERSION


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reconciliation-config", required=True)
    args = parser.parse_args()
    gate = load_reconciliation_execution_gate(ROOT / args.reconciliation_config)
    proc = subprocess.run(
        [
            sys.executable,
            "main.py",
            "reconciliation-execute-cloud",
            "--auth",
            "oauth-env",
            "--reconciliation-config",
            args.reconciliation_config,
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
        print(json.dumps({"status": "STOP_INVALID_RECONCILIATION_RUNTIME_JSON", "error": str(exc)}, indent=2))
        return 14
    checks = {
        "runtime_status_pass": payload.get("status") == "PASS_CLOUD_RECONCILIATION_EXECUTION_GATE",
        "software_version_match": payload.get("software_version") == SOFTWARE_VERSION,
        "release_status_match": payload.get("release_status") == RELEASE_STATUS,
        "selection_checks_pass": bool(payload.get("selection_checks")) and all(payload["selection_checks"].values()),
        "execution_checks_pass": bool(payload.get("execution_checks")) and all(payload["execution_checks"].values()),
        "one_task_selected": payload.get("selected") == gate.required_selected,
        "one_allowlisted_target": payload.get("allowed_targets") == list(gate.allowed_targets),
        "financial_identity_edges_zero": payload.get("financial_identity_edges") == 0,
        "source_origin_network_not_called": payload.get("source_origin_network_called") is False,
        "state_remote_replaced": (payload.get("state_remote") or {}).get("mode") == "REPLACED",
        "append_only_log_created": (payload.get("append_only_log") or {}).get("created") is True,
        "task_identifiers_hidden": payload.get("task_identifiers_exposed") is False,
        "candidate_payloads_hidden": payload.get("candidate_payloads_exposed") is False,
        "remote_identifiers_hidden": payload.get("remote_identifiers_exposed") is False,
        "secret_values_hidden": payload.get("secret_values_exposed") is False,
    }
    result = {
        "status": "PASS_GITHUB_RECONCILIATION_EXECUTION_GATE" if all(checks.values()) else "STOP_GITHUB_RECONCILIATION_EXECUTION_GATE",
        "checks": checks,
        "software_version": payload.get("software_version"),
        "release_status": payload.get("release_status"),
        "selected": payload.get("selected"),
        "allowed_targets": payload.get("allowed_targets"),
        "result_status_counts": payload.get("result_status_counts"),
        "candidate_evidence_edges": payload.get("candidate_evidence_edges"),
        "financial_identity_edges": 0,
        "state_remote_mode": (payload.get("state_remote") or {}).get("mode"),
        "append_only_log_created": (payload.get("append_only_log") or {}).get("created") is True,
        "task_identifiers_exposed": False,
        "candidate_payloads_exposed": False,
        "remote_identifiers_exposed": False,
        "secret_values_exposed": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"].startswith("PASS_GITHUB_") else 15


if __name__ == "__main__":
    raise SystemExit(main())
