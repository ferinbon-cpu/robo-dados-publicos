#!/usr/bin/env python3
"""Fail-closed repository and OAuth preflight for the current release identity."""

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
from robo_dados_publicos.reconciliation.gate import load_reconciliation_execution_gate
from robo_dados_publicos.observability import SourceCard


WORKFLOW = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"
CHECKOUT_PIN = "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
SETUP_PYTHON_PIN = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
UPLOAD_ARTIFACT_PIN = "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
OAUTH_NAMES = (
    "GOOGLE_DRIVE_CLIENT_ID",
    "GOOGLE_DRIVE_CLIENT_SECRET",
    "GOOGLE_DRIVE_REFRESH_TOKEN",
)
SOURCE_GATE_CONFIG = ROOT / "config" / "sources.jornal_oficial_7310_gate.json"
SOURCE_GATE_ID = "LIMEIRA_JORNAL_OFICIAL_EDICAO_7310"
PROCESSING_GATE_CONFIG = ROOT / "config" / "processing.jornal_oficial_7310_gate.json"
RECONCILIATION_GATE_CONFIG = ROOT / "config" / "reconciliation.first_contract_gate.json"
OBSERVABILITY_CONFIG = ROOT / "config" / "observability.jornal_oficial_7310.json"
OBSERVABILITY_SCRIPT = ROOT / "scripts" / "github_observability_report.py"


def run_preflight(require_oauth: bool = False) -> tuple[dict, int]:
    text = WORKFLOW.read_text(encoding="utf-8")
    active_lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]
    manifest = json.loads((ROOT / "release_manifest_v01.json").read_text(encoding="utf-8"))
    inventory = load_source_inventory(SOURCE_GATE_CONFIG)
    source = inventory.enabled[0] if len(inventory.enabled) == 1 else None
    processing_gate = load_journal_processing_gate(PROCESSING_GATE_CONFIG)
    reconciliation_gate = load_reconciliation_execution_gate(RECONCILIATION_GATE_CONFIG)
    observability_payload = json.loads(OBSERVABILITY_CONFIG.read_text(encoding="utf-8"))
    source_card = SourceCard.from_mapping(observability_payload["source_card"])

    checks = {
        "software_version_0_6_3": SOFTWARE_VERSION == "0.6.3",
        "release_status_candidate": RELEASE_STATUS == "CANDIDATE",
        "active_version_0_6_2": ACTIVE_VALIDATED_VERSION == "0.6.2",
        "current_candidate_0_6_3": CURRENT_CANDIDATE_VERSION == "0.6.3",
        "next_action_observability_runtime_gate": NEXT_ACTION == "M5_OBSERVABILITY_RUNTIME_REPORT_GATE_0_6_3",
        "manifest_identity": (
            manifest.get("current_active") == "0.6.2"
            and manifest.get("current_candidate") == "0.6.3"
            and manifest.get("active_manifest") == "release_manifest_v01_0.6.2_active.json"
            and manifest.get("candidate_manifest") == "release_manifest_v01_0.6.3.json"
            and manifest.get("preserved_candidate_manifest") == "release_manifest_v01_0.6.2.json"
        ),
        "source_inventory_one_enabled": source is not None,
        "source_inventory_immutable_contract": bool(
            source
            and source.source_id == SOURCE_GATE_ID
            and source.expected_sha256 == processing_gate.source_sha256
            and source.expected_bytes == processing_gate.source_bytes
            and source.expected_content_types == ("application/pdf",)
        ),
        "observability_source_card_contract": bool(
            source
            and source_card.source_id == source.source_id
            and source_card.source_url == source.url
            and source_card.formats == source.expected_content_types
            and source_card.periodicity == source.cadence
            and source_card.expected_update_interval_hours is None
        ),
        "observability_report_script_present": OBSERVABILITY_SCRIPT.is_file(),
        "workflow_manual_dispatch": bool(re.search(r"^  workflow_dispatch:\s*$", text, re.MULTILINE)),
        "workflow_schedule_disabled": not any(line.strip() == "schedule:" for line in active_lines),
        "workflow_confirmation_required": "inputs.confirm_persistence == true" in text,
        "workflow_reconciliation_rerun_disabled": "confirm_reconciliation:" not in text,
        "workflow_source_rerun_disabled": "confirm_source_collection:" not in text,
        "workflow_source_gate_not_reachable": "--source-config config/sources.jornal_oficial_7310_gate.json" not in text,
        "processing_gate_contract": (
            processing_gate.source_id == SOURCE_GATE_ID
            and source is not None
            and processing_gate.source_sha256 == source.expected_sha256
            and processing_gate.source_bytes == source.expected_bytes
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
        "workflow_processing_rerun_disabled": "confirm_processing:" not in text,
        "workflow_processing_gate_not_reachable": "scripts/github_processing_gate.py --processing-config config/processing.jornal_oficial_7310_gate.json" not in text,
        "reconciliation_gate_contract": (
            reconciliation_gate.allowed_targets == ("LIMEIRA_CONTRATOS",)
            and reconciliation_gate.limit == 1
            and reconciliation_gate.required_selected == 1
            and reconciliation_gate.initial_status == "READY_SEARCH"
            and reconciliation_gate.selection_policy == "ELIGIBLE_PRIORITY_DESC_TASK_ID_ASC"
            and set(reconciliation_gate.allowed_result_statuses) == {"MATCH_CANDIDATE", "NO_MATCH"}
            and reconciliation_gate.financial_identity_auto_promotion == "PROHIBITED"
        ),
        "workflow_reconciliation_gate_not_reachable": "scripts/github_reconciliation_gate.py" not in text,
        "workflow_observability_report_enabled": (
            'github_run_gate.py > "$RUNNER_TEMP/run_gate_raw.json"' in text
            and "scripts/github_observability_report.py" in text
            and '--input "$RUNNER_TEMP/run_gate_raw.json"' in text
            and "--github-summary" in text
            and "path: observability-report/" in text
            and "PASS_M5_OBSERVABILITY_RUNTIME_GATE" in text
        ),
        "workflow_observability_raw_not_uploaded": (
            "path: $RUNNER_TEMP/run_gate_raw.json" not in text
            and "path: \"$RUNNER_TEMP/run_gate_raw.json\"" not in text
        ),
        "workflow_runtime_failure_propagated": (
            "steps.runtime_gate.outputs.exit_code" in text
            and "steps.observability.outcome" in text
        ),
        "permissions_contents_read": "permissions:\n  contents: read" in text,
        "checkout_immutable_pin": CHECKOUT_PIN in text,
        "setup_python_immutable_pin": SETUP_PYTHON_PIN in text,
        "upload_artifact_immutable_pin": UPLOAD_ARTIFACT_PIN in text,
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
