"""TASK 285: deterministic, offline-only pilot queue for Limeira JOM budget acts.

No public-source GET, PDF acquisition, Drive, workflow dispatch, or publication.
This is a manifest builder, not permission to download its source URLs.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
PINNED_TARGETS = (
    ROOT / "docs/evidence/fixtures/task219/"
    "TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv"
)
PILOT_EDITIONS = (7211, 7208, 7209, 7210, 7212)
TARGET_COUNT = 87
ALLOWED_HOST = "ecrie.com.br"
ALLOWED_PATH_PREFIX = "/Sistema/Conteudos/DiarioOficial/upload/"


class Task285Stop(RuntimeError):
    """Inconsistent pinned evidence; stop without a network effect."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task285Stop(code)


def build_pilot_queue(csv_text: str | None = None) -> dict:
    """Read pinned fixture and emit five exact already-declared URLs.

    The sole documented budget target in this pilot is edition 7211,
    where the official legislation index identifies Decree 62/2026, page 5.
    Neighboring editions are *screening candidates*, not budget-act proof.
    """
    if csv_text is None:
        csv_text = PINNED_TARGETS.read_text(encoding="utf-8")

    reader = csv.DictReader(io.StringIO(csv_text))
    required = ("edition", "publication_date", "source_id", "document_url")
    _require(tuple(reader.fieldnames or ()) == required, "STOP_FIXTURE_SCHEMA")
    rows = list(reader)
    _require(len(rows) == TARGET_COUNT, "STOP_FIXTURE_ROW_COUNT")
    by_edition: dict[int, dict] = {}

    for item in rows:
        try:
            edition = int(item["edition"])
            day = date.fromisoformat(item["publication_date"])
        except (TypeError, ValueError) as exc:
            raise Task285Stop("STOP_EDITION_OR_DATE_FORMAT") from exc
        _require(edition > 0 and edition not in by_edition, "STOP_DUPLICATE_EDITION")
        _require(day.year == 2026, "STOP_YEAR_OUT_OF_SCOPE")
        _require(item["source_id"] == f"LIMEIRA_JO_{edition:05d}", "STOP_SOURCE_ID")

        url = item["document_url"]
        parsed = urlparse(url)
        _require(
            parsed.scheme == "https"
            and parsed.netloc == ALLOWED_HOST
            and parsed.path.startswith(ALLOWED_PATH_PREFIX)
            and parsed.path.endswith(".pdf")
            and not parsed.params
            and not parsed.query
            and not parsed.fragment
            and not parsed.username
            and not parsed.password,
            "STOP_UNTRUSTED_PDF_ROUTE",
        )
        by_edition[edition] = item

    selection = []
    for edition in PILOT_EDITIONS:
        _require(edition in by_edition, "STOP_PILOT_EDITION_MISSING")
        row = by_edition[edition]
        _require(row["publication_date"].startswith("2026-03-"), "STOP_PILOT_DATE")
        selection.append(
            {
                "edition": edition,
                "publication_date": row["publication_date"],
                "source_id": row["source_id"],
                "document_url": row["document_url"],
                "budget_act_confirmed_by_index": edition == 7211,
                "act_reference": (
                    "Decreto Municipal 62/2026 — JOM 7211, p. 5"
                    if edition == 7211 else None
                ),
                "target_annexes": ["I", "II"] if edition == 7211 else [],
                "pdf_content_inspected": False,
                "budget_line_extracted": False,
                "authorization_state": "NOT_AUTHORIZED_TO_DOWNLOAD",
            }
        )

    return {
        "schema": "TASK285_JOM_BUDGET_PILOT_QUEUE_V1",
        "status": "READY_FOR_SEPARATE_T1_GATE",
        "source": "TASK219A_PINNED_87",
        "pinned_document_count": len(rows),
        "pilot_document_count": len(selection),
        "official_urls_guessed": 0,
        "network_request_count": 0,
        "pdf_download_count": 0,
        "drive_write_count": 0,
        "publication_count": 0,
        "retries_authorized": False,
        "recurrence_authorized": False,
        "live_execution_authorized": False,
        "download_gate_required": True,
        "custody_gate_required": True,
        "absence_inference_allowed": False,
        "documents": selection,
    }
