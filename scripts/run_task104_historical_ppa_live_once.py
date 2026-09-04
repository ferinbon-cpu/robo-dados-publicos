#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from robo_dados_publicos.research.eiti_historical_ppa_live import (
    BoundedOfficialHttpClient,
    HistoricalPpaLiveStop,
    acquire_historical_ppa_evidence,
    load_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/eiti_historical_ppa_primary_acquisition.v1.json"
RUNTIME = ROOT / "runtime"
RESULT = RUNTIME / "task104_result.json"


def canonical_sha256(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    return sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    contract = load_contract(CONTRACT)
    live = contract["live_contract"]
    client = BoundedOfficialHttpClient(
        allowed_hosts=set(live["allowed_hosts"]),
        total_max=int(live["maximum_http_requests_total"]),
        per_period_max=int(live["maximum_http_requests_per_period"]),
    )

    try:
        payload = acquire_historical_ppa_evidence(
            contract=contract,
            runtime_dir=RUNTIME,
            client=client,
        )
    except HistoricalPpaLiveStop as exc:
        payload = {
            "schema": "TASK_104_HISTORICAL_PPA_LIVE_RESULT_V1",
            "task": "TASK_104_SINGLE_USE_HISTORICAL_PPA_PRIMARY_EVIDENCE",
            "overall_status": "STOP_TASK104_FATAL_CONTRACT_OR_BUDGET_ERROR",
            "error": str(exc),
            "request_count": len(client.request_log),
            "requests": client.request_log,
            "hard_boundaries": {
                "drive_reads": 0,
                "drive_writes": 0,
                "bronze_writes": 0,
                "silver_writes": 0,
                "gold_writes": 0,
                "state_registry_writes": 0,
                "queue_writes": 0,
                "serving_writes": 0,
                "publications": 0,
                "financial_identity_assertions": 0,
                "causal_effect_assertions": 0,
            },
            "retry_performed": False,
            "recurrence": False,
            "schedule": False,
            "future_execution_authorized": False,
        }

    payload["contract_path"] = str(CONTRACT.relative_to(ROOT))
    payload["owner_authorization_path"] = (
        "docs/evidence/TASK_104_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
    )
    payload["result_canonical_sha256"] = canonical_sha256(payload)

    RUNTIME.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "overall_status": payload["overall_status"],
                "primary_match_count": payload.get("primary_match_count", 0),
                "request_count": payload["request_count"],
                "result_canonical_sha256": payload["result_canonical_sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
