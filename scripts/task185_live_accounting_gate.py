from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from robo_dados_publicos.accounting.task185_persistence import (
    build_custody_manifest_plan,
    inspect_zip_bytes,
    load_contract,
)
from robo_dados_publicos.accounting.tcesp_current import (
    load_contracts as load_task173_contracts,
    normalize_tcesp_expense_row,
)
from robo_dados_publicos.analytics.observatory_knowledge_pack import question_answerability
from robo_dados_publicos.analytics.observatory_products import build_accounting_ledger
from robo_dados_publicos.analytics.task184_local_bundle import (
    _transition_report,
    _with_catalog,
    build_task184_bundle,
)
from robo_dados_publicos.storage.drive_rest import (
    DriveRESTClient,
    OAuthCredentials,
    TokenProvider,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUTH = ROOT / "docs/evidence/TASK_185_STAGE_B_OWNER_AUTHORIZATION_0.8.0.json"
OUTPUT_DIR = ROOT / "task185-live-output"


class Task185LiveStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task185LiveStop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _load_authorization(path: Path, implementation_sha: str) -> dict[str, Any]:
    auth = json.loads(path.read_text(encoding="utf-8"))
    _stop(auth.get("schema") == "TASK185_STAGE_B_OWNER_AUTHORIZATION_V1", "TASK185_AUTH_SCHEMA")
    _stop(auth.get("issue") == 581, "TASK185_AUTH_ISSUE")
    _stop(auth.get("status") == "AUTHORIZED_SINGLE_USE", "TASK185_AUTH_STATUS")
    _stop(auth.get("implementation_sha") == implementation_sha, "TASK185_AUTH_IMPLEMENTATION_SHA")
    _stop(auth.get("source_url") == load_contract()["source"]["url"], "TASK185_AUTH_SOURCE_URL")
    _stop(auth.get("source_id") == "TCESP_LIMEIRA_2026_DESPESAS", "TASK185_AUTH_SOURCE_ID")
    _stop(auth.get("custody_folder_id") == load_contract()["custody"]["target_folder_id"], "TASK185_AUTH_FOLDER")
    _stop(auth.get("max_source_requests") == 1, "TASK185_AUTH_REQUEST_BUDGET")
    _stop(auth.get("retry") == 0, "TASK185_AUTH_RETRY")
    _stop(auth.get("serving") is False, "TASK185_AUTH_SERVING")
    _stop(auth.get("publication") is False, "TASK185_AUTH_PUBLICATION")
    _stop(auth.get("schedule") is False, "TASK185_AUTH_SCHEDULE")
    _stop(auth.get("recurrence") is False, "TASK185_AUTH_RECURRENCE")
    return auth


def _verify_git_parent(implementation_sha: str) -> str:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], text=True).strip()
    _stop(len(head) == 40, "TASK185_GIT_HEAD")
    _stop(parent == implementation_sha, "TASK185_AUTH_COMMIT_PARENT")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD^", "HEAD"],
        text=True,
    ).splitlines()
    _stop(
        changed == ["docs/evidence/TASK_185_STAGE_B_OWNER_AUTHORIZATION_0.8.0.json"],
        "TASK185_AUTH_COMMIT_DIFF",
    )
    return head


def _download_once(url: str, max_bytes: int) -> bytes:
    opener = urllib.request.build_opener(_NoRedirect())
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "ROBO_DADOS_PUBLICOS-TASK185/0.8.0",
            "Accept": "application/zip, application/octet-stream;q=0.9, */*;q=0.1",
        },
    )
    try:
        with opener.open(request, timeout=60) as response:
            status = int(getattr(response, "status", 0) or response.getcode())
            _stop(status == 200, f"TASK185_SOURCE_HTTP_{status}")
            content_type = str(response.headers.get("Content-Type") or "")
            chunks: list[bytes] = []
            total = 0
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                _stop(total <= max_bytes, "TASK185_SOURCE_RESPONSE_TOO_LARGE")
                chunks.append(block)
    except urllib.error.HTTPError as exc:
        raise Task185LiveStop(f"TASK185_SOURCE_HTTP_{exc.code}") from exc
    except urllib.error.URLError as exc:
        raise Task185LiveStop("TASK185_SOURCE_TRANSPORT") from exc
    payload = b"".join(chunks)
    _stop(bool(payload), "TASK185_SOURCE_EMPTY")
    return payload


def _csv_member_bytes(zip_payload: bytes, member_name: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(zip_payload)) as archive:
        return archive.read(member_name)


def _rows_from_csv(csv_payload: bytes, *, encoding: str, delimiter: str) -> list[dict[str, str]]:
    text = csv_payload.decode(encoding)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for row in reader:
        normalized = {
            str(key or "").strip().lstrip("\ufeff"): "" if value is None else str(value)
            for key, value in row.items()
        }
        if any(value.strip() for value in normalized.values()):
            rows.append(normalized)
    return rows


def _build_stage_c(
    csv_payload: bytes,
    inspection: dict[str, Any],
    *,
    generated_at: str,
    software_version: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = _rows_from_csv(
        csv_payload,
        encoding=inspection["csv_encoding"],
        delimiter=inspection["csv_delimiter"],
    )
    _stop(len(rows) == inspection["record_count"], "TASK185_STAGE_C_ROW_COUNT_DRIFT")

    observations = [normalize_tcesp_expense_row(row) for row in rows]
    _stop(len(observations) == len(rows), "TASK185_STAGE_C_NORMALIZATION_COUNT")
    accounting = build_accounting_ledger(
        observations,
        generated_at=generated_at,
        software_version=software_version,
    )
    _stop(accounting["row_count"] == len(rows), "TASK185_LEDGER_ROW_COUNT")

    task184 = build_task184_bundle(
        generated_at=generated_at,
        software_version=software_version,
    )
    before = task184["answerability"]["final"]
    substantive = {
        name: product
        for name, product in task184["products"].items()
        if name != "QUERY_PRODUCT_CATALOG"
    }
    after_products = _with_catalog(
        {**substantive, "ACCOUNTING_LEDGER": accounting},
        generated_at=generated_at,
        software_version=software_version,
    )
    after = question_answerability(after_products)
    gain = _transition_report(before, after)

    adapter, _observation_contract = load_task173_contracts()
    stage_counts = dict(sorted(Counter(obs["stage"] for obs in observations).items()))
    missing_expense_id = sum(
        1
        for obs in observations
        if not obs["transaction_keys"].get("source_expense_identifier")
    )
    missing_empenho = sum(
        1
        for obs in observations
        if not obs["transaction_keys"].get("fiscal_year_plus_empenho")
    )
    policy_hint_counts = Counter()
    for obs in observations:
        policy_hint_counts.update(obs.get("policy_domain_hints") or [])

    summary = {
        "schema": "TASK185_STAGE_C_ACCOUNTING_MATERIALIZATION_RESULT_V1",
        "source_id": "TCESP_LIMEIRA_2026_DESPESAS",
        "source_csv_sha256": inspection["csv_sha256"],
        "source_row_count": len(rows),
        "normalized_observation_count": len(observations),
        "accounting_ledger": {
            "product_schema": accounting["product_schema"],
            "snapshot_id": accounting["snapshot_id"],
            "content_sha256": accounting["content_sha256"],
            "row_count": accounting["row_count"],
            "stage_counts": stage_counts,
            "policy_domain_hint_counts": dict(sorted(policy_hint_counts.items())),
        },
        "unsupported_or_missing_field_ledger": {
            "source_columns_not_assumed": adapter["unproven_columns_not_assumed"],
            "rows_missing_source_expense_identifier": missing_expense_id,
            "rows_missing_fiscal_year_plus_empenho": missing_empenho,
            "other_review_rows": stage_counts.get("OTHER_REVIEW", 0),
        },
        "answerability": {
            "question_count": after["question_count"],
            "before_status_counts": before["status_counts"],
            "after_status_counts": after["status_counts"],
            "accounting_attributable_gain": gain,
        },
        "guards": {
            "control_record_ne_municipal_primary_policy_identity": True,
            "commitment_ne_liquidation_ne_payment": True,
            "amount_date_text_ne_identity": True,
            "program_action_source_ne_specific_policy_identity": True,
            "weak_join_can_create_identity": False,
        },
        "remote_effects": {
            "stage_c_source_network": 0,
            "stage_c_drive_write": 0,
            "serving": 0,
            "publication": 0,
        },
    }
    compact_ledger = {
        "product_name": accounting["product_name"],
        "product_schema": accounting["product_schema"],
        "snapshot_id": accounting["snapshot_id"],
        "content_sha256": accounting["content_sha256"],
        "row_count": accounting["row_count"],
        "generated_at": accounting["generated_at"],
        "software_version": accounting["software_version"],
        "rows": accounting["rows"],
    }
    return summary, compact_ledger


def _drive_client() -> DriveRESTClient:
    credentials = OAuthCredentials.from_env()
    return DriveRESTClient(TokenProvider(credentials))


def _preflight_collisions(client: DriveRESTClient, folder_id: str, names: list[str]) -> None:
    listing = client.list_children_single_page(folder_id, page_size=1000)
    _stop(not listing.get("next_page_token"), "TASK185_DRIVE_FOLDER_PAGINATION")
    existing = {str(item.get("name") or "") for item in listing["files"]}
    collisions = sorted(set(names) & existing)
    _stop(not collisions, "TASK185_DRIVE_COLLISION")


def _write_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _readback_sha(client: DriveRESTClient, file_id: str, expected_sha: str, destination: Path) -> dict[str, Any]:
    got = client.get(file_id, destination)
    _stop(got["sha256"] == expected_sha, "TASK185_DRIVE_READBACK_SHA")
    return got


def run(
    *,
    authorization_path: Path,
    implementation_sha: str,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    contract = load_contract()
    auth = _load_authorization(authorization_path, implementation_sha)
    authorization_commit_sha = _verify_git_parent(implementation_sha)

    payload = _download_once(
        contract["source"]["url"],
        int(contract["source"]["max_response_bytes"]),
    )
    inspection = inspect_zip_bytes(payload)
    csv_payload = _csv_member_bytes(payload, inspection["member_name"])
    _stop(_sha256_bytes(csv_payload) == inspection["csv_sha256"], "TASK185_CSV_SHA_REOPEN")

    manifest_plan = build_custody_manifest_plan(
        inspection,
        retrieved_at=generated_at,
        authorization_artifact=str(authorization_path.relative_to(ROOT)),
        implementation_sha=implementation_sha,
    )

    stage_c_summary, compact_ledger = _build_stage_c(
        csv_payload,
        inspection,
        generated_at=generated_at,
        software_version=software_version,
    )
    stage_counts = stage_c_summary["accounting_ledger"]["stage_counts"]

    folder_id = contract["custody"]["target_folder_id"]
    names = manifest_plan["artifact_names"]
    client = _drive_client()
    _preflight_collisions(client, folder_id, [names["zip"], names["csv"], names["manifest"]])

    with tempfile.TemporaryDirectory(prefix="task185-live-") as tmp:
        tmpdir = Path(tmp)
        zip_path = tmpdir / names["zip"]
        csv_path = tmpdir / names["csv"]
        _write_file(zip_path, payload)
        _write_file(csv_path, csv_payload)

        zip_created = client.put(
            zip_path,
            names["zip"],
            folder_id,
            mime_type="application/zip",
        )
        csv_created = client.put(
            csv_path,
            names["csv"],
            folder_id,
            mime_type="text/csv",
        )
        _stop(zip_created.get("name") == names["zip"], "TASK185_DRIVE_ZIP_NAME")
        _stop(csv_created.get("name") == names["csv"], "TASK185_DRIVE_CSV_NAME")

        zip_readback = _readback_sha(
            client,
            zip_created["id"],
            inspection["zip_sha256"],
            tmpdir / "readback.zip",
        )
        csv_readback = _readback_sha(
            client,
            csv_created["id"],
            inspection["csv_sha256"],
            tmpdir / "readback.csv",
        )

        manifest = {
            **manifest_plan,
            "schema": "TASK185_TCE_CUSTODY_MANIFEST_V1",
            "stage_counts": stage_counts,
            "authorization_commit_sha": authorization_commit_sha,
            "owner_authorization_text": auth["owner_authorization_text"],
            "drive_objects": {
                "zip": {
                    "id": zip_created["id"],
                    "name": zip_created["name"],
                    "sha256": zip_readback["sha256"],
                    "bytes": zip_readback["bytes"],
                },
                "csv": {
                    "id": csv_created["id"],
                    "name": csv_created["name"],
                    "sha256": csv_readback["sha256"],
                    "bytes": csv_readback["bytes"],
                },
            },
            "accounting_ledger_snapshot_id": stage_c_summary["accounting_ledger"]["snapshot_id"],
            "accounting_ledger_content_sha256": stage_c_summary["accounting_ledger"]["content_sha256"],
            "answerability_gain": stage_c_summary["answerability"]["accounting_attributable_gain"],
        }
        manifest_bytes = _canonical_bytes(manifest)
        manifest_sha = _sha256_bytes(manifest_bytes)
        manifest_path = tmpdir / names["manifest"]
        _write_file(manifest_path, manifest_bytes)
        manifest_created = client.put(
            manifest_path,
            names["manifest"],
            folder_id,
            mime_type="application/json",
        )
        _stop(manifest_created.get("name") == names["manifest"], "TASK185_DRIVE_MANIFEST_NAME")
        manifest_readback = _readback_sha(
            client,
            manifest_created["id"],
            manifest_sha,
            tmpdir / "readback-manifest.json",
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "TASK185_STAGE_B_C_LIVE_RESULT_V1",
        "status": "PASS",
        "authorization": {
            "implementation_sha": implementation_sha,
            "authorization_commit_sha": authorization_commit_sha,
            "owner_authorization_text": auth["owner_authorization_text"],
            "single_use": True,
        },
        "source": {
            "source_id": contract["source"]["source_id"],
            "url": contract["source"]["url"],
            "request_count": 1,
            "retry_count": 0,
            "zip_sha256": inspection["zip_sha256"],
            "zip_bytes": inspection["zip_bytes"],
            "member_name": inspection["member_name"],
            "csv_sha256": inspection["csv_sha256"],
            "csv_bytes": inspection["csv_bytes"],
            "record_count": inspection["record_count"],
            "historical_task172_record_count": inspection["historical_task172_record_count"],
            "record_count_required_to_match_historical": False,
        },
        "custody": {
            "folder_id": folder_id,
            "create_only": True,
            "collision_policy": "STOP_BEFORE_FIRST_WRITE",
            "manifest_written_last": True,
            "zip_file_id": zip_created["id"],
            "csv_file_id": csv_created["id"],
            "manifest_file_id": manifest_created["id"],
            "manifest_sha256": manifest_readback["sha256"],
        },
        "stage_c": stage_c_summary,
        "remote_effects": {
            "source_gets": 1,
            "drive_creates": 3,
            "drive_readbacks": 3,
            "serving": 0,
            "publication": 0,
            "schedule": 0,
            "recurrence": 0,
        },
    }
    (OUTPUT_DIR / "result.json").write_bytes(_canonical_bytes(result))
    (OUTPUT_DIR / "stage_c_summary.json").write_bytes(_canonical_bytes(stage_c_summary))
    with gzip.open(OUTPUT_DIR / "accounting_ledger.json.gz", "wb", compresslevel=9) as gz:
        gz.write(_canonical_bytes(compact_ledger))
    print(json.dumps({
        "status": "PASS",
        "source_record_count": inspection["record_count"],
        "accounting_snapshot_id": stage_c_summary["accounting_ledger"]["snapshot_id"],
        "accounting_gain_changed_questions": stage_c_summary["answerability"]["accounting_attributable_gain"]["changed_question_count"],
        "drive_creates": 3,
        "source_gets": 1,
    }, ensure_ascii=False, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", default=str(DEFAULT_AUTH))
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--software-version", default="0.8.0")
    args = parser.parse_args()
    run(
        authorization_path=Path(args.authorization).resolve(),
        implementation_sha=args.implementation_sha,
        generated_at=args.generated_at,
        software_version=args.software_version,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
