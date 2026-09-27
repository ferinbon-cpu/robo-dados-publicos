#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from robo_dados_publicos.accounting.rreo_rests_payable import build_rests_payable_observations
from robo_dados_publicos.analytics.observatory_products import build_accounting_ledger


def canonical_json_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ledger", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--software-version", default="0.8.0")
    args = parser.parse_args()

    base_path = Path(args.base_ledger)
    if base_path.suffix == ".gz":
        with gzip.open(base_path, "rt", encoding="utf-8") as stream:
            base = json.load(stream)
    else:
        base = json.loads(base_path.read_text(encoding="utf-8"))

    base_rows = []
    for raw in base["rows"]:
        row = dict(raw)
        row.pop("snapshot_id", None)
        base_rows.append(row)

    rp_rows = build_rests_payable_observations()
    product = build_accounting_ledger(
        [*base_rows, *rp_rows],
        generated_at=args.generated_at,
        software_version=args.software_version,
    )
    product["source_scope"] = {
        "base_accounting_snapshot_id": base["snapshot_id"],
        "base_accounting_row_count": base["row_count"],
        "rests_payable_observation_count": len(rp_rows),
        "rests_payable_periods": ["2026-02", "2026-04"],
        "rreo_aggregate_materialized": True,
        "tcesp_granular_rests_materialized": False,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_bytes = canonical_json_bytes(product)
    json_path = out_dir / "ACCOUNTING_LEDGER_WITH_RESTS.json"
    json_path.write_bytes(json_bytes)

    gzip_path = out_dir / "ACCOUNTING_LEDGER_WITH_RESTS.json.gz"
    with gzip.open(gzip_path, "wb", compresslevel=9) as stream:
        stream.write(json_bytes)

    gzip_bytes = gzip_path.read_bytes()
    manifest = {
        "schema": "TASK188_ACCOUNTING_LEDGER_WITH_RESTS_MANIFEST_V1",
        "base_snapshot_id": base["snapshot_id"],
        "product_name": product["product_name"],
        "product_schema": product["product_schema"],
        "snapshot_id": product["snapshot_id"],
        "content_sha256": product["content_sha256"],
        "row_count": product["row_count"],
        "capabilities": product["capabilities"],
        "observed_stages": product["observed_stages"],
        "json_sha256": hashlib.sha256(json_bytes).hexdigest(),
        "json_bytes": len(json_bytes),
        "gzip_sha256": hashlib.sha256(gzip_bytes).hexdigest(),
        "gzip_bytes": len(gzip_bytes),
        "generated_at": args.generated_at,
        "software_version": args.software_version,
        "network": False,
        "drive_write": False,
        "serving": False,
        "publication": False,
    }
    manifest_path = out_dir / "ACCOUNTING_LEDGER_WITH_RESTS.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
