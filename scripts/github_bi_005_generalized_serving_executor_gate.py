#!/usr/bin/env python3
"""Offline fail-closed gate for BI-005 final serving integration."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.analytics.bi_serving_executor_multi import (  # noqa: E402
    PASS,
    load_executor_contract,
)


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    contract = load_executor_contract()
    evidence = load("docs/evidence/BI_005_FINAL_SERVING_INTEGRATION_0.8.0.json")
    reference = load(
        "docs/evidence/BI_002_T2_MATERIALIZATION_SANITIZED_REFERENCE_0.8.0.json"
    )
    bi004 = load("config/bi/serving_executor.v1.json")
    source = (
        ROOT / "robo_dados_publicos/analytics/bi_serving_executor_multi.py"
    ).read_text(encoding="utf-8").lower()
    entry_test = (
        ROOT / "tests/test_bi_005_gate_entrypoint.py"
    ).read_text(encoding="utf-8")
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")

    reference_pins = {
        item["dataset_id"]: {
            "serving_name": f"{item['dataset_id']}__SERVING",
            "row_count": item["row_count"],
            "snapshot_id": item["snapshot_id"],
            "canonical_matrix_sha256": item["canonical_matrix_sha256"],
            "schema_fingerprint_sha256": item["schema_fingerprint_sha256"],
        }
        for item in reference["snapshots"]
    }
    limits = contract["limits"]
    history = evidence["bi_004_historical_live_reference"]

    checks = {
        "base_exact": contract["base_main_sha"]
        == evidence["base_main_sha"]
        == "396ef26cdb38f79be3c2512329bc9e848774d6f9",
        "tier_t0": contract["tier"]
        == evidence["tier"]
        == "T0_OFFLINE_IMPLEMENTATION_REVIEW",
        "status_exact": contract["status"] == evidence["status"] == PASS,
        "six_exact_pins": contract["dataset_pins"] == reference_pins
        and len(contract["dataset_allowlist"]) == 6,
        "one_dataset_per_execution": contract["one_dataset_per_execution"] is True
        and evidence["one_dataset_per_execution"] is True,
        "operations_bounded": contract["future_live_operation_allowlist"]
        == evidence["future_live_operation_allowlist"]
        == ["CREATE_INITIAL_SERVING", "NO_CHANGE_IDEMPOTENT"],
        "zero_active_authorization": contract["active_authorization"] is None
        and evidence["active_t3_authorization_embedded"] is False
        and evidence["remote_execution_authorized"] is False,
        "budgets_one": all(
            limits[key] == 1
            for key in (
                "discovery_read_count",
                "spreadsheet_create_count_max",
                "logical_batch_update_count_max",
                "semantic_readback_count_max",
                "manifest_create_count_max",
            )
        ),
        "budgets_zero": all(
            limits[key] == 0
            for key in (
                "retry_count",
                "delete_count",
                "cleanup_count",
                "looker_publication_count",
            )
        ),
        "zero_remote_effects": all(
            evidence[key] == 0
            for key in (
                "source_network",
                "drive_reads",
                "drive_writes",
                "sheets_api_calls",
                "looker_api_calls",
                "publication",
                "serving_files_created",
                "serving_files_modified",
                "remote_manifests_created",
                "retry_count",
                "delete_count",
                "cleanup_count",
            )
        ),
        "offline_module": all(
            term not in source
            for term in (
                "googleapiclient",
                "requests",
                "httplib",
                "socket",
                "lookerstudio",
            )
        ),
        "bi004_contract_preserved": bi004["task"] == "BI_004"
        and bi004["remote_execution_authorized"] is False,
        "bi004_live_reference_consumed": history["semantic_readback_verified"] is True
        and history["authorization_consumed"] is True
        and history["remote_file_ids_included"] is False,
        "prior_authorizations_not_reusable": evidence["prior_authorizations_reusable"]
        is False,
        "no_replace_retry_cleanup_looker": all(
            evidence[key] is False
            for key in (
                "replace_existing_authorized",
                "retry_authorized",
                "cleanup_authorized",
                "looker_publication_authorized",
                "multi_dataset_mutation_authorized",
            )
        ),
        "gate_runs_in_ci_via_unittest": "github_bi_005_generalized_serving_executor_gate.py"
        in entry_test
        and "python -m unittest discover -s tests -v" in ci,
        "engineering_closure_declared": evidence["serving_layer_engineering_phase"]
        == "CLOSED_FOR_CURRENT_SIX_DATASETS_AFTER_MERGE",
    }
    failed = [name for name, passed in checks.items() if not passed]
    status = PASS if not failed else "STOP_BI_005_GATE"
    print(
        json.dumps(
            {"status": status, "checks": checks, "failed_checks": failed},
            sort_keys=True,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
