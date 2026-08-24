#!/usr/bin/env python3
"""Run the persistent command once and enforce every active-runtime criterion."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.qa.github_gate import evaluate_live_payload

def main() -> int:
    proc = subprocess.run(
        [sys.executable, "main.py", "run", "--auth", "oauth-env"],
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
    gate = evaluate_live_payload(payload)
    evidence = {
        **gate,
        "software_version": payload.get("software_version"),
        "release_status": payload.get("release_status"),
        "state_source": payload.get("state_source"),
        "state_remote_mode": (payload.get("state_remote") or {}).get("mode"),
        "log_remote": payload.get("log_remote"),
        "secret_values_exposed": False,
    }
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if gate["status"] == "PASS_GITHUB_LIVE_GATE" else 7


if __name__ == "__main__":
    raise SystemExit(main())
