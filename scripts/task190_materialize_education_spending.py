#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from robo_dados_publicos.analytics.task190_rreo_education_spending import build_fiscal_overlay


def canonical_json_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--software-version", default="0.8.0")
    args = parser.parse_args()

    product = build_fiscal_overlay(
        generated_at=args.generated_at,
        software_version=args.software_version,
    )
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_bytes = canonical_json_bytes(product)
    json_path = out_dir / "FISCAL_SERIES_TASK190.json"
    json_path.write_bytes(json_bytes)

    gzip_path = out_dir / "FISCAL_SERIES_TASK190.json.gz"
    with gzip_path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as stream:
            stream.write(json_bytes)
    gzip_bytes = gzip_path.read_bytes()

    manifest = {
        "schema": "TASK190_FISCAL_SERIES_MANIFEST_V1",
        "product_name": product["product_name"],
        "product_schema": product["product_schema"],
        "snapshot_id": product["snapshot_id"],
        "content_sha256": product["content_sha256"],
        "row_count": product["row_count"],
        "base_task183_rows": product["overlay_scope"]["base_task183_rows"],
        "task190_rows": product["overlay_scope"]["task190_rows"],
        "canonical_spending_metric": product["overlay_scope"]["canonical_spending_metric"],
        "canonical_stage_semantic": product["overlay_scope"]["canonical_stage_semantic"],
        "annual_final": False,
        "real_terms": False,
        "per_student_metric_materialized": False,
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
    manifest_path = out_dir / "FISCAL_SERIES_TASK190.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
