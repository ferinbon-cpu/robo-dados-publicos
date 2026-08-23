#!/usr/bin/env python3
"""Fail-closed repository and OAuth preflight for M4D."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

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


WORKFLOW = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"
CHECKOUT_PIN = "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
SETUP_PYTHON_PIN = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
OAUTH_NAMES = (
    "GOOGLE_DRIVE_CLIENT_ID",
    "GOOGLE_DRIVE_CLIENT_SECRET",
    "GOOGLE_DRIVE_REFRESH_TOKEN",
)


def run_preflight(require_oauth: bool = False) -> tuple[dict, int]:
    text = WORKFLOW.read_text(encoding="utf-8")
    active_lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    manifest = json.loads((ROOT / "release_manifest_v01.json").read_text(encoding="utf-8"))
    checks = {
        "software_version_0_5_9": SOFTWARE_VERSION == "0.5.9",
        "release_status_candidate": RELEASE_STATUS == "CANDIDATE",
        "active_version_preserved_0_5_8": ACTIVE_VALIDATED_VERSION == "0.5.8",
        "current_candidate_0_5_9": CURRENT_CANDIDATE_VERSION == "0.5.9",
        "next_action_live_gate": NEXT_ACTION == "M4D_GITHUB_LIVE_GATE_0_5_9",
        "manifest_identity": manifest.get("current_active") == "0.5.8" and manifest.get("current_candidate") == "0.5.9",
        "workflow_manual_dispatch": bool(re.search(r"^  workflow_dispatch:\s*$", text, re.MULTILINE)),
        "workflow_schedule_disabled": not any(line.strip() == "schedule:" for line in active_lines),
        "workflow_confirmation_required": "inputs.confirm_persistence == true" in text,
        "permissions_contents_read": "permissions:\n  contents: read" in text,
        "checkout_immutable_pin": CHECKOUT_PIN in text,
        "setup_python_immutable_pin": SETUP_PYTHON_PIN in text,
        "checkout_credentials_not_persisted": "persist-credentials: false" in text,
        "gitignore_protects_oauth": all(
            marker in (ROOT / ".gitignore").read_text(encoding="utf-8")
            for marker in ("tokens.json", "client_secret*.json", ".env")
        ),
    }
    failed = sorted(name for name, ok in checks.items() if not ok)
    missing = [name for name in OAUTH_NAMES if not os.getenv(name, "").strip()] if require_oauth else []
    if failed:
        status, code = "STOP_GITHUB_PREFLIGHT", 2
    elif missing:
        status, code = "STOP_MISSING_GITHUB_SECRETS", 3
    else:
        status, code = ("PASS_LIVE_PREFLIGHT" if require_oauth else "PASS_OFFLINE"), 0
    return {
        "status": status,
        "software_version": SOFTWARE_VERSION,
        "active_version": ACTIVE_VALIDATED_VERSION,
        "current_candidate": CURRENT_CANDIDATE_VERSION,
        "checks": checks,
        "failed_checks": failed,
        "missing_oauth_secrets": missing,
        "secret_values_exposed": False,
    }, code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-oauth", action="store_true")
    args = parser.parse_args()
    payload, code = run_preflight(require_oauth=args.require_oauth)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
