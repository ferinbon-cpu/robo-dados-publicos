from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlparse


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class JournalProcessingGate:
    version: int
    gate: str
    source_id: str
    edition: int
    publication_date: str
    source_url: str
    source_sha256: str
    source_bytes: int
    extractor: str
    extractor_version: str
    output_prefix: str
    expected_pages: int
    expected_total_extracted_chars: int
    expected_gold_events: int
    expected_rag_chunks: int
    expected_reconciliation_tasks: int

    @classmethod
    def from_mapping(cls, data: dict) -> "JournalProcessingGate":
        required = {
            "version", "gate", "source_id", "edition", "publication_date",
            "source_url", "source_sha256", "source_bytes", "extractor",
            "extractor_version", "output_prefix",
            "expected_pages", "expected_total_extracted_chars",
            "expected_gold_events", "expected_rag_chunks",
            "expected_reconciliation_tasks",
        }
        missing = sorted(required - set(data))
        if missing:
            raise ValueError("PROCESSING_GATE_MISSING_FIELDS: " + ", ".join(missing))
        gate = cls(**{key: data[key] for key in required})
        gate.validate()
        return gate

    def validate(self) -> None:
        if self.version != 1:
            raise ValueError("PROCESSING_GATE_VERSION_UNSUPPORTED")
        if self.gate != "M4E_FIRST_SOURCE_PROCESSING_GATE":
            raise ValueError("PROCESSING_GATE_NAME_INVALID")
        if not self.source_id.strip():
            raise ValueError("PROCESSING_SOURCE_ID_REQUIRED")
        if int(self.edition) <= 0:
            raise ValueError("PROCESSING_EDITION_INVALID")
        try:
            date.fromisoformat(self.publication_date)
        except ValueError as exc:
            raise ValueError("PROCESSING_PUBLICATION_DATE_INVALID") from exc
        parsed = urlparse(self.source_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("PROCESSING_SOURCE_URL_HTTPS_REQUIRED")
        if not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("PROCESSING_SOURCE_SHA256_INVALID")
        if int(self.source_bytes) <= 0:
            raise ValueError("PROCESSING_SOURCE_BYTES_INVALID")
        if self.extractor != "pypdf":
            raise ValueError("PROCESSING_EXTRACTOR_INVALID")
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", self.extractor_version):
            raise ValueError("PROCESSING_EXTRACTOR_VERSION_INVALID")
        if not re.fullmatch(r"[A-Z0-9_]+", self.output_prefix):
            raise ValueError("PROCESSING_OUTPUT_PREFIX_INVALID")
        metrics = (
            self.expected_pages,
            self.expected_total_extracted_chars,
            self.expected_gold_events,
            self.expected_rag_chunks,
            self.expected_reconciliation_tasks,
        )
        if any(int(value) < 0 for value in metrics) or int(self.expected_pages) == 0:
            raise ValueError("PROCESSING_EXPECTED_METRICS_INVALID")

    def expected_metrics(self) -> dict:
        return {
            "pages": int(self.expected_pages),
            "total_extracted_chars": int(self.expected_total_extracted_chars),
            "gold_events": int(self.expected_gold_events),
            "rag_chunks": int(self.expected_rag_chunks),
            "reconciliation_tasks": int(self.expected_reconciliation_tasks),
        }


def load_journal_processing_gate(path: str | Path) -> JournalProcessingGate:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("PROCESSING_GATE_OBJECT_REQUIRED")
    return JournalProcessingGate.from_mapping(data)
