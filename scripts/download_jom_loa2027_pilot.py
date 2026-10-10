"""Manual, five-document JOM 2026 original-PDF acquisition to GitHub artifact.

Distinct from TASK219A event redigest. Manual dispatch on protected main only.
No Drive connection, credentials, retries, search, pagination, or recurrence.
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
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pypdf import PdfReader

# GitHub Actions invokes 'python scripts/...'; make repository imports explicit.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.research.task219a_jom_general_event_redigest import (
    load_pinned_targets,
)

EDITIONS = (7211, 7208, 7209, 7210, 7212)
MAX_PER_PDF = 200 * 1024 * 1024
MAX_TOTAL = 500 * 1024 * 1024
SOURCE_HOST = "ecrie.com.br"
SOURCE_PREFIX = "/Sistema/Conteudos/DiarioOficial/upload/"
CHUNK_BYTES = 1024 * 1024


class PilotStop(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise PilotStop("STOP_REDIRECT_NOT_PREAUTHORIZED")


def exact_sources() -> list[dict]:
    """Reuse the 87 originals, hash-verified by the existing TASK219A loader."""
    all_rows = load_pinned_targets()
    by_id = {int(x["edition"]): x for x in all_rows}
    if not all(n in by_id for n in EDITIONS):
        raise PilotStop("STOP_PINNED_EDITION_MISSING")
    rows = [by_id[n] for n in EDITIONS]
    if len({x["document_url"] for x in rows}) != len(EDITIONS):
        raise PilotStop("STOP_DUPLICATE_SOURCE_URL")
    for r in rows:
        u = urlparse(r["document_url"])
        n = int(r["edition"])
        if not (
            u.scheme == "https"
            and u.hostname == SOURCE_HOST
            and u.path.startswith(SOURCE_PREFIX)
            and u.path.lower().endswith(".pdf")
            and not u.query and not u.fragment
            and not u.username and not u.password
            and r["source_id"] == f"LIMEIRA_JO_{n:05d}"
        ):
            raise PilotStop("STOP_SOURCE_IDENTITY_DRIFT")
    return rows


def validate_manual_context(environment: dict) -> None:
    if not (
        environment.get("JOM_OWNER_CONFIRM") == "true"
        and environment.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
        and environment.get("GITHUB_REF") == "refs/heads/main"
        and environment.get("GITHUB_RUN_ATTEMPT") == "1"
        and re.fullmatch(r"[0-9a-f]{40}", environment.get("GITHUB_SHA", ""))
    ):
        raise PilotStop("STOP_MANUAL_OWNER_MAIN_CONTEXT_REQUIRED")


def inspect_pdf(path: Path, edition: int) -> int:
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise PilotStop("STOP_NOT_PDF")
        stream.seek(0)
        try:
            doc = PdfReader(stream, strict=False)
            count = len(doc.pages)
            if not 0 < count <= 2500:
                raise PilotStop("STOP_PAGE_COUNT")
            # Edition is printed on the cover or early header, not inferred
            # from URL alone. If extraction is impossible, fail that file.
            front = " ".join(
                (doc.pages[i].extract_text() or "")
                for i in range(min(count, 2))
            )
        except PilotStop:
            raise
        except Exception as exc:
            raise PilotStop("STOP_PDF_PARSER") from exc
    if not re.search(rf"(?<!\d){edition}(?!\d)", front):
        raise PilotStop("STOP_COVER_EDITION_NOT_VERIFIED")
    return count


def collect_pilot(out: Path, *, transport=None) -> dict:
    """Exactly one GET each; successful PDFs may be retained on partial failure.

    No negative inference from source unavailability. A failure is recorded;
    it does not cause an automatic retry.
    """
    rows = exact_sources()
    transport = transport or build_opener(NoRedirect())
    originals = out / "originals"
    originals.mkdir(parents=True, exist_ok=True)
    statuses = []
    total = 0
    for source in rows:
        edition = int(source["edition"])
        target = originals / f"JOM_{edition}_2026_ORIGINAL.pdf"
        partial = originals / f".JOM_{edition}.part"
        sha = hashlib.sha256()
        received = 0
        item = {
            "edition": edition,
            "date": source["publication_date"],
            "url": source["document_url"],
            "source_id": source["source_id"],
            "request_attempts": 1,
        }
        try:
            with transport.open(
                Request(
                    source["document_url"],
                    headers={"User-Agent": "LOA-LIMEIRA-2027-JOM-Research/1.0", "Accept": "application/pdf"},
                    method="GET",
                ), timeout=35,
            ) as response:
                final = response.geturl()
                parsed = urlparse(final)
                if final != source["document_url"] or parsed.hostname != SOURCE_HOST:
                    raise PilotStop("STOP_FINAL_URL_DRIFT")
                mime = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                if mime not in ("application/pdf", "application/octet-stream"):
                    raise PilotStop("STOP_RESPONSE_MIME")
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_PER_PDF:
                    raise PilotStop("STOP_CONTENT_LENGTH_LIMIT")
                with partial.open("xb") as dst:
                    while True:
                        chunk = response.read(CHUNK_BYTES)
                        if not chunk:
                            break
                        received += len(chunk)
                        if received > MAX_PER_PDF or received + total > MAX_TOTAL:
                            raise PilotStop("STOP_BYTE_BUDGET")
                        sha.update(chunk)
                        dst.write(chunk)
            if received < 100:
                raise PilotStop("STOP_TOO_FEW_BYTES")
            pages = inspect_pdf(partial, edition)
            partial.rename(target)
            total += received
            item.update({
                "status": "VALIDATED_ORIGINAL",
                "bytes": received,
                "sha256": sha.hexdigest(),
                "pages": pages,
                "file_name": target.name,
                "cover_edition_verified": True,
            })
        except Exception as exc:
            partial.unlink(missing_ok=True)
            # Errors are explicit; never claim a missing PDF is absent at source.
            item.update({
                "status": "SOURCE_OR_VALIDATION_FAILED",
                "code": str(exc) if isinstance(exc, PilotStop) else type(exc).__name__,
                "bytes_confirmed": 0,
                "no_absence_inference": True,
            })
        statuses.append(item)
    success = sum(x["status"] == "VALIDATED_ORIGINAL" for x in statuses)
    result = {
        "schema": "LOA2027_JOM_PILOT_ORIGINALS_GITHUB_ARTIFACT_V1",
        "status": "PASS_5_VALIDATED" if success == 5 else "PARTIAL_STOP_REVIEW_FAILURES",
        "requested_count": 5,
        "validated_count": success,
        "failed_count": 5 - success,
        "bytes_archived": total,
        "source_get_attempts": 5,
        "retry_count": 0,
        "index_get_count": 0,
        "drive_write_count": 0,
        "publication_count": 0,
        "absence_inference_allowed": False,
        "pdfs_are_originals_not_budget_analysis": True,
        "github_sha": os.getenv("GITHUB_SHA", "LOCAL_TEST"),
        "documents": statuses,
    }
    (out / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--out", type=Path, required=True)
    parsed = args.parse_args()
    validate_manual_context(os.environ)
    result = collect_pilot(parsed.out)
    print(json.dumps({
        "status": result["status"],
        "validated_count": result["validated_count"],
        "failed_count": result["failed_count"],
        "artifact_bytes": result["bytes_archived"],
    }, sort_keys=True))
    return 0 if result["validated_count"] == 5 else 2


if __name__ == "__main__":
    raise SystemExit(main())
