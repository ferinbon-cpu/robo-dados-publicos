from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import mimetypes
import tempfile

from robo_dados_publicos.connectors.http_source import HttpSourceConnector
from robo_dados_publicos.state.registry import StateRegistry
from robo_dados_publicos.sources.inventory import SourceInventory, SourceSpec
from robo_dados_publicos.release import USER_AGENT


def _now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _normalize_content_type(value: str | None) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


class SourceCollector:
    """Deterministic acquisition layer.

    Acquisition is kept separate from transformation. New payloads are written
    to Bronze under immutable hash-qualified names. HTTP validators are stored
    in the persistent state database so subsequent runs can use conditional GET.
    """

    def __init__(self, drive, bronze_id: str, quarantine_id: str, http=None):
        self.drive = drive
        self.bronze_id = bronze_id
        self.quarantine_id = quarantine_id
        self.http = http or HttpSourceConnector(user_agent=USER_AGENT)

    @staticmethod
    def _remote_name(spec: SourceSpec, digest: str, stamp: str | None = None) -> str:
        p = Path(spec.file_name)
        suffix = "".join(p.suffixes)
        stem = p.name[:-len(suffix)] if suffix else p.name
        stamp = stamp or _now_compact()
        return f"{spec.source_id}__{stem}__{stamp}__{digest[:12]}{suffix}"

    @staticmethod
    def _mime(spec: SourceSpec, observed: str | None) -> str:
        ctype = _normalize_content_type(observed)
        if ctype:
            return ctype
        return mimetypes.guess_type(spec.file_name)[0] or "application/octet-stream"

    @staticmethod
    def _validate_content_type(spec: SourceSpec, observed: str | None) -> tuple[bool, str]:
        observed_norm = _normalize_content_type(observed)
        if not spec.expected_content_types:
            return True, observed_norm
        return observed_norm in spec.expected_content_types, observed_norm

    def collect_inventory(self, inventory: SourceInventory, state: StateRegistry, *, dry_run: bool = False) -> dict:
        if dry_run:
            planned = [s.source_id for s in inventory.enabled]
            return {
                "status": "DRY_RUN",
                "inventory": inventory.summary(),
                "planned_sources": planned,
                "network": "NOT_CALLED",
                "writes": "NONE",
            }

        if not inventory.enabled:
            return {
                "status": "NO_ENABLED_SOURCES",
                "inventory": inventory.summary(),
                "results": [],
            }

        results = []
        overall = "PASS"
        for spec in inventory.enabled:
            try:
                result = self.collect_one(spec, state)
            except Exception as exc:
                result = {
                    "source_id": spec.source_id,
                    "status": "STOP_SOURCE_ERROR",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                state.upsert_source_state(
                    spec.source_id, spec.url, last_status="STOP_SOURCE_ERROR"
                )
                state.event("SOURCE_COLLECTION_ERROR", result)
            results.append(result)
            if str(result.get("status", "")).startswith("STOP_"):
                overall = "STOP_SOURCE_COLLECTION"

        return {
            "status": overall,
            "inventory": inventory.summary(),
            "results": results,
        }

    def collect_one(self, spec: SourceSpec, state: StateRegistry) -> dict:
        previous = state.get_source_state(spec.source_id) or {}
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / spec.file_name
            fetched = self.http.download(
                spec.url,
                local,
                etag=previous.get("etag"),
                last_modified=previous.get("last_modified"),
            )

            if fetched.status == "NOT_MODIFIED":
                state.upsert_source_state(
                    spec.source_id,
                    spec.url,
                    etag=previous.get("etag"),
                    last_modified=previous.get("last_modified"),
                    last_sha256=previous.get("last_sha256"),
                    last_status="NOT_MODIFIED",
                    remote_file_id=previous.get("remote_file_id"),
                )
                result = {
                    "source_id": spec.source_id,
                    "status": "NOT_MODIFIED",
                    "http_status": 304,
                    "sha256": previous.get("last_sha256"),
                }
                state.event("SOURCE_NOT_MODIFIED", result)
                return result

            ok_type, observed_type = self._validate_content_type(spec, fetched.content_type)
            if not ok_type:
                qname = self._remote_name(spec, fetched.sha256 or "unknown")
                uploaded = self.drive.put(
                    local,
                    qname,
                    self.quarantine_id,
                    self._mime(spec, fetched.content_type),
                )
                state.upsert_source_state(
                    spec.source_id,
                    spec.url,
                    etag=fetched.etag,
                    last_modified=fetched.last_modified,
                    last_sha256=fetched.sha256,
                    last_status="STOP_SOURCE_CONTRACT",
                    remote_file_id=uploaded.get("id"),
                )
                result = {
                    "source_id": spec.source_id,
                    "status": "STOP_SOURCE_CONTRACT",
                    "reason": "UNEXPECTED_CONTENT_TYPE",
                    "observed_content_type": observed_type,
                    "expected_content_types": list(spec.expected_content_types),
                    "sha256": fetched.sha256,
                    "quarantine_remote_id": uploaded.get("id"),
                }
                state.event("SOURCE_QUARANTINED", result)
                return result

            digest = fetched.sha256
            if digest and state.has_hash(digest):
                state.upsert_source_state(
                    spec.source_id,
                    spec.url,
                    etag=fetched.etag,
                    last_modified=fetched.last_modified,
                    last_sha256=digest,
                    last_status="DUPLICATE_HASH",
                    remote_file_id=previous.get("remote_file_id"),
                )
                result = {
                    "source_id": spec.source_id,
                    "status": "DUPLICATE_HASH",
                    "http_status": fetched.http_status,
                    "sha256": digest,
                    "bytes": fetched.bytes_written,
                }
                state.event("SOURCE_DUPLICATE_HASH", result)
                return result

            remote_name = self._remote_name(spec, digest)
            uploaded = self.drive.put(
                local,
                remote_name,
                self.bronze_id,
                self._mime(spec, fetched.content_type),
            )
            state.register_file(digest, spec.logical_key, remote_name, "BRONZE_REMOTE")
            state.upsert_source_state(
                spec.source_id,
                spec.url,
                etag=fetched.etag,
                last_modified=fetched.last_modified,
                last_sha256=digest,
                last_status="DOWNLOADED_NEW",
                remote_file_id=uploaded.get("id"),
            )
            result = {
                "source_id": spec.source_id,
                "status": "DOWNLOADED_NEW",
                "http_status": fetched.http_status,
                "sha256": digest,
                "bytes": fetched.bytes_written,
                "content_type": observed_type,
                "remote_id": uploaded.get("id"),
                "remote_name": remote_name,
            }
            state.event("SOURCE_DOWNLOADED", result)
            return result
