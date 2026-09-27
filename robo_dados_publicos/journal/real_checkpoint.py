"""Pure T0 validation for a TASK 018 Jornal canonical checkpoint candidate."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from urllib.parse import urlparse


EXPECTED = {
    "origin_task": "TASK_018",
    "origin_run_id": 33392616951,
    "origin_batch_id": "BATCH-CBBF70ADCA619C9C",
    "origin_execution_head_sha": "81db1a28c4532bd299d5b21cf38e295f4c49eeec",
}
ALLOWED_DOCUMENT_HOSTS = frozenset({"ecrie.com.br"})
PROHIBITED_AUTHORIZATIONS = frozenset({
    "source_network_authorized", "drive_read_authorized", "drive_write_authorized",
    "document_download_from_source_authorized", "workflow_dispatch_authorized",
    "processing_authorized", "downstream_authorized", "publication_authorized",
    "checkpoint_advance_authorized", "future_batch_execution_authorized",
    "schedule_authorized", "recurrence_authorized", "automatic_retry_authorized",
    "task_018_rerun_authorized", "live_proof_authorized",
})


def canonical_payload(items: list[dict]) -> bytes:
    """Serialize only the ordered canonical identities, without JSON ambiguity."""
    return json.dumps(
        items, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_payload_sha256(items: list[dict]) -> str:
    return hashlib.sha256(canonical_payload(items)).hexdigest()


def validate_t0_authorizations(authorizations: dict) -> dict:
    """Refuse any operational capability in this offline review."""
    if not isinstance(authorizations, dict):
        return _stop("STOP_AUTHORIZATION_CONTRACT_MISSING")
    enabled = sorted(key for key in PROHIBITED_AUTHORIZATIONS if authorizations.get(key) is not False)
    if enabled:
        return _stop("STOP_T0_OPERATIONAL_AUTHORIZATION", enabled=enabled)
    return {"status": "PASS_T0_AUTHORIZATIONS_BLOCKED", "remote_effects": 0, "live_proof_authorized": False}


def validate_real_checkpoint(snapshot: dict) -> dict:
    """Validate a candidate without performing I/O; every uncertainty is a STOP."""
    if not isinstance(snapshot, dict):
        return _stop("STOP_BAD_SNAPSHOT_CONTRACT")
    if snapshot.get("checkpoint_status") != "COMPLETE":
        return _stop("STOP_CHECKPOINT_NOT_COMPLETE")
    if any(snapshot.get(key) != value for key, value in EXPECTED.items()):
        mismatches = [key for key, value in EXPECTED.items() if snapshot.get(key) != value]
        return _stop("STOP_TASK_018_ORIGIN_MISMATCH", mismatches=mismatches)
    if snapshot.get("source_id") != "LIMEIRA_JORNAL_OFICIAL":
        return _stop("STOP_BAD_SOURCE")

    items = snapshot.get("items")
    if not isinstance(items, list) or len(items) != 12 or snapshot.get("item_count") != 12:
        return _stop("STOP_ITEM_COUNT_NOT_EXACTLY_12")
    editions: set[int] = set()
    source_ids: set[str] = set()
    logical_keys: set[str] = set()
    normalized: list[dict] = []
    for raw in items:
        if not isinstance(raw, dict):
            return _stop("STOP_BAD_ITEM_CONTRACT")
        edition = raw.get("edition")
        if isinstance(edition, bool) or not isinstance(edition, int) or edition <= 0:
            return _stop("STOP_BAD_EDITION")
        publication_date = raw.get("publication_date")
        try:
            if not isinstance(publication_date, str) or date.fromisoformat(publication_date).isoformat() != publication_date:
                raise ValueError
        except ValueError:
            return _stop("STOP_BAD_PUBLICATION_DATE")
        document_url = raw.get("document_url")
        parsed = urlparse(document_url) if isinstance(document_url, str) else None
        if not parsed or parsed.scheme != "https":
            return _stop("STOP_DOCUMENT_URL_NOT_HTTPS")
        if parsed.hostname not in ALLOWED_DOCUMENT_HOSTS:
            return _stop("STOP_DOCUMENT_HOST_NOT_ALLOWED")
        source_id = raw.get("source_id")
        logical_key = raw.get("logical_key")
        if source_id != f"LIMEIRA_JO_{edition:05d}":
            return _stop("STOP_SOURCE_ID_EDITION_MISMATCH")
        if logical_key != f"limeira/jornal_oficial/edicao/{edition}":
            return _stop("STOP_LOGICAL_KEY_EDITION_MISMATCH")
        if edition in editions:
            return _stop("STOP_DUPLICATE_EDITION")
        if source_id in source_ids:
            return _stop("STOP_DUPLICATE_SOURCE_ID")
        if logical_key in logical_keys:
            return _stop("STOP_DUPLICATE_LOGICAL_KEY")
        editions.add(edition); source_ids.add(source_id); logical_keys.add(logical_key)
        normalized.append({key: raw[key] for key in ("edition", "publication_date", "document_url", "source_id", "logical_key")})
    if [row["edition"] for row in normalized] != sorted(editions):
        return _stop("STOP_ITEMS_NOT_DETERMINISTICALLY_ORDERED")

    provenance = snapshot.get("provenance")
    if not isinstance(provenance, dict):
        return _stop("STOP_PROVENANCE_MISSING")
    if provenance.get("authority") != "TASK_018_HISTORICAL_SANITIZED_ARTIFACT":
        return _stop("STOP_PROVENANCE_NOT_OPERATIONAL")
    if provenance.get("artifact_name") != "task-018-sanitized-operational-evidence" or provenance.get("artifact_id") != 9758450652:
        return _stop("STOP_PROVENANCE_ARTIFACT_MISMATCH")
    if provenance.get("identities_observed_directly") is not True:
        return _stop("STOP_IDENTITIES_NOT_DIRECTLY_EVIDENCED")
    if provenance.get("sequence_assumed") is not False:
        return _stop("STOP_ASSUMED_SEQUENCE_PROHIBITED")
    if provenance.get("synthetic_fixture") is not False:
        return _stop("STOP_SYNTHETIC_FIXTURE_NOT_AUTHORITY")

    integrity = snapshot.get("integrity")
    digest = canonical_payload_sha256(normalized)
    if not isinstance(integrity, dict) or integrity.get("item_count") != 12 or integrity.get("canonical_payload_sha256") != digest:
        return _stop("STOP_INTEGRITY_MISMATCH")
    return {"status": "PASS_REAL_CHECKPOINT_PINNED", "item_count": 12, "canonical_payload_sha256": digest, "remote_effects": 0, "live_proof_authorized": False}


def _stop(status: str, **extra: object) -> dict:
    return {"status": status, "remote_effects": 0, "live_proof_authorized": False, **extra}
