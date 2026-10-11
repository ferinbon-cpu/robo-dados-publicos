"""TASK292A: recover 5 already-proven JOM 2026 PDFs; bounded manual source GET.

Data authority: TASK238 primary probe (7151) + TASK248 canonical rolling
discovery (7321..7324), NOT numerical edition inference or guessed URLs.
Never write Drive or publish. Artifact chunks are reversible, <= 90 MiB.
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

PRIMARY = ROOT / "docs/evidence/TASK_238_JOM_PRIMARY_CONTENT_CLOSURE_0.8.0.json"
DELTA = ROOT / "docs/evidence/TASK_248_JOM_LIVE_DELTA_CANONICAL_0.8.0.json"
EDITIONS = (7151, 7321, 7322, 7323, 7324)
SOURCE_PREFIX = "/Sistema/Conteudos/DiarioOficial/upload/"
MAX_PER_PDF = 200 * 1024 * 1024
MAX_TOTAL = 500 * 1024 * 1024
SEGMENT_BYTES = 90 * 1024 * 1024
READ_BYTES = 1024 * 1024
KNOWN_7151_SHA = "ec298a6cff290723c97d24c291e36ef2c2044713b0fc5082b4560329e1d1dab8"
KNOWN_7151_SIZE = 44002985
KNOWN_7151_PAGES = 125


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(READ_BYTES), b""):
            h.update(chunk)
    return h.hexdigest()


def exact_sources() -> list[dict]:
    p = json.loads(PRIMARY.read_text("utf-8"))
    d = json.loads(DELTA.read_text("utf-8"))
    if (p.get("task") != "TASK_238"
        or p.get("runtime", {}).get("status") != "PASS_PROBE_ALL_TARGETS_INSPECTED"):
        raise PilotStop("STOP_292A_TASK238_PROVENANCE")
    p7151 = next((r for r in p["primary_inspections"] if r["edition"] == 7151), None)
    if not p7151 or (p7151["sha256"], p7151["bytes"], p7151["pdf_page_count"]) != (
        KNOWN_7151_SHA, KNOWN_7151_SIZE, KNOWN_7151_PAGES
    ) or p7151["publication_date"] != "2026-01-06":
        raise PilotStop("STOP_292A_7151_PRIMARY_DRIFT")
    if (d.get("status") != "PASS_TASK247_LIVE_DELTA_CANONIZED"
        or d.get("live_result", {}).get("delta_count") != 4
        or d.get("interpretation", {}).get("pdf_content_proven") is not False):
        raise PilotStop("STOP_292A_TASK248_PROVENANCE")
    delta = d["live_result"]["delta_editions"]
    if tuple(int(r["edition"]) for r in delta) != EDITIONS[1:]:
        raise PilotStop("STOP_292A_FOUR_EDITION_DRIFT")
    rows = [{
        "edition": 7151,
        "publication_date": p7151["publication_date"],
        "source_id": None,  # not stated by TASK238 primary inspection
        "document_url": p7151["document_url"],
        "historical_sha256": KNOWN_7151_SHA,
        "historical_bytes": KNOWN_7151_SIZE,
        "historical_pages": KNOWN_7151_PAGES,
        "provenance": "TASK238_PRIMARY_INSPECTION",
    }]
    for r in delta:
        rows.append({
            "edition": int(r["edition"]),
            "publication_date": r["publication_date"],
            "source_id": r["source_id"],
            "document_url": r["document_url"],
            "historical_sha256": None,
            "historical_bytes": None,
            "historical_pages": None,
            "provenance": "TASK248_OFFICIAL_INDEX_DELTA",
        })
    if len(rows) != 5 or len({r["document_url"] for r in rows}) != 5:
        raise PilotStop("STOP_292A_SOURCE_CARDINALITY")
    for r in rows:
        u = urlparse(r["document_url"])
        if not (u.scheme == "https" and u.hostname == "ecrie.com.br"
                and u.path.startswith(SOURCE_PREFIX)
                and u.path.endswith(".pdf")
                and not u.query and not u.fragment and not u.username and not u.password):
            raise PilotStop("STOP_292A_URL_DRIFT")
        if (r["edition"] != 7151 and
            r["source_id"] != f"LIMEIRA_JO_{r['edition']:05d}"):
            raise PilotStop("STOP_292A_SOURCE_ID_DRIFT")
    return rows


def validate_context(env: dict) -> None:
    if not (
        env.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and env.get("GITHUB_REF") == "refs/heads/main"
        and env.get("GITHUB_RUN_ATTEMPT") == "1"
        and env.get("JOM292A_OWNER_CONFIRM") == "true"
        and re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))
    ):
        raise PilotStop("STOP_292A_MANUAL_OWNER_MAIN_ONE_SHOT")


def split_verified(original: Path, root: Path, row: dict, file_sha: str,
                   pages: int) -> list[dict]:
    edition = row["edition"]
    size = original.stat().st_size
    parts = (size + SEGMENT_BYTES - 1) // SEGMENT_BYTES
    if not 1 <= parts <= 3:
        raise PilotStop("STOP_292A_PART_COUNT")
    items = []
    with original.open("rb") as fp:
        for n in range(1, parts + 1):
            dst_dir = root / str(edition) / f"part{n:02d}"
            dst_dir.mkdir(parents=True, exist_ok=False)
            name = (f"JOM_{edition}_2026_ORIGINAL.pdf" if parts == 1
                    else f"JOM_{edition}_2026_ORIGINAL.pdf.part{n:02d}")
            chunk = fp.read(SEGMENT_BYTES)
            if not chunk or len(chunk) > SEGMENT_BYTES:
                raise PilotStop("STOP_292A_SEGMENT_SIZE")
            digest = hashlib.sha256(chunk).hexdigest()
            payload = dst_dir / name
            with payload.open("xb") as out:
                out.write(chunk)
            if sha_file(payload) != digest:
                raise PilotStop("STOP_292A_SEGMENT_READBACK")
            excerpt = {
                "schema": "TASK292A_JOM_2026_REVERSIBLE_PDF_SEGMENT_V1",
                "edition": edition,
                "publication_date": row["publication_date"],
                "source_url": row["document_url"],
                "source_provenance": row["provenance"],
                "source_id": row["source_id"],
                "original_filename": f"JOM_{edition}_2026_ORIGINAL.pdf",
                "original_size": size,
                "original_sha256": file_sha,
                "original_pages": pages,
                "parts_total": parts,
                "part_number": n,
                "part_file": name,
                "part_bytes": len(chunk),
                "part_sha256": digest,
                "reconstruction": "concatenate original part bytes in part_number ascending order",
                "github_actions_transient_not_permanent_drive_custody": True,
            }
            (dst_dir / "manifest_excerpt.json").write_text(
                json.dumps(excerpt, sort_keys=True, indent=2) + "\n", "utf-8")
            items.append({"part_number": n, "file_name": name, "bytes": len(chunk),
                          "sha256": digest})
        if fp.read(1):
            raise PilotStop("STOP_292A_TRAILING_UNSPLIT_DATA")
    if sum(x["bytes"] for x in items) != size:
        raise PilotStop("STOP_292A_RECONSTRUCT_SIZE")
    return items


def collect(out: Path, *, transport=None) -> dict:
    rows = exact_sources()  # exact-source provenance gate before network
    if out.exists():
        raise PilotStop("STOP_292A_OUTPUT_EXISTS")
    out.mkdir(parents=True)
    working = out / "_working"
    working.mkdir()
    transport = transport or build_opener(NoRedirect())
    statuses = []
    consumed = 0
    validated_bytes = 0
    attempts = 0
    for row in rows:
        ed = row["edition"]
        tmp = working / f".JOM_{ed}.incoming"
        item = {
            "edition": ed, "publication_date": row["publication_date"],
            "source_id": row["source_id"], "source_url": row["document_url"],
            "source_provenance": row["provenance"], "request_attempts": 0,
        }
        try:
            if consumed >= MAX_TOTAL:
                raise PilotStop("STOP_292A_GLOBAL_BUDGET_BEFORE_GET")
            sha = hashlib.sha256()
            received = 0
            attempts += 1
            item["request_attempts"] = 1
            with transport.open(
                Request(row["document_url"],
                        headers={"User-Agent": "LOA-LIMEIRA-2027-JOM-Archive/1.0",
                                 "Accept": "application/pdf"}, method="GET"),
                timeout=35,
            ) as response:
                if response.geturl() != row["document_url"]:
                    raise PilotStop("STOP_292A_FINAL_URL_DRIFT")
                mime = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                if mime not in ("application/pdf", "application/octet-stream"):
                    raise PilotStop("STOP_292A_MIME")
                head_length = response.headers.get("Content-Length")
                declared = int(head_length) if head_length else None
                if declared is not None and (
                    declared < 100 or declared > MAX_PER_PDF
                    or declared + consumed > MAX_TOTAL
                ):
                    raise PilotStop("STOP_292A_DECLARED_LENGTH")
                with tmp.open("xb") as dst:
                    while True:
                        chunk = response.read(READ_BYTES)
                        if not chunk:
                            break
                        received += len(chunk)
                        consumed += len(chunk)
                        if received > MAX_PER_PDF or consumed > MAX_TOTAL:
                            raise PilotStop("STOP_292A_BYTE_BUDGET")
                        sha.update(chunk)
                        dst.write(chunk)
            if declared is not None and declared != received:
                raise PilotStop("STOP_292A_TRUNCATED")
            if received < 100 or tmp.open("rb").read(5) != b"%PDF-":
                raise PilotStop("STOP_292A_NOT_PDF")
            pages = inspect_pdf(tmp, ed)
            digest = sha.hexdigest()
            if row["historical_sha256"] and (
                digest != row["historical_sha256"]
                or received != row["historical_bytes"]
                or pages != row["historical_pages"]
            ):
                raise PilotStop("STOP_292A_HISTORICAL_7151_HASH_SIZE_PAGES")
            parts = split_verified(tmp, out / "pieces", row, digest, pages)
            validated_bytes += received
            item.update({"status": "VALIDATED_ORIGINAL", "bytes": received,
                         "sha256": digest, "pages": pages, "parts": parts,
                         "cover_edition_verified": True})
        except Exception as exc:
            item.update({"status": "SOURCE_OR_VALIDATION_FAILED",
                         "code": str(exc) if isinstance(exc, PilotStop) else type(exc).__name__,
                         "no_source_absence_inference": True})
            # Quarantine/remove any incomplete segments on failure; never
            # permit a failed document to have a successful artifact.
            import shutil
            shutil.rmtree(out / "pieces" / str(ed), ignore_errors=True)
        finally:
            tmp.unlink(missing_ok=True)
        statuses.append(item)
    working.rmdir()
    count = sum(x["status"] == "VALIDATED_ORIGINAL" for x in statuses)
    result = {
        "schema": "TASK292A_FIVE_OFFICIAL_JOM_2026_ORIGINALS_V1",
        "status": "PASS_5_VALIDATED" if count == 5 else "PARTIAL_STOP_REVIEW_FAILURES",
        "expected_editions": list(EDITIONS),
        "requested_count": 5, "validated_count": count,
        "failed_count": 5 - count, "source_get_attempts": attempts,
        "retry_count": 0, "index_get_count": 0, "robots_get_count": 0,
        "source_bytes_consumed": consumed, "validated_original_bytes": validated_bytes,
        "drive_read_count": 0, "drive_write_count": 0, "publication_count": 0,
        "artifact_not_drive_custody": True, "source_absence_inference_allowed": False,
        "github_sha": os.getenv("GITHUB_SHA", "OFFLINE_TEST"),
        "documents": statuses,
    }
    (out / "manifest.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    validate_context(os.environ)
    result = collect(args.out)
    print(json.dumps({"status": result["status"],
                      "validated_count": result["validated_count"],
                      "source_get_attempts": result["source_get_attempts"],
                      "index_get_count": 0, "drive_write_count": 0}, sort_keys=True))
    return 0 if result["validated_count"] == 5 else 2


if __name__ == "__main__":
    raise SystemExit(main())
