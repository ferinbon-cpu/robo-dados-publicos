from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.manual_ingest.drive_ingestion_controller import (
    classify_metadata,
    load_controller_contract,
    route_inventory,
    summarize_routes,
)

CONTRACT = ROOT / "config" / "drive_ingestion_controller.v2.json"
EVIDENCE = ROOT / "docs" / "evidence" / "TASK_059A_OBSERVATORY_INGESTION_CATALOG_0.8.0.json"
FIXTURE = ROOT / "tests" / "fixtures" / "task_059a_observatory_ingestion_catalog.json"
EXPECTED_RESULT = "PASS_TASK059A_OBSERVATORY_WIDE_INGESTION_CATALOG_OFFLINE_READY"


def main() -> None:
    contract = load_controller_contract(CONTRACT)
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    fixtures = json.loads(FIXTURE.read_text(encoding="utf-8"))

    fixture_match = True
    for item in fixtures:
        decision = classify_metadata(item, contract)
        if decision.route != item["expected_route"] or decision.family != item["expected_family"]:
            fixture_match = False
            break

    summary = summarize_routes(route_inventory(fixtures, contract))
    default_routes = contract["family_default_routes"]
    checks = {
        "task_and_mode": contract.get("task") == "TASK_059A_OBSERVATORY_INGESTION_CATALOG" and contract.get("mode") == "T0_OFFLINE_ROUTING_CONTROLLER",
        "general_scope": contract.get("system_scope") == "GENERAL_MUNICIPAL_PUBLIC_DATA_OBSERVATORY",
        "eiti_not_global_filter": contract.get("eiti_role") == "ANALYTIC_USE_CASE_NOT_GLOBAL_INGESTION_FILTER",
        "family_count_21": len(contract.get("known_document_families", {})) == 21,
        "family_route_complete": set(default_routes) == set(contract["known_document_families"]),
        "journal_auto_eligible": default_routes.get("JORNAL_OFICIAL") == "AUTO_INGEST",
        "contracts_review": default_routes.get("MUNICIPAL_CONTRACTS") == "REVIEW",
        "tce_review": default_routes.get("TCE_SP_EXPENSES") == "REVIEW",
        "tda_review": default_routes.get("TDA_LIMEIRA") == "REVIEW",
        "siave_review": default_routes.get("SIAVE_LIMEIRA") == "REVIEW",
        "fixture_routes": fixture_match,
        "all_three_routes_exercised": all(summary[key] > 0 for key in ("AUTO_INGEST", "REVIEW", "QUARANTINE")),
        "remote_effects_zero": all(value == 0 for value in evidence.get("hard_boundaries", {}).values()),
        "f01_unchanged": evidence.get("f01_eiti_state", {}).get("changed_by_task_059a") is False,
        "next_gate_metadata_only": evidence.get("next_gate", {}).get("metadata_only") is True and evidence.get("next_gate", {}).get("content_read_allowed") is False,
        "result": evidence.get("result") == EXPECTED_RESULT,
    }

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit("STOP_TASK059A_OBSERVATORY_INGESTION_CATALOG_GATE:" + ",".join(failed))

    print(EXPECTED_RESULT)
    print(json.dumps({"checks": checks, "routes": summary}, sort_keys=True))


if __name__ == "__main__":
    main()
