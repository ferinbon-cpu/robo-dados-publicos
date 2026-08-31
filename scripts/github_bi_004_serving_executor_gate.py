"""Offline BI-004 bounded first-serving executor gate."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.analytics.bi_serving_executor import (
    PASS,
    load_executor_contract,
)

REFERENCE_PATH = (
    ROOT
    / "docs/evidence/BI_002_T2_MATERIALIZATION_SANITIZED_REFERENCE_0.8.0.json"
)
EVIDENCE_PATH = ROOT / "docs/evidence/BI_004_BOUNDED_FIRST_SERVING_EXECUTOR_0.8.0.json"
SOURCE_PATH = ROOT / "robo_dados_publicos/analytics/bi_serving_executor.py"


def stop(condition: bool, code: str) -> None:
    if not condition:
        raise SystemExit(f"STOP_BI_004_GATE_{code}")


def main() -> None:
    contract = load_executor_contract()
    reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    siope = next(
        (
            item
            for item in reference.get("snapshots", [])
            if item.get("dataset_id") == "BI_SIOPE_SERIES"
        ),
        None,
    )
    stop(isinstance(siope, dict), "SIOPE_REFERENCE_MISSING")
    expected_pin = {
        "snapshot_id": siope["snapshot_id"],
        "canonical_matrix_sha256": siope["canonical_matrix_sha256"],
        "schema_fingerprint_sha256": siope["schema_fingerprint_sha256"],
        "row_count": siope["row_count"],
    }
    stop(contract["selected_snapshot"] == expected_pin, "SNAPSHOT_PIN")
    stop(reference.get("final_readback_verified") is True, "SOURCE_READBACK")
    stop(reference.get("serving_expected_empty") is True, "SERVING_BASELINE")
    stop(reference.get("prior_t2_authorization_consumed") is True, "T2_CONSUMED")
    stop(
        reference.get("prior_cleanup_t3_authorization_consumed") is True,
        "CLEANUP_T3_CONSUMED",
    )

    stop(contract["selected_dataset"] == "BI_SIOPE_SERIES", "DATASET")
    stop(contract["serving_name"] == "BI_SIOPE_SERIES__SERVING", "TITLE")
    stop(contract["tabs"] == ["DATA", "META"], "TABS")
    stop(
        contract["first_live_operation_allowlist"]
        == ["CREATE_INITIAL_SERVING", "NO_CHANGE_IDEMPOTENT"],
        "OPERATIONS",
    )
    stop(contract["replace_existing_authorized_first_live"] is False, "REPLACE")
    stop(contract["remote_execution_authorized"] is False, "REMOTE")
    stop(contract["active_authorization"] is None, "AUTHORIZATION")
    stop(contract["looker_publication_authorized"] is False, "LOOKER")
    stop(contract["retry_authorized"] is False, "RETRY")
    stop(contract["cleanup_authorized"] is False, "CLEANUP")
    stop(
        contract["limits"]
        == {
            "discovery_read_count": 1,
            "spreadsheet_create_count_max": 1,
            "logical_batch_update_count_max": 1,
            "semantic_readback_count_max": 1,
            "manifest_create_count_max": 1,
            "retry_count": 0,
            "delete_count": 0,
            "cleanup_count": 0,
            "looker_publication_count": 0,
        },
        "LIMITS",
    )

    source = SOURCE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "googleapiclient",
        "gspread",
        "requests",
        "socket",
        "drive_service",
        "service_account",
    ):
        stop(forbidden not in source, f"REMOTE_CLIENT_{forbidden.upper()}")

    stop(evidence.get("status") == PASS, "EVIDENCE_STATUS")
    stop(evidence.get("base_main_sha") == "5b177c162a143e9265cec7492ab49cefda89c789", "BASE_SHA")
    stop(evidence.get("selected_snapshot") == expected_pin, "EVIDENCE_PIN")
    stop(evidence.get("live_execution_performed") is False, "LIVE_EFFECT")
    stop(evidence.get("active_t3_authorization_embedded") is False, "T3_EMBEDDED")
    stop(evidence.get("looker_publication") is False, "EVIDENCE_LOOKER")
    stop(evidence.get("retry_count") == 0, "EVIDENCE_RETRY")
    stop(evidence.get("delete_count") == 0, "EVIDENCE_DELETE")
    stop(evidence.get("cleanup_count") == 0, "EVIDENCE_CLEANUP")

    print(PASS)


if __name__ == "__main__":
    main()
