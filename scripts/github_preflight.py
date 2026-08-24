#!/usr/bin/env python3
"""Fail-closed repository and OAuth preflight for the current release identity."""

from __future__ import annotations

import argparse
from importlib.metadata import version as package_version
import json
import os
import re
import sys
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.journal.gate import load_journal_processing_gate
from robo_dados_publicos.observability import SourceCard
from robo_dados_publicos.reconciliation.gate import load_reconciliation_execution_gate
from robo_dados_publicos.release import (
    ACTIVE_VALIDATED_VERSION,
    CURRENT_CANDIDATE_VERSION,
    NEXT_ACTION,
    RELEASE_STATUS,
    SOFTWARE_VERSION,
)
from robo_dados_publicos.sources.expansion import load_source_expansion_gate
from robo_dados_publicos.sources.inventory import load_source_inventory

WORKFLOW = ROOT / ".github" / "workflows" / "robo-dados-publicos.yml"
PRODUCT_PUBLICATION_WORKFLOW = ROOT / ".github" / "workflows" / "product-output-publication-gate.yml"
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
PRODUCT_BUILDER = ROOT / "scripts" / "build_product_output.py"
PRODUCT_CONTRACT = ROOT / "robo_dados_publicos" / "product" / "contracts.py"
PRODUCT_BUNDLE = ROOT / "robo_dados_publicos" / "product" / "bundle.py"
PRODUCT_PUBLICATION = ROOT / "robo_dados_publicos" / "product" / "publication.py"
PRODUCT_PUBLICATION_SCRIPT = ROOT / "scripts" / "github_product_publication_gate.py"
PRODUCT_PUBLICATION_CONFIG = ROOT / "config" / "product_output.first_publication_gate.json"
PRODUCT_PUBLICATION_ANSWERS = ROOT / "config" / "product_output.first_publication_answers.json"
SOURCE_EXPANSION_CONFIG = ROOT / "config" / "source_expansion.siope_limeira_0_8_0.json"
SOURCE_EXPANSION_SCRIPT = ROOT / "scripts" / "github_source_expansion_design_gate.py"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_preflight(require_oauth: bool = False) -> tuple[dict, int]:
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    workflow_active_lines = [line for line in workflow_text.splitlines() if not line.lstrip().startswith("#")]
    publication_text = PRODUCT_PUBLICATION_WORKFLOW.read_text(encoding="utf-8")
    publication_active_lines = [line for line in publication_text.splitlines() if not line.lstrip().startswith("#")]
    publication_script_text = PRODUCT_PUBLICATION_SCRIPT.read_text(encoding="utf-8")

    manifest = _load_json(ROOT / "release_manifest_v01.json")
    active_manifest = _load_json(ROOT / "release_manifest_v01_0.7.0_active.json")
    candidate_manifest = _load_json(ROOT / "release_manifest_v01_0.8.0.json")
    preserved_candidate = _load_json(ROOT / "release_manifest_v01_0.7.0.json")
    cloud_config = _load_json(ROOT / "config" / "cloud.json")
    publication_gate = _load_json(PRODUCT_PUBLICATION_CONFIG)
    expansion_gate = load_source_expansion_gate(SOURCE_EXPANSION_CONFIG)

    inventory = load_source_inventory(SOURCE_GATE_CONFIG)
    source = inventory.enabled[0] if len(inventory.enabled) == 1 else None
    processing_gate = load_journal_processing_gate(PROCESSING_GATE_CONFIG)
    reconciliation_gate = load_reconciliation_execution_gate(RECONCILIATION_GATE_CONFIG)
    source_card = SourceCard.from_mapping(_load_json(OBSERVABILITY_CONFIG)["source_card"])

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    product_builder_text = PRODUCT_BUILDER.read_text(encoding="utf-8")

    checks = {
        "software_version_0_8_0": SOFTWARE_VERSION == "0.8.0",
        "release_status_candidate": RELEASE_STATUS == "CANDIDATE",
        "active_version_0_7_0": ACTIVE_VALIDATED_VERSION == "0.7.0",
        "current_candidate_0_8_0": CURRENT_CANDIDATE_VERSION == "0.8.0",
        "next_action_siope_route_discovery": NEXT_ACTION == "M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0",
        "manifest_identity": (
            manifest.get("current_active") == "0.7.0"
            and manifest.get("current_candidate") == "0.8.0"
            and manifest.get("last_active_validated") == "0.7.0"
            and manifest.get("active_manifest") == "release_manifest_v01_0.7.0_active.json"
            and manifest.get("candidate_manifest") == "release_manifest_v01_0.8.0.json"
            and manifest.get("preserved_candidate_manifest") == "release_manifest_v01_0.7.0.json"
            and manifest.get("promotion_gate") == "PENDING_M7_OFFLINE_SOURCE_EXPANSION_DESIGN_VALIDATION"
            and manifest.get("next_action") == "M7_SIOPE_LIMEIRA_ROUTE_DISCOVERY_GATE_0_8_0"
        ),
        "active_manifest_identity": (
            active_manifest.get("version") == "0.7.0"
            and active_manifest.get("status") == "ACTIVE"
            and active_manifest.get("live_gate", {}).get("status") == "PASS_M6_PRODUCT_OUTPUT_PUBLICATION_GATE"
            and active_manifest.get("live_gate", {}).get("created_count") == 3
            and active_manifest.get("drive_evidence", {}).get("target") == "08_OUTPUTS"
        ),
        "candidate_manifest_identity": (
            candidate_manifest.get("version") == "0.8.0"
            and candidate_manifest.get("status") == "CANDIDATE"
            and candidate_manifest.get("based_on_active") == "0.7.0"
            and candidate_manifest.get("source_expansion", {}).get("system") == "SIOPE"
            and candidate_manifest.get("source_expansion", {}).get("current_state") == "CONTRACT_VALIDATED"
            and candidate_manifest.get("source_expansion", {}).get("collection_authorization") == "PROHIBITED"
        ),
        "previous_candidate_evidence_preserved": (
            preserved_candidate.get("version") == "0.7.0"
            and preserved_candidate.get("status") == "CANDIDATE"
        ),
        "source_expansion_config_present": SOURCE_EXPANSION_CONFIG.is_file(),
        "source_expansion_script_present": SOURCE_EXPANSION_SCRIPT.is_file(),
        "source_expansion_design_gate_identity": (
            expansion_gate.gate_id == "M7_CONTROLLED_SOURCE_EXPANSION_DESIGN_0_8_0"
            and expansion_gate.software_version == "0.8.0"
            and expansion_gate.release_status == "CANDIDATE"
            and expansion_gate.active_validated_version == "0.7.0"
            and expansion_gate.mode == "DESIGN_ONLY"
        ),
        "source_expansion_single_pilot_siope_limeira": (
            expansion_gate.source.source_id == "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA"
            and expansion_gate.source.institution == "FNDE"
            and expansion_gate.source.system == "SIOPE"
            and expansion_gate.source.pilot.municipality == "Limeira"
            and expansion_gate.source.pilot.state == "SP"
            and expansion_gate.source.pilot.municipality_code == "352690"
            and expansion_gate.source.pilot.year == 2024
        ),
        "source_expansion_stops_at_contract_validated": (
            expansion_gate.source.lifecycle_state == "CONTRACT_VALIDATED"
            and expansion_gate.source.acquisition_route_status == "UNPROVEN"
            and expansion_gate.source.schema_status == "UNPROVEN"
            and expansion_gate.source.content_type_status == "UNPROVEN"
            and not expansion_gate.source.can_collect
            and not expansion_gate.source.can_schedule
        ),
        "source_expansion_execution_prohibited": (
            expansion_gate.network == "PROHIBITED"
            and expansion_gate.remote_writes == "PROHIBITED"
            and expansion_gate.source_collection == "PROHIBITED"
            and expansion_gate.source_processing == "PROHIBITED"
            and expansion_gate.recurrence == "PROHIBITED"
            and expansion_gate.schedule == "DISABLED"
        ),
        "production_workflow_source_expansion_not_reachable": (
            "source_expansion.siope_limeira_0_8_0.json" not in workflow_text
            and "github_source_expansion_design_gate.py" not in workflow_text
            and "confirm_source_expansion" not in workflow_text
            and "dadosInformadosMunicipio" not in workflow_text
        ),
        "product_contract_present": PRODUCT_CONTRACT.is_file(),
        "product_bundle_present": PRODUCT_BUNDLE.is_file(),
        "product_builder_present": PRODUCT_BUILDER.is_file(),
        "product_builder_local_only": (
            "DriveRESTClient" not in product_builder_text
            and "_drive_client" not in product_builder_text
            and "drive.put(" not in product_builder_text
            and "drive.replace_content(" not in product_builder_text
        ),
        "product_publication_module_present": PRODUCT_PUBLICATION.is_file(),
        "product_publication_script_present": PRODUCT_PUBLICATION_SCRIPT.is_file(),
        "product_publication_answers_present": PRODUCT_PUBLICATION_ANSWERS.is_file(),
        "product_publication_gate_contract_preserved": (
            publication_gate.get("gate_id") == "M6_FIRST_PRODUCT_OUTPUT_PUBLICATION_GATE_0_7_0"
            and publication_gate.get("software_version") == "0.7.0"
            and publication_gate.get("release_status") == "CANDIDATE"
            and publication_gate.get("drive_target") == "08_OUTPUTS"
            and publication_gate.get("required_remote_count") == 3
            and publication_gate.get("allow_overwrite") is False
            and publication_gate.get("collision_policy") == "STOP_BEFORE_WRITES"
            and publication_gate.get("completion_manifest_written_last") is True
            and publication_gate.get("schedule") == "DISABLED"
        ),
        "product_publication_rerun_blocked_by_identity": (
            'SOFTWARE_VERSION == "0.7.0"' in publication_script_text
            and 'RELEASE_STATUS == "CANDIDATE"' in publication_script_text
            and 'CURRENT_CANDIDATE_VERSION == "0.7.0"' in publication_script_text
        ),
        "production_workflow_product_publication_not_reachable": (
            "build_product_output.py" not in workflow_text
            and "github_product_publication_gate.py" not in workflow_text
            and "confirm_product_publication" not in workflow_text
        ),
        "product_publication_workflow_manual": (
            bool(re.search(r"^  workflow_dispatch:\s*$", publication_text, re.MULTILINE))
            and "confirm_product_publication:" in publication_text
            and "inputs.confirm_product_publication == true" in publication_text
        ),
        "product_publication_workflow_schedule_disabled": not any(
            line.strip() == "schedule:" for line in publication_active_lines
        ),
        "product_publication_workflow_permissions_read": "permissions:\n  contents: read" in publication_text,
        "product_publication_workflow_pins": all(
            marker in publication_text for marker in (CHECKOUT_PIN, SETUP_PYTHON_PIN, UPLOAD_ARTIFACT_PIN)
        ),
        "product_publication_workflow_sanitized_artifact": (
            "publication-gate-evidence/result.json" in publication_text
            and "product-publication-gate-${{ github.run_id }}" in publication_text
        ),
        "outputs_drive_target_configured": bool(str(cloud_config.get("outputs_id", "")).strip()),
        "reportlab_dependency_pinned": (
            "reportlab==5.0.0" in requirements
            and "reportlab==5.0.0" in pyproject
            and package_version("reportlab") == "5.0.0"
        ),
        "source_inventory_one_enabled": source is not None,
        "source_inventory_immutable_contract": bool(
            source
            and source.source_id == SOURCE_GATE_ID
            and source.expected_sha256 == processing_gate.source_sha256
            and source.expected_bytes == processing_gate.source_bytes
            and source.expected_content_types == ("application/pdf",)
        ),
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
        "processing_dependency_pinned": "pypdf==6.10.0" in requirements and "pypdf==6.10.0" in pyproject,
        "reconciliation_gate_contract": (
            reconciliation_gate.allowed_targets == ("LIMEIRA_CONTRATOS",)
            and reconciliation_gate.limit == 1
            and reconciliation_gate.required_selected == 1
            and reconciliation_gate.initial_status == "READY_SEARCH"
            and reconciliation_gate.selection_policy == "ELIGIBLE_PRIORITY_DESC_TASK_ID_ASC"
            and set(reconciliation_gate.allowed_result_statuses) == {"MATCH_CANDIDATE", "NO_MATCH"}
            and reconciliation_gate.financial_identity_auto_promotion == "PROHIBITED"
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
        "workflow_manual_dispatch": bool(re.search(r"^  workflow_dispatch:\s*$", workflow_text, re.MULTILINE)),
        "workflow_schedule_disabled": not any(line.strip() == "schedule:" for line in workflow_active_lines),
        "workflow_confirmation_required": "inputs.confirm_persistence == true" in workflow_text,
        "workflow_reconciliation_rerun_disabled": "confirm_reconciliation:" not in workflow_text,
        "workflow_source_rerun_disabled": "confirm_source_collection:" not in workflow_text,
        "workflow_processing_rerun_disabled": "confirm_processing:" not in workflow_text,
        "workflow_historical_gates_not_reachable": (
            "scripts/github_reconciliation_gate.py" not in workflow_text
            and "scripts/github_processing_gate.py --processing-config config/processing.jornal_oficial_7310_gate.json" not in workflow_text
            and "--source-config config/sources.jornal_oficial_7310_gate.json" not in workflow_text
        ),
        "workflow_observability_report_enabled": (
            'github_run_gate.py > "$RUNNER_TEMP/run_gate_raw.json"' in workflow_text
            and "scripts/github_observability_report.py" in workflow_text
            and '--input "$RUNNER_TEMP/run_gate_raw.json"' in workflow_text
            and "--github-summary" in workflow_text
            and "path: observability-report/" in workflow_text
            and "PASS_ACTIVE_RUNTIME_OBSERVABILITY" in workflow_text
        ),
        "workflow_observability_raw_not_uploaded": (
            "path: $RUNNER_TEMP/run_gate_raw.json" not in workflow_text
            and "path: \"$RUNNER_TEMP/run_gate_raw.json\"" not in workflow_text
        ),
        "workflow_runtime_failure_propagated": (
            "steps.runtime_gate.outputs.exit_code" in workflow_text
            and "steps.observability.outcome" in workflow_text
        ),
        "permissions_contents_read": "permissions:\n  contents: read" in workflow_text,
        "checkout_immutable_pin": CHECKOUT_PIN in workflow_text,
        "setup_python_immutable_pin": SETUP_PYTHON_PIN in workflow_text,
        "upload_artifact_immutable_pin": UPLOAD_ARTIFACT_PIN in workflow_text,
        "checkout_credentials_not_persisted": "persist-credentials: false" in workflow_text,
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
    elif require_oauth and RELEASE_STATUS == "CANDIDATE":
        status, code = "STOP_CANDIDATE_PERSISTENT_RUNTIME_NOT_AUTHORIZED", 14
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
