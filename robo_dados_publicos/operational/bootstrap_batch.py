"""Pure, dependency-injected TASK 018 bounded batch orchestrator.

Production transports must implement these small protocols.  The implementation PR
does not instantiate a network or Drive transport and therefore has zero effects.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.product.bundle import build_product_report, write_product_bundle


ITEM_LOCAL_STOPS = {"STOP_OCR_REQUIRED", "STOP_SCHEMA_UNKNOWN", "STOP_DOCUMENT_NOT_PDF", "STOP_DOCUMENT_TOO_LARGE", "STOP_DOCUMENT_HASH_COLLISION", "EVIDENCIA_INSUFICIENTE", "QUARANTINED"}
SYSTEMIC_STOPS = {"STOP_OWNER_AUTHORIZATION_REQUIRED", "STOP_IMPLEMENTATION_SHA_MISMATCH", "STOP_CANONICAL_POLICY_DRIFT", "STOP_RELEASE_STATE_DRIFT", "STOP_REMOTE_EFFECT_POLICY", "STOP_CREDENTIAL_CAPABILITY", "STOP_DRIVE_LAYOUT_UNPROVEN", "STOP_DISCOVERY_CONTRACT_BROKEN", "STOP_CREATE_ONLY_INVARIANT", "STOP_MANIFEST_INTEGRITY"}


class SourceTransport(Protocol):
    def discover(self, family: dict, maximum_pages: int) -> list[dict]: ...
    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict]: ...


class CreateOnlyStore(Protocol):
    def lookup(self, destination: str, logical_key: str) -> dict | None: ...
    def create(self, destination: str, name: str, data: bytes, metadata: dict) -> dict: ...
    def readback(self, destination: str, name: str) -> dict: ...


class Processor(Protocol):
    def process(self, item: dict, data: bytes) -> dict: ...


@dataclass
class Budget:
    config: dict
    started: float
    gets: int = 0
    pages: int = 0
    documents: int = 0
    bytes: int = 0
    creates: int = 0
    reconciliations: int = 0

    def exhausted(self) -> bool:
        c = self.config
        return (time.monotonic() - self.started >= c["maximum_runtime_seconds"] or self.gets >= c["maximum_total_remote_get_count"] or self.documents >= c["maximum_documents"] or self.bytes >= c["maximum_aggregate_source_bytes"] or self.creates >= c["maximum_drive_create_operations"])


def eligibility_inventory(config: dict) -> list[dict]:
    """Return the canonical classifications; connector presence is irrelevant."""
    allowed = {"ELIGIBLE_LIVE_COLLECTION", "REUSE_ALREADY_PROVEN", "BLOCKED_CONTRACT_UNPROVEN", "BLOCKED_SEMANTIC_UNPROVEN", "BLOCKED_AUTHORIZATION_SCOPE", "NOT_APPLICABLE"}
    rows = sorted(config["eligibility"], key=lambda row: row["source_family"])
    if not rows or any(row.get("classification") not in allowed for row in rows):
        raise ValueError("STOP_CANONICAL_POLICY_DRIFT")
    return rows


class BootstrapBatch:
    def __init__(self, config: dict, source: SourceTransport, store: CreateOnlyStore, processor: Processor, *, reconciler=None):
        self.config, self.source, self.store, self.processor, self.reconciler = config, source, store, processor, reconciler

    def run(self, output_dir: str | Path, authorization: dict, *, preflight_ok: bool = True, started: float | None = None) -> dict:
        effects = {"source_gets": 0, "drive_reads": 0, "drive_writes": 0, "publication_writes": 0, "live_reconciliation": 0}
        required = ("source_read_authorized", "drive_read_authorized", "drive_create_only_authorized", "processing_authorized", "reconciliation_read_authorized", "product_generation_authorized", "product_publication_create_only_authorized")
        if not authorization.get("authorized") or any(authorization.get(k) is not True for k in required):
            return {"status": "STOP_OWNER_AUTHORIZATION_REQUIRED", "effects": effects, "items": [], "systemic_stop": True}
        if not preflight_ok:
            return {"status": "STOP_CANONICAL_POLICY_DRIFT", "effects": effects, "items": [], "systemic_stop": True}
        if any(authorization.get(k) for k in ("overwrite_authorized", "replace_authorized", "delete_authorized", "automatic_retry_authorized", "schedule_authorized", "recurrence_authorized", "gold_2025_authorized", "siope_2025_series_inclusion_authorized")):
            return {"status": "STOP_REMOTE_EFFECT_POLICY", "effects": effects, "items": [], "systemic_stop": True}
        budget = Budget(self.config["hard_safety_ceilings"], started or time.monotonic())
        inventory, discovered = eligibility_inventory(self.config), []
        for family in inventory:
            if family["classification"] == "ELIGIBLE_LIVE_COLLECTION":
                rows = self.source.discover(family, budget.config["maximum_index_discovery_pages"])
                budget.pages += 1
                discovered.extend(rows)
        # Deterministic logical identity, never synthesized URLs.
        unique = {row["logical_key"]: row for row in sorted(discovered, key=lambda x: (x["logical_key"], x["url"]))}
        items = []
        for logical_key, item in unique.items():
            if budget.exhausted():
                break
            existing = self.store.lookup("Bronze", logical_key); effects["drive_reads"] += 1
            if existing and item.get("expected_sha256") == existing.get("sha256"):
                items.append({**item, "status": "SKIPPED_ALREADY_PROVEN"}); continue
            if existing:
                items.append({**item, "status": "STOP_DOCUMENT_HASH_COLLISION"}); continue
            data, meta = self.source.get(item["url"], budget.config["maximum_bytes_per_document"]); budget.gets += 1; budget.documents += 1; budget.bytes += len(data); effects["source_gets"] += 1
            host_ok = meta.get("https") and meta.get("final_host") in item["allowed_hosts"]
            if not host_ok or not data.startswith(b"%PDF") or meta.get("content_type") != "application/pdf":
                items.append({**item, "status": "STOP_DOCUMENT_NOT_PDF"}); continue
            if len(data) > budget.config["maximum_bytes_per_document"]:
                items.append({**item, "status": "STOP_DOCUMENT_TOO_LARGE"}); continue
            digest = hashlib.sha256(data).hexdigest()
            if item.get("expected_sha256") and item["expected_sha256"] != digest:
                items.append({**item, "status": "STOP_DOCUMENT_HASH_COLLISION"}); continue
            source_meta = {"source_id": item["source_id"], "logical_key": logical_key, "source_url": item["url"], "publication_date": item.get("publication_date"), "sha256": digest, "byte_count": len(data), "content_type": meta["content_type"], "provenance": "DECLARED_AUTHORIZED_DISCOVERY_LINK"}
            self.store.create("Bronze", logical_key + ".pdf", data, source_meta); budget.creates += 1; effects["drive_writes"] += 1
            try:
                derived = self.processor.process(item, data)
            except Exception as exc:
                status = getattr(exc, "status", "STOP_SCHEMA_UNKNOWN")
                self.store.create("Quarantine", logical_key + ".json", json.dumps({"logical_key": logical_key, "status": status}).encode(), {"diagnostic_only": True}); budget.creates += 1; effects["drive_writes"] += 1
                items.append({**item, "status": status if status in ITEM_LOCAL_STOPS else "QUARANTINED"}); continue
            for destination, objects in derived.get("layers", {}).items():
                for name, payload in objects:
                    self.store.create(destination, name, payload, {"source_sha256": digest, "create_only": True}); budget.creates += 1; effects["drive_writes"] += 1
            items.append({**item, "status": "PASS_ITEM", "sha256": digest, "derived_counts": {k: len(v) for k, v in derived.get("layers", {}).items()}})
        remaining = len(unique) - len(items)
        status = "PARTIAL_BATCH_SAFETY_BUDGET_REACHED" if remaining else "COMPLETE"
        result = {"status": status, "systemic_stop": False, "inventory": inventory, "items": items, "effects": effects, "checkpoint": {"remaining_logical_keys": sorted(set(unique) - {x["logical_key"] for x in items})}, "budget": budget.__dict__ | {"started": None}}
        self._product(Path(output_dir), result)
        return result

    def _product(self, out: Path, result: dict) -> None:
        if out.exists(): raise FileExistsError("STOP_CREATE_ONLY_INVARIANT")
        out.mkdir(parents=True)
        rows = [AnswerContract("ANSWERED", "TASK 018 bounded inventory", json.dumps({"items": len(result["items"]), "status": result["status"]}), "No candidate is financial identity.", "Synthetic/offline tests or separately authorized execution only.", "Blocked and quarantined rows remain explicit.", tuple())]
        report = build_product_report(rows, report_id="TASK018-" + hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()[:16], title="Full operational bootstrap", scope=self.config["authorization_scope"], generated_at=datetime.now(timezone.utc).isoformat(), limitations=("MATCH_CANDIDATE is not financial identity.",), notes="0.7.0 ACTIVE; 0.8.0 CANDIDATE", software_version="0.8.0")
        write_product_bundle(report, out / "product")
        (out / "operational_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        (out / "operational_summary.md").write_text(f"# TASK 018 operational summary\n\nStatus: **{result['status']}**\n\nItems: {len(result['items'])}\n")
