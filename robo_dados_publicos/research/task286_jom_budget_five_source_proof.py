"""TASK286: bounded JOM budget PDF source-proof runner.

The default operation is offline/blocked. A future owner-approved, SHA-pinned
T1 invocation may call the official source once per pinned edition. Never
persists a raw PDF, page text or budget record.
"""
from __future__ import annotations

import hashlib
import io
from typing import Any, Protocol
from urllib.parse import urlparse

from pypdf import PdfReader

from robo_dados_publicos.research.task219a_jom_general_event_redigest import (
    load_pinned_targets,
)

PILOT = (7211, 7208, 7209, 7210, 7212)
MAX_PER_PDF = 200 * 1024 * 1024
MAX_TOTAL = 500 * 1024 * 1024
REQUIRED_CONSENT = "TASK286_APPROVE_5_EXACT_PDFS_SOURCE_READ_ONLY_NO_CUSTODY"


class Task286Stop(RuntimeError):
    pass


class DocumentSource(Protocol):
    network_capable: bool

    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict[str, Any]]: ...


def select_pinned_pilot() -> list[dict[str, Any]]:
    """Reuse the repository's already SHA-validated 87-file source fixture."""
    by_edition = {int(x["edition"]): x for x in load_pinned_targets()}
    if not all(number in by_edition for number in PILOT):
        raise Task286Stop("STOP_PILOT_SOURCE_MISSING")
    selected = [by_edition[n] for n in PILOT]
    for row in selected:
        u = urlparse(row["document_url"])
        if (
            u.scheme != "https"
            or u.hostname != "ecrie.com.br"
            or not u.path.startswith("/Sistema/Conteudos/DiarioOficial/upload/")
            or not u.path.endswith(".pdf")
            or u.query or u.fragment or u.username or u.password
            or row["source_id"] != f"LIMEIRA_JO_{int(row['edition']):05d}"
        ):
            raise Task286Stop("STOP_PILOT_SOURCE_URL_OR_ID_DRIFT")
    return selected


def validate_t1_gate(
    authorization: dict[str, Any] | None,
    *,
    implementation_sha: str,
    offline_test_mode: bool,
    source: DocumentSource,
) -> None:
    if offline_test_mode:
        if source.network_capable:
            raise Task286Stop("STOP_FAKE_SOURCE_REQUIRED")
        return
    if not source.network_capable:
        raise Task286Stop("STOP_NETWORK_SOURCE_REQUIRED")
    if (
        not authorization
        or authorization.get("consent") != REQUIRED_CONSENT
        or authorization.get("implementation_sha") != implementation_sha
        or len(implementation_sha) != 40
        or any(c not in "0123456789abcdef" for c in implementation_sha)
        or authorization.get("exact_editions") != list(PILOT)
        or authorization.get("max_document_gets") != 5
        or authorization.get("max_aggregate_bytes") != MAX_TOTAL
        or authorization.get("owner_authorized") is not True
        or authorization.get("no_retry") is not True
        or authorization.get("drive_write_allowed") is not False
        or authorization.get("pdf_artifact_persist_allowed") is not False
        or authorization.get("publication_allowed") is not False
    ):
        raise Task286Stop("STOP_UNAUTHORIZED_T1")


def execute_pilot(
    source: DocumentSource,
    *,
    authorization: dict[str, Any] | None = None,
    implementation_sha: str = "",
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    """One exact GET per document; no index GET, retries, raw-file storage.

    A PDF is validated by its signature, parser, page count and source URL.
    Failed document means STOP; the result of successful documents before
    failure is not promoted into an exhaustive inventory.
    """
    records = select_pinned_pilot()
    validate_t1_gate(
        authorization, implementation_sha=implementation_sha,
        offline_test_mode=offline_test_mode, source=source,
    )
    results = []
    total_bytes = 0
    for item in records:
        data, meta = source.get(item["document_url"], MAX_PER_PDF)
        if not isinstance(data, bytes) or not (5 <= len(data) <= MAX_PER_PDF):
            raise Task286Stop("STOP_PDF_BYTES_LIMIT")
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL:
            raise Task286Stop("STOP_TOTAL_PDF_BYTES_LIMIT")
        if not data.startswith(b"%PDF-"):
            raise Task286Stop("STOP_PDF_SIGNATURE")
        if (
            meta.get("https") is not True
            or meta.get("final_host") != "ecrie.com.br"
            or meta.get("remote_get_count") != 1
            or meta.get("content_type") not in ("application/pdf", "application/octet-stream")
        ):
            raise Task286Stop("STOP_SOURCE_RESPONSE_IDENTITY")
        try:
            pdf = PdfReader(io.BytesIO(data), strict=True)
            pages = len(pdf.pages)
        except Exception as exc:
            raise Task286Stop("STOP_PDF_PARSE") from exc
        if pages < 1:
            raise Task286Stop("STOP_EMPTY_PDF")
        results.append({
            "edition": item["edition"],
            "publication_date": item["publication_date"],
            "source_id": item["source_id"],
            "source_url": item["document_url"],
            "bytes": len(data),
            "pages": pages,
            "sha256": hashlib.sha256(data).hexdigest(),
            "budget_annex_extracted": False,
            "source_edition_print_verified": False,
            "raw_pdf_persisted": False,
            "source_proof_only": True,
        })
    if len(results) != 5:
        raise Task286Stop("STOP_INCOMPLETE_PILOT")
    return {
        "schema": "TASK286_JOM_BUDGET_FIVE_PDF_SOURCE_PROOF_V1",
        "status": "PASS_SOURCE_PDF_INTEGRITY_ONLY_NOT_ARCHIVED",
        "source_get_count": len(results),
        "index_get_count": 0,
        "aggregate_bytes": total_bytes,
        "pdf_persisted_count": 0,
        "drive_write_count": 0,
        "publication_count": 0,
        "annex_I_II_verified": False,
        "budget_lines_extracted": 0,
        "absence_inference_allowed": False,
        "needs_separate_T2_custody_gate": True,
        "results": results,
    }
