from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from robo_dados_publicos.accounting.tcesp_json_api import (
    Task185JsonStop,
    load_contract,
    normalize_json_expense_row,
    source_capabilities,
    validate_payload,
)
from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.observatory_products import build_accounting_ledger
from robo_dados_publicos.analytics.task184_local_bundle import _transition_report, _with_catalog, build_task184_bundle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "task185-json-live-output"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def exact_auth_comment(main_sha: str) -> str:
    return f"TASK185_JSON_API_2026_LIVE_AUTHORIZED main={main_sha} months=1-8 max_requests=8 retry=0"


def verify_authorization() -> tuple[str, str]:
    main_sha = os.environ.get("GITHUB_SHA", "").strip()
    body = os.environ.get("TASK185_AUTH_COMMENT", "")
    actor = os.environ.get("GITHUB_ACTOR", "")
    issue = os.environ.get("TASK185_ISSUE_NUMBER", "")
    if len(main_sha) != 40:
        raise RuntimeError("TASK185_AUTH_MAIN_SHA")
    if actor != "ferinbon-cpu":
        raise RuntimeError("TASK185_AUTH_ACTOR")
    if issue != "581":
        raise RuntimeError("TASK185_AUTH_ISSUE")
    if body != exact_auth_comment(main_sha):
        raise RuntimeError("TASK185_AUTH_COMMENT_MISMATCH")
    return main_sha, body


def get_once(url: str, max_bytes: int) -> tuple[bytes, str]:
    opener = urllib.request.build_opener(NoRedirect())
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent":"ROBO_DADOS_PUBLICOS-TASK185-JSON/0.8.0","Accept":"application/json"},
    )
    try:
        with opener.open(req, timeout=60) as response:
            status = int(getattr(response, "status", 0) or response.getcode())
            if status != 200:
                raise Task185JsonStop(f"TASK185_JSON_HTTP_{status}")
            content_type = str(response.headers.get("Content-Type") or "")
            blocks = []
            total = 0
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > max_bytes:
                    raise Task185JsonStop("TASK185_JSON_BODY_TOO_LARGE")
                blocks.append(block)
    except urllib.error.HTTPError as exc:
        raise Task185JsonStop(f"TASK185_JSON_HTTP_{exc.code}") from exc
    except urllib.error.URLError as exc:
        raise Task185JsonStop("TASK185_JSON_TRANSPORT") from exc
    payload = b"".join(blocks)
    if not payload:
        raise Task185JsonStop("TASK185_JSON_EMPTY_BODY")
    return payload, content_type


def run() -> int:
    contract = load_contract()
    main_sha, auth_comment = verify_authorization()
    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    requests_used = 0
    month_manifest = []
    observations = []
    stop_code = None

    for month in contract["source"]["months"]:
        url = contract["source"]["url_template"].format(month=month)
        requests_used += 1
        try:
            payload, content_type = get_once(url, int(contract["source"]["max_response_bytes_per_month"]))
            rows, meta = validate_payload(payload, month=month)
            if month == contract["source"]["probe_month"] and not rows:
                raise Task185JsonStop("TASK185_JSON_PROBE_EMPTY")
            raw_path = raw_dir / f"month_{month:02d}.json"
            raw_path.write_bytes(payload)
            meta["url"] = url
            meta["content_type"] = content_type
            meta["raw_file"] = str(raw_path.relative_to(OUT))
            month_manifest.append(meta)
            observations.extend(
                normalize_json_expense_row(
                    row,
                    source_body_sha256=meta["body_sha256"],
                    month=month,
                )
                for row in rows
            )
        except Task185JsonStop as exc:
            stop_code = str(exc)
            break

    if stop_code is not None:
        result = {
            "schema":"TASK185_JSON_API_2026_LIVE_RESULT_V1",
            "status":"STOP",
            "stop_code":stop_code,
            "authorization":{
                "main_sha":main_sha,
                "issue":581,
                "comment":auth_comment,
                "single_use":True,
                "consumed": requests_used > 0,
            },
            "source":{
                "requests_used":requests_used,
                "max_requests":8,
                "retry_count":0,
                "months_completed":[row["month"] for row in month_manifest],
            },
            "month_manifest":month_manifest,
            "accounting_ledger_materialized":False,
            "stage_c_executed":False,
        }
        write_json(OUT / "result.json", result)
        write_json(OUT / "source_manifest.json", {
            "schema":"TASK185_JSON_API_2026_SOURCE_MANIFEST_V1",
            "status":"PARTIAL_STOP",
            "months":month_manifest,
        })
        print(json.dumps({"status":"STOP","stop_code":stop_code,"requests_used":requests_used}, sort_keys=True))
        return 0

    capabilities = source_capabilities(observations)
    ledger = build_accounting_ledger(
        observations,
        generated_at=generated_at,
        software_version="0.8.0",
    )
    ledger["capabilities"] = capabilities
    ledger["source_scope"] = {
        "route":"TCESP_JSON_API",
        "fiscal_year":2026,
        "months":[1,2,3,4,5,6,7,8],
        "programmatic_classification_available":False,
    }

    task184 = build_task184_bundle(generated_at=generated_at, software_version="0.8.0")
    before = task184["answerability"]["final"]
    substantive = {k:v for k,v in task184["products"].items() if k != "QUERY_PRODUCT_CATALOG"}
    after_products = _with_catalog(
        {**substantive, "ACCOUNTING_LEDGER": ledger},
        generated_at=generated_at,
        software_version="0.8.0",
    )
    after = question_answerability(after_products)
    gain = _transition_report(before, after)

    stage_counts = dict(sorted(Counter(row["stage"] for row in observations).items()))
    source_bundle_sha = hashlib.sha256(canonical_bytes([
        [m["month"], m["body_sha256"], m["row_count"]] for m in month_manifest
    ])).hexdigest()

    manifest = {
        "schema":"TASK185_JSON_API_2026_SOURCE_MANIFEST_V1",
        "status":"COMPLETE",
        "source_id":contract["source"]["source_id"],
        "fiscal_year":2026,
        "months":[1,2,3,4,5,6,7,8],
        "request_count":requests_used,
        "retry_count":0,
        "source_bundle_sha256":source_bundle_sha,
        "total_rows":sum(m["row_count"] for m in month_manifest),
        "months_detail":month_manifest,
        "capabilities":capabilities,
        "missing_capabilities":contract["source_capabilities"]["not_provided"],
    }
    write_json(OUT / "source_manifest.json", manifest)

    compact = {
        "product_name":ledger["product_name"],
        "product_schema":ledger["product_schema"],
        "snapshot_id":ledger["snapshot_id"],
        "content_sha256":ledger["content_sha256"],
        "row_count":ledger["row_count"],
        "generated_at":ledger["generated_at"],
        "software_version":ledger["software_version"],
        "capabilities":capabilities,
        "source_scope":ledger["source_scope"],
        "rows":ledger["rows"],
    }
    with gzip.open(OUT / "accounting_ledger.json.gz", "wb", compresslevel=9) as gz:
        gz.write(canonical_bytes(compact))

    result = {
        "schema":"TASK185_JSON_API_2026_LIVE_RESULT_V1",
        "status":"PASS",
        "authorization":{
            "main_sha":main_sha,
            "issue":581,
            "comment":auth_comment,
            "single_use":True,
            "consumed":True,
        },
        "source":{
            "requests_used":requests_used,
            "max_requests":8,
            "retry_count":0,
            "months":[1,2,3,4,5,6,7,8],
            "total_rows":manifest["total_rows"],
            "source_bundle_sha256":source_bundle_sha,
        },
        "accounting":{
            "normalized_observations":len(observations),
            "ledger_snapshot_id":ledger["snapshot_id"],
            "ledger_content_sha256":ledger["content_sha256"],
            "stage_counts":stage_counts,
            "capabilities":capabilities,
            "missing_capabilities":contract["source_capabilities"]["not_provided"],
        },
        "answerability":{
            "before_status_counts":before["status_counts"],
            "after_status_counts":after["status_counts"],
            "accounting_attributable_gain":gain,
        },
        "remote_effects":{
            "source_gets":requests_used,
            "drive_writes":0,
            "serving":0,
            "publication":0,
            "schedule":0,
            "recurrence":0,
        },
    }
    write_json(OUT / "result.json", result)
    print(json.dumps({
        "status":"PASS",
        "requests_used":requests_used,
        "total_rows":manifest["total_rows"],
        "stage_counts":stage_counts,
        "changed_questions":gain["changed_question_count"],
        "capabilities":capabilities,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(run())
