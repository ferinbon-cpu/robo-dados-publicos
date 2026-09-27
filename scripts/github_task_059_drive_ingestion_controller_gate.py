from __future__ import annotations

import json
from pathlib import Path

from robo_dados_publicos.manual_ingest.drive_ingestion_controller import (
    classify_metadata,
    load_controller_contract,
    route_inventory,
    summarize_routes,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/drive_ingestion_controller.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_059_DRIVE_INGESTION_CONTROLLER_0.8.0.json"
FIXTURE = ROOT / "tests/fixtures/task_059_drive_ingestion_controller.json"
EXPECTED_RESULT = "PASS_TASK059_DRIVE_INGESTION_CONTROLLER_OFFLINE_READY_FOR_METADATA_PILOT"


def main() -> None:
    contract = load_controller_contract(CONTRACT)
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    fixtures = json.loads(FIXTURE.read_text(encoding="utf-8"))
    decisions = route_inventory(fixtures, contract)
    summary = summarize_routes(decisions)

    fixture_match = all(
        classify_metadata(item, contract).route == item["expected"] for item in fixtures
    )
    hard = evidence.get("hard_boundaries") or {}
    zero_effects = all(value == 0 for value in hard.values())
    checks = {
        "task_and_mode": evidence.get("task") == "TASK_059_DRIVE_INGESTION_CONTROLLER" and evidence.get("mode") == "T0_OFFLINE_ROUTING_CONTROLLER",
        "base_pinned": evidence.get("base_sha") == "e5c6658b1e05fc2d824e5d9cbcc116b0e9f40a5c",
        "metadata_only": contract.get("allowed_input_surface") == "DRIVE_METADATA_ONLY",
        "fixture_routes": fixture_match,
        "all_three_routes_exercised": all(summary[key] > 0 for key in ("AUTO_INGEST", "REVIEW", "QUARANTINE")),
        "auto_ingest_is_routing_only": contract.get("routing_semantics", {}).get("AUTO_INGEST", "").startswith("Eligible for a later authorized"),
        "future_execution_separate": contract.get("handoff", {}).get("auto_ingest_requires_separate_execution_authorization") is True,
        "hash_required_for_content_dedupe": contract.get("deduplication", {}).get("hash_required_for_content_duplicate_claim") is True,
        "zero_remote_effects": zero_effects,
        "task058_deferred": evidence.get("task058_status") == "DEFERRED_NOT_EXECUTED",
        "f01_unchanged": evidence.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED" and evidence.get("eiti_transaction_level_financial_identity") == "EVIDENCIA_INSUFICIENTE",
        "result": evidence.get("result") == EXPECTED_RESULT,
    }
    failed = [name for name, passed in checks.items() if not passed]
    status = EXPECTED_RESULT if not failed else "STOP_TASK059_DRIVE_INGESTION_CONTROLLER"
    print(json.dumps({"status": status, "checks": checks, "routing_summary": summary, "failed_checks": failed}, ensure_ascii=False, sort_keys=True))
    if failed:
        raise SystemExit(13)


if __name__ == "__main__":
    main()
