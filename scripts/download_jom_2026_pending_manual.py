"""TASK296 — Manual bounded download of 88 user-supplied JOM 2026 URLs.

These are candidate edition identities until their original PDF covers are checked.
One manual batch per invocation, no search, retry, Drive, recurrence or publication.
GitHub artifacts are temporary acquisition evidence, NOT SME Bronze custody.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.download_jom_loa2027_pilot import NoRedirect, PilotStop, inspect_pdf

FIXTURE = ROOT / "config/jom_2026_88_pending_urls_v1.json"
SCHEMA = "TASK296_JOM_2026_PENDING_88_OFFICIAL_URLS_V1"
BATCH_IDS = tuple(f"P{x:02d}" for x in range(1, 11))
BATCH_SIZE = 9
SOURCE_HOST = "ecrie.com.br"
SOURCE_PREFIX = "/Sistema/Conteudos/DiarioOficial/upload/"
MAX_PER_PDF = 200 * 1024 * 1024
MAX_TOTAL = 500 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024

# Explicit bounded target universe; never discover new editions during a live run.
EXPECTED_EDITIONS = tuple(sorted(
    [*range(7152, 7161), *range(7173, 7179),
     *range(7191, 7201), *range(7213, 7221),
     *range(7233, 7242), *range(7254, 7262),
     *range(7274, 7283), 7285, 7286,
     *range(7295, 7304), *range(7325, 7343)]
))


def load_sources(path: Path = FIXTURE) -> list[dict]:
    """Fail closed on missing, injected, duplicate or malformed fixtures."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PilotStop("STOP_FIXTURE_UNREADABLE") from exc
    if not isinstance(raw, dict) or raw.get("schema") != SCHEMA:
        raise PilotStop("STOP_FIXTURE_SCHEMA")
    rows = raw.get("sources")
    if not isinstance(rows, list) or len(rows) != 88 or raw.get("row_count") != 88 or raw.get("unique_source_urls") != 88:
        raise PilotStop("STOP_FIXTURE_COUNT")
    if any(not isinstance(r, dict) or type(r.get("edition")) is not int for r in rows):
        raise PilotStop("STOP_FIXTURE_ROW")
    if tuple(r["edition"] for r in rows) != EXPECTED_EDITIONS:
        raise PilotStop("STOP_FIXTURE_EDITION_SET_OR_ORDER")
    if len({r.get("url") for r in rows}) != 88:
        raise PilotStop("STOP_FIXTURE_DUPLICATE_URL")
    for row in rows:
        value = row.get("url")
        if not isinstance(value, str):
            raise PilotStop("STOP_SOURCE_URL_TYPE")
        parsed = urlparse(value)
        if not (
            parsed.scheme == "https"
            and parsed.netloc == SOURCE_HOST
            and parsed.path.startswith(SOURCE_PREFIX + "u_137_")
            and re.fullmatch(r"/Sistema/Conteudos/DiarioOficial/upload/u_137_\d{14}\.pdf", parsed.path)
            and not parsed.query and not parsed.fragment
        ):
            raise PilotStop("STOP_SOURCE_URL_DRIFT")
        expected_date = row.get("expected_date")
        if expected_date is not None and not (
            isinstance(expected_date, str) and
            re.fullmatch(r"2026-\d\d-\d\d", expected_date)
        ):
            raise PilotStop("STOP_EXPECTED_DATE_DRIFT")
        if row.get("identity_status") not in (
            "NUMBER_AND_DATE_INDEXED_PENDING_PDF_COVER",
            "NUMERICAL_CANDIDATE_PENDING_PDF_COVER",
        ):
            raise PilotStop("STOP_IDENTITY_STATUS")
        if row["edition"] in range(7152, 7161) and expected_date is None:
            raise PilotStop("STOP_JANUARY_DATE_MISSING")
        if row["edition"] not in range(7152, 7161) and expected_date is not None:
            raise PilotStop("STOP_UNVERIFIED_DATE_AS_FACT")
    return rows


def batch_map(path: Path = FIXTURE) -> dict[str, list[dict]]:
    rows = load_sources(path)
    out = {name: rows[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
           for i, name in enumerate(BATCH_IDS)}
    if tuple(len(out[name]) for name in BATCH_IDS) != (9,) * 9 + (7,):
        raise PilotStop("STOP_BATCH_PARTITION_DRIFT")
    return out


def require_manual_owner_context(env: dict, batch: str) -> None:
    if not (
        batch in BATCH_IDS
        and env.get("JOM296_BATCH") == batch
        and env.get("JOM296_OWNER_CONFIRM") == "true"
        and env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_RUN_ATTEMPT") == "1"
        and re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))
    ):
        raise PilotStop("STOP_OWNER_MANUAL_MAIN_ONESHOT_CONTEXT")


def collect_batch(out: Path, batch: str, *, transport=None, fixture: Path = FIXTURE) -> dict:
    if batch not in BATCH_IDS:
        raise PilotStop("STOP_UNKNOWN_BATCH")
    sources = batch_map(fixture)[batch]  # full preflight before GET
    transport = transport or build_opener(NoRedirect())
    originals = out / "originals"
    originals.mkdir(parents=True, exist_ok=False)
    statuses: list[dict] = []
    consumed = 0
    archived = 0
    attempts = 0

    for row in sources:
        ed = row["edition"]
        partial = originals / f".JOM_{ed}.part"
        final = originals / f"JOM_{ed}_2026_ORIGINAL.pdf"
        item = {
            "edition_candidate": ed,
            "url": row["url"],
            "expected_date": row["expected_date"],
            "identity_status_prior_to_pdf": row["identity_status"],
            "request_attempts": 0,
        }
        try:
            if consumed >= MAX_TOTAL:
                raise PilotStop("STOP_AGGREGATE_BUDGET_BEFORE_GET")
            sha = hashlib.sha256()
            received = 0
            attempts += 1
            item["request_attempts"] = 1
            with transport.open(
                Request(row["url"], headers={
                    "User-Agent": "LOA-LIMEIRA-2027-JOM-TASK296/1.0",
                    "Accept": "application/pdf",
                }, method="GET"),
                timeout=35,
            ) as response:
                if response.geturl() != row["url"]:
                    raise PilotStop("STOP_FINAL_URL_DRIFT")
                mime = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                if mime not in ("application/pdf", "application/octet-stream"):
                    raise PilotStop("STOP_RESPONSE_MIME")
                raw_length = response.headers.get("Content-Length")
                declared = int(raw_length) if raw_length is not None else None
                if declared is not None and (
                    declared < 100 or declared > MAX_PER_PDF or consumed + declared > MAX_TOTAL
                ):
                    raise PilotStop("STOP_DECLARED_BYTE_BUDGET")
                with partial.open("xb") as dest:
                    while True:
                        piece = response.read(CHUNK_BYTES)
                        if not piece:
                            break
                        consumed += len(piece)
                        received += len(piece)
                        if received > MAX_PER_PDF or consumed > MAX_TOTAL:
                            raise PilotStop("STOP_READ_BYTE_BUDGET")
                        sha.update(piece)
                        dest.write(piece)
            if declared is not None and received != declared:
                raise PilotStop("STOP_TRUNCATED_PDF")
            if received < 100 or partial.open("rb").read(5) != b"%PDF-":
                raise PilotStop("STOP_NOT_PDF_OR_TOO_SMALL")
            pages = inspect_pdf(partial, ed)  # number on first two pages, not URL name
            partial.rename(final)
            archived += received
            item.update({
                "status": "VALIDATED_ORIGINAL_IN_ARTIFACT_ONLY",
                "sha256": sha.hexdigest(), "bytes": received,
                "pages": pages, "file_name": final.name,
                "cover_edition_verified": True,
                "custodied_in_sme": False,
                "publication_date_verified": False,  # needs separate cover/date QA
            })
        except Exception as exc:
            partial.unlink(missing_ok=True)
            item.update({
                "status": "SOURCE_OR_VALIDATION_FAILED",
                "code": str(exc) if isinstance(exc, PilotStop) else type(exc).__name__,
                "no_absence_inference": True,
            })
        statuses.append(item)

    good = sum(x["status"] == "VALIDATED_ORIGINAL_IN_ARTIFACT_ONLY" for x in statuses)
    result = {
        "schema": "TASK296_JOM_PENDING_BATCH_RESULT_V1",
        "batch": batch, "status": "PASS_ALL_PDFS_IN_TEMP_ARTIFACT" if good == len(sources)
        else "PARTIAL_STOP_REVIEW",
        "requested_count": len(sources),
        "validated_count": good,
        "failed_count": len(sources) - good,
        "get_attempts": attempts, "retry_count": 0,
        "index_get_count": 0, "drive_read_count": 0,
        "drive_write_count": 0, "publication_count": 0,
        "bytes_transferred_including_failures": consumed,
        "bytes_archived": archived,
        "github_sha": os.getenv("GITHUB_SHA", "LOCAL_OFFLINE_TEST"),
        "artifact_expiring_not_bronze_custody": True,
        "all_88_identities_proven": False,
        "documents": statuses,
    }
    (out / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", choices=BATCH_IDS, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require_manual_owner_context(os.environ, args.batch)
    result = collect_batch(args.out, args.batch)
    print(json.dumps({
        "batch": args.batch,
        "status": result["status"],
        "validated_count": result["validated_count"],
        "requested_count": result["requested_count"],
        "get_attempts": result["get_attempts"],
    }, sort_keys=True))
    return 0 if result["validated_count"] == result["requested_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
