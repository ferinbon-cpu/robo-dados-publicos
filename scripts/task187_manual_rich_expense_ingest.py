#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from robo_dados_publicos.accounting.tcesp_rich_expenses import (
    load_contract,
    normalize_csv_bytes,
    validate_real_payload,
)
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
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--software-version", default="0.8.0")
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = input_path.read_bytes()
    validation = validate_real_payload(payload)
    observations = normalize_csv_bytes(payload)
    product = build_accounting_ledger(
        observations,
        generated_at=args.generated_at,
        software_version=args.software_version,
    )
    contract = load_contract()
    product["source_scope"] = {
        "source": contract["source"]["source_id"],
        "months": contract["source"]["months_expected"],
        "official_record_id": "id_despesa_detalhe",
        "row_count": validation["row_count"],
        "raw_csv_sha256": contract["source"]["csv_sha256"],
        "raw_zip_sha256": contract["source"]["zip_sha256"],
        "reconciled_one_to_one_with_task185_json_ledger": contract["reconciliation"]["exact_one_to_one"],
        "reconciliation_rule": "+".join(contract["reconciliation"]["comparison_projection"]),
    }

    json_bytes = canonical_json_bytes(product)
    json_sha = hashlib.sha256(json_bytes).hexdigest()
    json_path = out_dir / "ACCOUNTING_LEDGER_RICH.json"
    json_path.write_bytes(json_bytes)

    gzip_path = out_dir / "ACCOUNTING_LEDGER_RICH.json.gz"
    with gzip.open(gzip_path, "wb", compresslevel=9) as stream:
        stream.write(json_bytes)
    gzip_bytes = gzip_path.read_bytes()
    gzip_sha = hashlib.sha256(gzip_bytes).hexdigest()

    manifest = {
        "schema": "TASK187_RICH_ACCOUNTING_LEDGER_MANIFEST_V1",
        "source_csv_sha256": contract["source"]["csv_sha256"],
        "source_zip_sha256": contract["source"]["zip_sha256"],
        "validation": validation,
        "product_name": product["product_name"],
        "product_schema": product["product_schema"],
        "snapshot_id": product["snapshot_id"],
        "content_sha256": product["content_sha256"],
        "row_count": product["row_count"],
        "capabilities": product["capabilities"],
        "observed_stages": product["observed_stages"],
        "json_sha256": json_sha,
        "json_bytes": len(json_bytes),
        "gzip_sha256": gzip_sha,
        "gzip_bytes": len(gzip_bytes),
        "generated_at": args.generated_at,
        "software_version": args.software_version,
        "network": False,
        "drive_write": False,
        "serving": False,
        "publication": False,
    }
    manifest_path = out_dir / "ACCOUNTING_LEDGER_RICH.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
