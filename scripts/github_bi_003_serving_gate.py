#!/usr/bin/env python3
"""Fail-closed offline repository gate for BI-003."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from robo_dados_publicos.analytics.bi_materialization import load_policy as load_materialization_policy
from robo_dados_publicos.analytics.bi_serving import (
    build_target,
    load_serving_contract,
    serialize_target,
)


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    policy = load_serving_contract()
    materialization_policy = load_materialization_policy()
    evidence = load("docs/evidence/BI_003_STABLE_SERVING_LAYER_0.8.0.json")
    reference = load("docs/evidence/BI_002_T2_MATERIALIZATION_SANITIZED_REFERENCE_0.8.0.json")
    fixture = load("tests/fixtures/bi_003_serving_scenarios.json")
    ci = (ROOT / ".github/workflows/ci-offline.yml").read_text(encoding="utf-8")
    serving_source = (ROOT / "robo_dados_publicos/analytics/bi_serving.py").read_text(encoding="utf-8").lower()
    materialization_source = (
        ROOT / "robo_dados_publicos/analytics/bi_materialization.py"
    ).read_text(encoding="utf-8").lower()

    expected = {
        "BI_SIOPE_SERIES",
        "BI_JORNAL_EVENTOS",
        "BI_RECONCILIACAO",
        "BI_FONTES_STATUS",
        "BI_EXECUCOES_ROBO",
        "BI_DICIONARIO",
    }
    targets = {
        dataset_id: build_target(dataset_id, rows)
        for dataset_id, rows in fixture["rows"].items()
    }
    reference_by_dataset = {
        item["dataset_id"]: item for item in reference["snapshots"]
    }

    auth_contract = materialization_policy.get("authorization_contract", {})
    checks = {
        "base_expected": evidence["base_sha"] == "602e4e98f2d8abf079064595fa5bffa6a01dd469",
        "t0_offline": policy["tier"] == evidence["tier"] == "T0_OFFLINE_IMPLEMENTATION_REVIEW",
        "option_3": policy["architecture"] == "OPTION_3_CREATE_ONLY_SNAPSHOTS_PLUS_STABLE_SERVING_SHEET",
        "bi002_hardening_preserved": (
            materialization_policy["task"] == "BI_002"
            and auth_contract.get("required") is True
            and auth_contract.get("active_authorization_embedded") is False
            and "schema_fingerprint_sha256" in materialization_source
            and "validate_t2_authorization" in materialization_source
        ),
        "real_reference": (
            reference["snapshot_count"] == reference["manifest_count"] == 6
            and reference["total_rows"] == 520
            and sum(item["row_count"] for item in reference["snapshots"]) == 520
            and reference["final_readback_verified"] is True
        ),
        "closure_pinned": (
            reference["closure_sha256"]
            == evidence["materialization_closure_sha256"]
            == "7907b225b0b7f806034aaae5c15e78be391af0b5e7149c8a869297772217d6f8"
        ),
        "serving_empty_checkpoint": (
            reference["serving_expected_empty"]
            is evidence["serving_expected_empty_at_checkpoint"]
            is True
        ),
        "six_serving_definitions": (
            set(policy["dataset_allowlist"]) == expected == set(targets)
            and len(policy["serving_names"]) == 6
        ),
        "real_schema_fingerprints_match": (
            set(reference_by_dataset) == expected
            and all(
                targets[dataset_id].schema_fingerprint_sha256
                == reference_by_dataset[dataset_id]["schema_fingerprint_sha256"]
                for dataset_id in expected
            )
        ),
        "typed_raw_payloads": all(
            serialize_target(target)["value_input_option"] == "RAW"
            for target in targets.values()
        ),
        "t3_future_only": (
            policy["serving_tier"] == "T3_MUTATING_OR_PUBLICATION"
            and policy["remote_execution_authorized"] is False
        ),
        "no_active_authorization": (
            policy["active_authorization"] is None
            and evidence["active_authorization"] is False
            and reference["prior_t2_authorization_consumed"] is True
            and reference["prior_cleanup_t3_authorization_consumed"] is True
        ),
        "looker_separate": (
            policy["looker_is_separate"] is True
            and "looker_separate_authorization_required" in serving_source
            and "if looker_authorized" in materialization_source
        ),
        "sha_pinning_hardened": (
            "hex40" in serving_source
            and "serving_authorization_implementation_sha_invalid" in serving_source
        ),
        "no_remote_transport": all(
            token not in serving_source
            for token in ("googleapiclient", "requests", "httplib", "socket")
        ),
        "no_live_workflow": (
            not list((ROOT / ".github/workflows").glob("*bi-003*"))
            and ci.count("python scripts/github_bi_003_serving_gate.py") == 1
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
                "serving_files_mutated",
                "serving_manifests_created",
            )
        ),
        "no_schedule_recurrence": (
            evidence["schedule"] is False
            and evidence["recurrence"] is False
            and evidence["future_batch_execution_authorized"] is False
        ),
        "fixture_synthetic": (
            fixture["classification"] == "SYNTHETIC_SANITIZED_TEST_ONLY"
            and fixture["operational_authority"] is False
        ),
        "release_unchanged": (
            evidence["release_boundary_unchanged"] is True
            and evidence["task_024_authorized"] is False
            and evidence["release"]["0.7.0"] == "ACTIVE"
            and evidence["release"]["0.8.0"] == "CANDIDATE"
        ),
    }

    failed = [key for key, value in checks.items() if not value]
    status = (
        "PASS_BI_003_STABLE_SERVING_LAYER_IMPLEMENTATION_OFFLINE"
        if not failed
        else "STOP"
    )
    print(json.dumps({"status": status, "checks": checks, "failed_checks": failed}, sort_keys=True))
    return bool(failed)


if __name__ == "__main__":
    raise SystemExit(main())
