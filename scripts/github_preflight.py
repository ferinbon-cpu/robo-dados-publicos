#!/usr/bin/env python3
"""Fail-closed repository and OAuth preflight for the active runtime."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
import pypdf

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
from robo_dados_publicos.sources.inventory import load_source_inventory
from robo_dados_publicos.journal.gate import load_journal_processing_gate


WORKFLOW = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"
CHECKOUT_PIN = "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
SETUP_PYTHON_PIN = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
OAUTH_NAMES = (
    "GOOGLE_DRIVE_CLIENT_ID",
    "GOOGLE_DRIVE_CLIENT_SECRET",
    "GOOGLE_DRIVE_REFRESH_TOKEN",
)
SOURCE_GATE_CONFIG = ROOT / "config" / "sources.jornal_oficial_7310_gate.json"
SOURCE_GATE_ID = "LIMEIRA_JORNAL_OFICIAL_EDICAO_7310"
SOURCE_GATE_SHA256 = "78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680"
SOURCE_GATE_BYTES = 16952899
PROCESSING_GATE_CONFIG = ROOT / "config" / "processing.jornal_oficial_7310_gate.json"


def run_preflight(require_oauth: bool = False) -> tuple[dict, int]:
    text = WORKFLOW.read_text(encoding="utf-8")
    active_lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    manifest = json.loads((ROOT / "release_manifest_v01.json").read_text(encoding="utf-8"))
    inventory = load_source_inventory(SOURCE_GATE_CONFIG)
    source = inventory.enabled[0] if len(inventory.enabled) == 1 else None
    processing_gate = load_journal_processing_gate(PROCESSING_GATE_CONFIG)
    checks = {
        "software_version_0_6_1": SOFTWARE_VERSION == "0.6.1",
        "release_status_candidate": RELEASE_STATUS == "CANDIDATE",
        "active_version_preserved_0_6_0": ACTIVE_VALIDATED_VERSION == "0.6.0",
        "current_candidate_0_6_1": CURRENT_CANDIDATE_VERSION == "0.6.1",
        "next_action_source_processing_live_gate": NEXT_ACTION == "M4E_FIRST_SOURCE_PROCESSING_LIVE_GATE_0_6_1",
        "manifest_identity": manifest.get("current_active") == "0.6.0" and manifest.get("current_candidate") == "0.6.1",
        "source_inventory_one_enabled": source is not None,
        "source_inventory_immutable_contract": bool(
            source
            and source.source_id == SOURCE_GATE_ID
            and source.expected_sha256 == SOURCE_GATE_SHA256
            and source.expected_bytes == SOURCE_GATE_BYTES
            and source.expected_content_types == ("application/pdf",)
        ),
        "workflow_manual_dispatch": bool(re.search(r"^  workflow_dispatch:\s*$", text, re.MULTILINE)),
        "workflow_schedule_disabled": not any(line.strip() == "schedule:" for line in active_lines),
        "workflow_confirmation_required": "inputs.confirm_persistence == true" in text,
        "workflow_source_rerun_disabled": "confirm_source_collection:" not in text,
        "workflow_source_gate_not_reachable": "--source-config config/sources.jornal_oficial_7310_gate.json" not in text,
        "processing_gate_contract": (
            processing_gate.source_id == SOURCE_GATE_ID
            and processing_gate.source_sha256 == SOURCE_GATE_SHA256
            and processing_gate.source_bytes == SOURCE_GATE_BYTES
            and processing_gate.extractor == "pypdf"
            and processing_gate.extractor_version == "6.10.0"
            and pypdf.__version__ == processing_gate.extractor_version
            and processing_gate.expected_metrics() == {
                "pages": 76,
                "total_extracted_chars": 195540,
                "gold_events": 53,
                "rag_chunks": 148,
                "reconciliation_tasks": 68,
            }
        ),
        "processing_dependency_pinned": (
            "pypdf==6.10.0" in (ROOT / "requirements.txt").read_text(encoding="utf-8")
            and "pypdf==6.10.0" in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        ),
        "workflow_processing_confirmation_required": "confirm_processing:" in text and "inputs.confirm_processing == true" in text,
        "workflow_processing_gate_explicit": "scripts/github_processing_gate.py --processing-config config/processing.jornal_oficial_7310_gate.json" in text,
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
