#!/usr/bin/env python3
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.eiti_historical_ppa_live import (  # noqa: E402
    BoundedOfficialHttpClient,
    HistoricalPpaLiveStop,
    acquire_historical_ppa_evidence,
    load_contract,
)
from robo_dados_publicos.research.local_pdf_capability import (  # noqa: E402
    LocalPdfCapabilityStop,
    _minimal_pdf_bytes,
    extract_pdf_text_pypdf,
)


CONTRACT = ROOT / "config/eiti_historical_ppa_primary_acquisition.v1.json"
RUNTIME = ROOT / "runtime"
RESULT = RUNTIME / "task107_result.json"


def canonical_sha256(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    return sha256(canonical.encode("utf-8")).hexdigest()


def parser_preflight() -> dict:
    marker = "TASK107_RUNNER_BOOTSTRAP_PYPDF_MARKER_73159"
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "synthetic.pdf"
        path.write_bytes(_minimal_pdf_bytes(marker))
        text = extract_pdf_text_pypdf(path)
        if marker not in text:
            raise LocalPdfCapabilityStop("TASK107_PYPDF_PREFLIGHT_MARKER_NOT_RECOVERED")
    return {
        "status": "PASS_TASK107_RUNNER_BOOTSTRAP_AND_PYPDF_PREFLIGHT",
        "repository_root": str(ROOT),
        "marker_recovered": True,
        "source_requests": 0,
    }


def _task107_payload(payload: dict) -> dict:
    converted = dict(payload)
    converted["schema"] = "TASK_107_HISTORICAL_PPA_LIVE_RESULT_V1"
    converted["task"] = "TASK_107_SINGLE_USE_HISTORICAL_PPA_PRIMARY_EVIDENCE_PYPDF"
    status = str(converted.get("overall_status") or "")
    converted["overall_status"] = status.replace("TASK104", "TASK107")
    converted["parser"] = {
        "name": "pypdf",
        "version_contract": "pypdf==6.10.0",
        "offline_capability_proof_task": "TASK_105",
        "runner_bootstrap_proof_task": "TASK_107",
    }
    return converted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    preflight = parser_preflight()
    if args.preflight_only:
        print(json.dumps(preflight, ensure_ascii=False, sort_keys=True))
        return 0

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
            extract_pdf_text=extract_pdf_text_pypdf,
        )
        payload = _task107_payload(payload)
    except (HistoricalPpaLiveStop, LocalPdfCapabilityStop) as exc:
        payload = {
            "schema": "TASK_107_HISTORICAL_PPA_LIVE_RESULT_V1",
            "task": "TASK_107_SINGLE_USE_HISTORICAL_PPA_PRIMARY_EVIDENCE_PYPDF",
            "overall_status": "STOP_TASK107_FATAL_CONTRACT_BUDGET_OR_PARSER_ERROR",
            "error": str(exc),
            "request_count": len(client.request_log),
            "requests": client.request_log,
            "parser": {
                "name": "pypdf",
                "version_contract": "pypdf==6.10.0",
                "offline_capability_proof_task": "TASK_105",
                "runner_bootstrap_proof_task": "TASK_107",
            },
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

    payload["preflight"] = preflight
    payload["contract_path"] = str(CONTRACT.relative_to(ROOT))
    payload["owner_authorization_path"] = (
        "docs/evidence/TASK_107_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
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
