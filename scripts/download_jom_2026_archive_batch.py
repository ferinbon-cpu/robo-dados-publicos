"""TASK288: Nine explicit manual, nine-PDF archive batches from the pinned 87 JOM originals.

Exclude the six originals already in the SME bronze folder on 2026-10-10.
The 12 other pre-existing (August) editions belong to the separate 99-edition
discovery fixture and are not in this pinned 87-document CSV.
Only original public PDF bytes and an auditable manifest are archived.
NO Drive/network discovery, automatic retries, recurrence or publication.
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

from robo_dados_publicos.research.task219a_jom_general_event_redigest import load_pinned_targets
from scripts import download_jom_loa2027_pilot as previous

BATCH_SIZE = 9
BATCH_IDS = tuple(f"B{index:02d}" for index in range(1, 10))
# Checked against the 2026-10-10 SME Drive custodian folder; no remote Drive
# calls happen in the runner. Exact editions, never fuzzy name matching.
ALREADY_PRESERVED = frozenset({7208, 7209, 7210, 7211, 7212, 7294})
MAX_PER_PDF = 200 * 1024 * 1024
MAX_TOTAL = 500 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024

PilotStop = previous.PilotStop
NoRedirect = previous.NoRedirect


def batch_map() -> dict[str, list[dict]]:
    rows = load_pinned_targets()  # SHA-verified pinned 87 official URLs
    original_editions = {int(r["edition"]) for r in rows}
    if len(rows) != 87 or len(original_editions) != 87:
        raise PilotStop("STOP_PINNED_87_IDENTITY_DRIFT")
    if not ALREADY_PRESERVED.issubset(original_editions):
        raise PilotStop("STOP_PRESERVED_EXCLUSION_DRIFT")
    remaining = sorted(
        (r for r in rows if int(r["edition"]) not in ALREADY_PRESERVED),
        key=lambda row: int(row["edition"]),
    )
    if len(remaining) != 81:
        raise PilotStop("STOP_REMAINING_81_IDENTITY_DRIFT")
    if len({r["document_url"] for r in remaining}) != 81:
        raise PilotStop("STOP_DUPLICATE_URL")
    for row in remaining:
        u = urlparse(row["document_url"])
        if not (
            u.scheme == "https" and u.hostname == "ecrie.com.br"
            and u.path.startswith("/Sistema/Conteudos/DiarioOficial/upload/")
            and u.path.endswith(".pdf") and not u.query and not u.fragment
            and not u.username and not u.password
            and row["source_id"] == f"LIMEIRA_JO_{int(row['edition']):05d}"
        ):
            raise PilotStop("STOP_SOURCE_DRIFT")
    result = {key: remaining[i*BATCH_SIZE:(i+1)*BATCH_SIZE]
              for i, key in enumerate(BATCH_IDS)}
    if not all(len(rows) == 9 for rows in result.values()):
        raise PilotStop("STOP_BATCH_PARTITION")
    if set().union(*(set(int(r["edition"]) for r in rs) for rs in result.values())) != (
        original_editions - ALREADY_PRESERVED
    ):
        raise PilotStop("STOP_BATCH_COVERAGE")
    return result


def validate_manual_context(environment: dict, batch: str) -> None:
    if not (
        batch in BATCH_IDS
        and environment.get("JOM_2026_OWNER_CONFIRM") == "true"
        and environment.get("JOM_2026_BATCH") == batch
        and environment.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and environment.get("GITHUB_REF") == "refs/heads/main"
        and environment.get("GITHUB_RUN_ATTEMPT") == "1"
        and re.fullmatch(r"[a-f0-9]{40}", environment.get("GITHUB_SHA", ""))
    ):
        raise PilotStop("STOP_MANUAL_OWNER_BATCH_MAIN_CONTEXT_REQUIRED")


def collect_batch(out: Path, batch: str, *, transport=None) -> dict:
    if batch not in BATCH_IDS:
        raise PilotStop("STOP_INVALID_BATCH")
    sources = batch_map()[batch]  # preflight before any GET or persistence
    transport = transport or build_opener(NoRedirect())
    originals = out / "originals"
    originals.mkdir(parents=True, exist_ok=False)  # create-only locally
    statuses = []
    consumed_bytes = 0  # counts all bytes, even failed/invalid responses
    persisted_bytes = 0
    get_attempts = 0
    for row in sources:
        edition = int(row["edition"])
        item = {
            "edition": edition, "publication_date": row["publication_date"],
            "source_id": row["source_id"], "url": row["document_url"],
            "request_attempts": 0,
        }
        tmp = originals / f".JOM_{edition}.part"
        target = originals / f"JOM_{edition}_2026_ORIGINAL.pdf"
        try:
            if consumed_bytes >= MAX_TOTAL:
                raise PilotStop("STOP_TOTAL_BYTES_EXHAUSTED_BEFORE_GET")
            sha = hashlib.sha256()
            received = 0
            get_attempts += 1
            item["request_attempts"] = 1
            with transport.open(
                Request(row["document_url"],
                        headers={"User-Agent": "LOA-LIMEIRA-2027-JOM-Archive/1.0",
                                 "Accept": "application/pdf"},
                        method="GET"),
                timeout=35,
            ) as response:
                if response.geturl() != row["document_url"]:
                    raise PilotStop("STOP_FINAL_URL_DRIFT")
                mime = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                if mime not in ("application/pdf", "application/octet-stream"):
                    raise PilotStop("STOP_MIME")
                declared = response.headers.get("Content-Length")
                expected = int(declared) if declared is not None else None
                if expected is not None and (expected < 100 or expected > MAX_PER_PDF):
                    raise PilotStop("STOP_CONTENT_LENGTH_LIMIT")
                if expected is not None and expected + consumed_bytes > MAX_TOTAL:
                    raise PilotStop("STOP_TOTAL_DECLARED_LENGTH_LIMIT")
                with tmp.open("xb") as stream:
                    while True:
                        chunk = response.read(CHUNK_BYTES)
                        if not chunk:
                            break
                        consumed_bytes += len(chunk)
                        received += len(chunk)
                        if received > MAX_PER_PDF or consumed_bytes > MAX_TOTAL:
                            raise PilotStop("STOP_BYTE_BUDGET")
                        stream.write(chunk)
                        sha.update(chunk)
            if expected is not None and received != expected:
                raise PilotStop("STOP_TRUNCATED_CONTENT_LENGTH")
            if received < 100:
                if tmp.open("rb").read(5) != b"%PDF-":
                    raise PilotStop("STOP_NOT_PDF")
                raise PilotStop("STOP_TOO_FEW_BYTES")
            pages = previous.inspect_pdf(tmp, edition)
            tmp.rename(target)
            persisted_bytes += received
            item.update({"status": "VALIDATED_ORIGINAL", "bytes": received,
                         "sha256": sha.hexdigest(), "pages": pages,
                         "file_name": target.name, "cover_edition_verified": True})
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            item.update({
                "status": "SOURCE_OR_VALIDATION_FAILED",
                "code": str(exc) if isinstance(exc, PilotStop) else type(exc).__name__,
                "no_source_absence_inference": True,
            })
        statuses.append(item)
    valid = sum(d["status"] == "VALIDATED_ORIGINAL" for d in statuses)
    result = {
        "schema": "LOA2027_JOM_2026_BATCH_9_ORIGINALS_V1",
        "status": "PASS_9_VALIDATED" if valid == 9 else "PARTIAL_STOP_REVIEW_FAILURES",
        "batch": batch,
        "batch_ids": list(BATCH_IDS),
        "requested_count": 9, "validated_count": valid,
        "failed_count": 9-valid, "source_get_attempts": get_attempts,
        "retry_count": 0, "index_get_count": 0, "drive_read_count": 0,
        "drive_write_count": 0, "publication_count": 0,
        "bytes_transferred_including_failed": consumed_bytes,
        "bytes_archived": persisted_bytes,
        "artifact_not_permanent_custody": True,
        "no_absence_inference": True,
        "excluded_already_in_sme": sorted(ALREADY_PRESERVED),
        "github_sha": os.getenv("GITHUB_SHA", "LOCAL_OFFLINE_TEST"),
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
    validate_manual_context(os.environ, args.batch)
    result = collect_batch(args.out, args.batch)
    print(json.dumps({
        "batch": args.batch, "status": result["status"],
        "validated": result["validated_count"], "failed": result["failed_count"],
        "source_get_attempts": result["source_get_attempts"]
    }, sort_keys=True))
    return 0 if result["validated_count"] == 9 else 2


if __name__ == "__main__":
    raise SystemExit(main())
