#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from robo_dados_publicos.manual_ingest.mde_fundeb import validate_f02_source_bytes
from robo_dados_publicos.manual_ingest.mde_fundeb_parser import (
    load_f02_ingest_plan,
    normalize_f02_document,
    reconcile_f02,
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline fail-closed processor for the F02 MDE/FUNDEB supervised pilot."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--rreo", required=True)
    parser.add_argument("--fundeb-local", required=True)
    parser.add_argument("--mde25-local", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    plan = load_f02_ingest_plan(args.config)
    paths = {
        "RREO_MDE": Path(args.rreo),
        "FUNDEB_LOCAL": Path(args.fundeb_local),
        "MDE_25_LOCAL": Path(args.mde25_local),
    }

    source_results = []
    normalized = []
    for contract in plan["contracts"]:
        payload = paths[contract.family].read_bytes()
        verified = validate_f02_source_bytes(contract, payload)
        text = verified.pop("text")
        record = normalize_f02_document(contract, text)
        source_results.append(verified)
        normalized.append(record)

    reconciliation = reconcile_f02(normalized)
    core = {
        "schema": "F02_MDE_FUNDEB_SILVER_CANDIDATE_V1",
        "mode": "MANUAL_SUPERVISED_INGEST",
        "contract": plan["raw"]["contract"],
        "batch": plan["raw"]["batch"],
        "reference_period": plan["raw"]["reference_period"],
        "source_precedence": plan["raw"]["source_precedence"],
        "sources": source_results,
        "normalized": normalized,
        "reconciliation": reconciliation,
        "effects": {
            "drive_reads": 0,
            "bronze_writes": 0,
            "silver_writes": 0,
            "gold_writes": 0,
            "serving_writes": 0,
            "publication_writes": 0,
        },
        "status": "PASS_F02_OFFLINE_SILVER_CANDIDATE_NOT_PROMOTED",
    }
    digest = hashlib.sha256(canonical_bytes(core)).hexdigest()
    artifact = {"content_sha256": digest, **core}
    rendered = json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + "\n"

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
