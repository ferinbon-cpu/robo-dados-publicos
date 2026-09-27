from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from robo_dados_publicos.accounting.tcesp_json_api import normalize_json_expense_row, validate_payload
from robo_dados_publicos.analytics.observatory_products import build_accounting_ledger

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs/evidence/TASK_185_USER_SUPPLIED_JSON_JAN_JUL_2026.json"

MONTH_LABELS = {
    "JANEIRO":1, "FEVEREIRO":2, "MARÇO":3, "MARCO":3, "ABRIL":4,
    "MAIO":5, "JUNHO":6, "JULHO":7, "AGOSTO":8,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def detect_month(payload: bytes) -> int:
    obj = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(obj, list) or not obj:
        raise RuntimeError("TASK185_MANUAL_MONTH_NOT_DETECTABLE")
    labels = {str(row.get("mes") or "").upper() for row in obj if isinstance(row, dict)}
    if len(labels) != 1:
        raise RuntimeError("TASK185_MANUAL_MONTH_AMBIGUOUS")
    label = next(iter(labels))
    month = MONTH_LABELS.get(label)
    if month is None:
        raise RuntimeError("TASK185_MANUAL_MONTH_UNKNOWN")
    return month


def run(paths: list[Path], output_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["months"]
    seen: set[int] = set()
    observations = []
    files = []

    for path in paths:
        payload = path.read_bytes()
        month = detect_month(payload)
        if month in seen:
            raise RuntimeError("TASK185_MANUAL_DUPLICATE_MONTH")
        seen.add(month)
        rows, meta = validate_payload(payload, month=month)
        spec = expected.get(str(month))
        if spec and spec.get("sha256"):
            if meta["body_sha256"] != spec["sha256"]:
                raise RuntimeError(f"TASK185_MANUAL_HASH_MISMATCH_MONTH_{month}")
            if meta["row_count"] != spec["rows"]:
                raise RuntimeError(f"TASK185_MANUAL_ROWCOUNT_MISMATCH_MONTH_{month}")
        files.append({
            "month":month,
            "path_name":path.name,
            "sha256":meta["body_sha256"],
            "bytes":meta["body_bytes"],
            "rows":meta["row_count"],
        })
        observations.extend(
            normalize_json_expense_row(row, source_body_sha256=meta["body_sha256"], month=month)
            for row in rows
        )

    generated_at = datetime.now(timezone.utc).isoformat()
    ledger = build_accounting_ledger(observations, generated_at=generated_at, software_version="0.8.0")
    ledger["source_scope"] = {
        "route":"TCESP_JSON_API_USER_SUPPLIED_BYTES",
        "fiscal_year":2026,
        "months":sorted(seen),
        "august_status":expected["8"]["status"],
        "programmatic_classification_available":False,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(output_dir / "accounting_ledger.json.gz", "wb", compresslevel=9) as gz:
        gz.write(canonical_bytes(ledger))
    result = {
        "schema":"TASK185_MANUAL_JSON_INGEST_RESULT_V1",
        "status":"PASS",
        "network_gets":0,
        "months":sorted(seen),
        "files":files,
        "normalized_observations":len(observations),
        "ledger_snapshot_id":ledger["snapshot_id"],
        "ledger_content_sha256":ledger["content_sha256"],
        "capabilities":ledger["capabilities"],
        "august_status":expected["8"]["status"],
    }
    (output_dir / "result.json").write_bytes(canonical_bytes(result))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=Path("task185-manual-json-output"))
    args = parser.parse_args()
    result = run(args.files, args.output_dir, args.manifest)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
