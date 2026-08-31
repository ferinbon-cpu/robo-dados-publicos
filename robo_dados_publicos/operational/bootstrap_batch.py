"""Bounded, stage-aware TASK 018 orchestration; transports are dependency injected."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.product.bundle import build_product_report, write_product_bundle

ROOT = Path(__file__).resolve().parents[2]
ITEM_LOCAL_STOPS = {"STOP_OCR_REQUIRED", "STOP_SCHEMA_UNKNOWN", "STOP_DOCUMENT_NOT_PDF", "STOP_DOCUMENT_TOO_LARGE", "STOP_DOCUMENT_HASH_COLLISION", "STOP_DISCOVERY_AMBIGUITY", "EVIDENCIA_INSUFICIENTE", "QUARANTINED"}
SYSTEMIC_STOPS = {"STOP_OWNER_AUTHORIZATION_REQUIRED", "STOP_IMPLEMENTATION_SHA_MISMATCH", "STOP_CANONICAL_POLICY_DRIFT", "STOP_RELEASE_STATE_DRIFT", "STOP_REMOTE_EFFECT_POLICY", "STOP_CREDENTIAL_CAPABILITY", "STOP_DRIVE_LAYOUT_UNPROVEN", "STOP_DISCOVERY_CONTRACT_BROKEN", "STOP_CREATE_ONLY_INVARIANT", "STOP_MANIFEST_INTEGRITY", "STOP_BATCH_AUTHORIZATION_CONSUMED"}

class SourceTransport(Protocol):
    def discover(self, family: dict, maximum_pages: int): ...
    def get(self, url: str, maximum_bytes: int): ...
class CreateOnlyStore(Protocol):
    def lookup(self, destination: str, logical_key: str, suffix: str = ""): ...
    def create(self, destination: str, name: str, data: bytes, metadata: dict): ...
    def readback(self, destination: str, name: str): ...
class Processor(Protocol):
    def process(self, item: dict, data: bytes): ...


def canonical_json(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def identity(prefix, value): return prefix + hashlib.sha256(canonical_json(value).encode()).hexdigest()[:16].upper()


def validate_authorization(auth: dict) -> str | None:
    required = ("source_read_authorized", "drive_read_authorized", "drive_create_only_authorized", "processing_authorized", "reconciliation_read_authorized", "product_generation_authorized", "product_publication_create_only_authorized")
    if not auth.get("authorized") or auth.get("status") != "AUTHORIZED" or any(auth.get(k) is not True for k in required): return "STOP_OWNER_AUTHORIZATION_REQUIRED"
    if auth.get("single_batch_authorized") is not True or auth.get("consumed") or auth.get("further_execution_authorized") or auth.get("retry_authorized"): return "STOP_BATCH_AUTHORIZATION_CONSUMED"
    forbidden = ("overwrite_authorized", "replace_authorized", "delete_authorized", "automatic_retry_authorized", "schedule_authorized", "recurrence_authorized", "release_promotion_authorized", "gold_2025_authorized", "siope_2025_series_inclusion_authorized")
    if any(auth.get(k) for k in forbidden): return "STOP_REMOTE_EFFECT_POLICY"
    return None


def validate_canonical_projection(config: dict, root: Path = ROOT) -> bool:
    """Cross-check policy projection against independent checked-in evidence."""
    try:
        discovery = json.loads((root / "config/limeira_sources_discovery.json").read_text())
        source_gate = json.loads((root / "config/sources.jornal_oficial_7310_gate.json").read_text())
        automation = json.loads((root / "config/automation_policy.v1.json").read_text())
        cloud = json.loads((root / "config/cloud.json").read_text())
        pending = json.loads((root / "docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json").read_text())
        closure = json.loads((root / "docs/evidence/TASK_015_M8_R3_PUBLICATION_CLOSURE_0.8.0.json").read_text())
    except (OSError, ValueError): return False
    surfaces = {x["source_id"]: x for x in discovery.get("surfaces", [])}
    families = {x["source_family"]: x for x in config.get("eligibility", [])}
    source = source_gate.get("sources", [{}])[0]
    canonical = pending.get("canonical_state", {})
    gate = next((x for x in automation.get("gates", []) if x.get("id") == "TASK_018_FULL_OPERATIONAL_BOOTSTRAP"), {})
    required_cloud = {"bronze_id", "silver_id", "gold_id", "documentos_id", "rag_id", "bancos_id", "logs_id", "outputs_id", "quarantine_id"}
    return all((
        surfaces.get("LIMEIRA_JORNAL_OFICIAL", {}).get("status") == "LIVE_VALIDATED",
        surfaces.get("LIMEIRA_TDA_PORTAL", {}).get("status") == "BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN",
        families.get("LIMEIRA_TDA_PORTAL", {}).get("classification") == "BLOCKED_CONTRACT_UNPROVEN",
        families.get("SIOPE_2025", {}).get("classification") == "BLOCKED_SEMANTIC_UNPROVEN",
        families.get("LIMEIRA_JORNAL_OFICIAL", {}).get("scope") == "DECLARED_LINKS_IN_PROVEN_MODERN_WINDOW_2026_08",
        "ecrie.com.br" in families.get("LIMEIRA_JORNAL_OFICIAL", {}).get("allowed_hosts", []),
        source.get("url", "").startswith("https://ecrie.com.br/"),
        source.get("expected_sha256") == "78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680",
        gate.get("auto_allowed") is False and gate.get("owner_authorization_required") is True,
        required_cloud <= set(cloud),
        canonical.get("release_0_8_0") == "CANDIDATE" and canonical.get("gold_2025") == "UNKNOWN/BLOCKED",
        closure.get("release_status") == "CANDIDATE" and closure.get("publication_scope") == "SIOPE_HISTORICAL_2016_2024" and closure.get("include_2025") is False,
    ))


class Budget:
    def __init__(self, config, started=None):
        self.config, self.started = config, started or time.monotonic()
        self.counts = {k: 0 for k in ("robots_get_count", "index_get_count", "document_get_count", "reconciliation_get_count", "total_remote_get_count", "source_bytes", "drive_create_operations")}
    def add_gets(self, kind, amount):
        if amount < 0 or self.counts["total_remote_get_count"] + amount > self.config["maximum_total_remote_get_count"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        if kind == "index_get_count" and self.counts[kind] + amount > self.config["maximum_index_discovery_pages"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        if kind == "reconciliation_get_count" and self.counts[kind] + amount > self.config["maximum_live_reconciliation_requests"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.counts[kind] += amount; self.counts["total_remote_get_count"] += amount
    def before_document(self):
        if self.counts["document_get_count"] >= self.config["maximum_documents"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.add_gets("document_get_count", 1)
    def accept_bytes(self, amount):
        if amount > self.config["maximum_bytes_per_document"] or self.counts["source_bytes"] + amount > self.config["maximum_aggregate_source_bytes"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.counts["source_bytes"] += amount
    def before_create(self):
        if self.counts["drive_create_operations"] >= self.config["maximum_drive_create_operations"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.counts["drive_create_operations"] += 1
    def runtime_ok(self):
        if time.monotonic() - self.started >= self.config["maximum_runtime_seconds"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")


def eligibility_inventory(config):
    allowed = {"ELIGIBLE_LIVE_COLLECTION", "REUSE_ALREADY_PROVEN", "BLOCKED_CONTRACT_UNPROVEN", "BLOCKED_SEMANTIC_UNPROVEN", "BLOCKED_AUTHORIZATION_SCOPE", "NOT_APPLICABLE"}
    rows = sorted(config["eligibility"], key=lambda x: x["source_family"])
    if not rows or any(x.get("classification") not in allowed for x in rows): raise ValueError("STOP_CANONICAL_POLICY_DRIFT")
    return rows


def deduplicate_discovery(rows):
    grouped = defaultdict(list)
    for row in rows: grouped[row["logical_key"]].append(row)
    accepted, ambiguous = [], []
    fields = ("url", "source_id", "publication_date", "source_page_url", "archive_class")
    for key in sorted(grouped):
        group = grouped[key]; signatures = {tuple(x.get(f) for f in fields) for x in group}
        if len(signatures) != 1: ambiguous.append({**group[0], "status": "STOP_DISCOVERY_AMBIGUITY", "conflicting_provenance": [{f: x.get(f) for f in fields} for x in group]})
        else: accepted.append(group[0])
    return accepted, ambiguous


class BootstrapBatch:
    def __init__(self, config, source, store, processor, *, reconciler=None, canonical_validator=validate_canonical_projection):
        self.config, self.source, self.store, self.processor, self.reconciler, self.canonical_validator = config, source, store, processor, reconciler, canonical_validator

    def run(self, output_dir, authorization, *, execution=None):
        effects = {"source_gets": 0, "drive_reads": 0, "drive_writes": 0, "publication_writes": 0, "live_reconciliation": 0}
        stop = validate_authorization(authorization)
        if stop: return self._stopped(stop, effects, output_dir)
        if not self.canonical_validator(self.config): return self._stopped("STOP_CANONICAL_POLICY_DRIFT", effects, output_dir)
        execution = execution or {}; provenance = {"implementation_merge_sha": authorization.get("implementation_merge_sha"), "authorization_evidence_identity": authorization.get("authorization_sha"), **execution}
        batch_id = identity("BATCH-", {"implementation": provenance["implementation_merge_sha"], "authorization": provenance["authorization_evidence_identity"], "scope": authorization.get("scope")})
        marker_name = batch_id + ".json"
        prior_marker = self.store.lookup("Logs", batch_id, ".json")
        current_run = execution.get("github_run_id")
        if prior_marker:
            try: prior_run = json.loads(prior_marker.get("data", b"{}")).get("github_run_id")
            except (ValueError, UnicodeDecodeError): prior_run = None
            if not current_run or prior_run != current_run: return self._stopped("STOP_BATCH_AUTHORIZATION_CONSUMED", effects, output_dir)
        budget = Budget(self.config["hard_safety_ceilings"]); inventory, discovered = eligibility_inventory(self.config), []
        try:
            for family in inventory:
                if family["classification"] != "ELIGIBLE_LIVE_COLLECTION": continue
                rows, telemetry = self.source.discover(family, budget.config["maximum_index_discovery_pages"])
                budget.add_gets("robots_get_count", telemetry["robots_get_count"]); budget.add_gets("index_get_count", telemetry["index_get_count"]); discovered.extend(rows)
            accepted, ambiguous = deduplicate_discovery(discovered); items = list(ambiguous); tasks = []
            # The one-shot execution marker is the first mutation. Its existence
            # makes a repeated dispatch fail closed before any repeated effects.
            if not prior_marker:
                budget.before_create(); marker = self.store.create("Logs", marker_name, canonical_json({"batch_id": batch_id, "state": "STARTED", "github_run_id": current_run}).encode(), {"content_type": "application/json"}); effects["drive_writes"] += marker["status"] == "CREATED"
            for item in accepted:
                budget.runtime_ok(); logical = item["logical_key"]; suffix = ".pdf"
                existing = self.store.lookup("Bronze", logical, suffix); effects["drive_reads"] += 1
                data = existing.get("data") if existing else None
                if existing:
                    if existing.get("source_url") and existing["source_url"] != item["url"]: items.append({**item, "status": "STOP_DOCUMENT_HASH_COLLISION"}); continue
                    item["bronze_state"] = "REUSED_IDENTICAL"
                else:
                    budget.before_document(); effects["source_gets"] += 1
                    data, meta = self.source.get(item["url"], budget.config["maximum_bytes_per_document"]); budget.accept_bytes(len(data))
                    host = meta.get("final_host", "").lower()
                    if not meta.get("https") or host not in item["allowed_hosts"] or not data.startswith(b"%PDF") or meta.get("content_type") != "application/pdf": items.append({**item, "status": "STOP_DOCUMENT_NOT_PDF"}); continue
                    digest = hashlib.sha256(data).hexdigest()
                    if item.get("expected_sha256") and digest != item["expected_sha256"]: items.append({**item, "status": "STOP_DOCUMENT_HASH_COLLISION"}); continue
                    budget.before_create(); created = self.store.create("Bronze", logical.replace("/", "_") + suffix, data, {"content_type": "application/pdf", "logical_key": logical, "source_url": item["url"], "sha256": digest}); effects["drive_writes"] += created.get("status") == "CREATED"; item["bronze_state"] = created["status"]
                try: derived = self.processor.process(item, data)
                except Exception as exc:
                    status = getattr(exc, "status", "STOP_SCHEMA_UNKNOWN"); budget.before_create(); self.store.create("Quarantine", logical.replace("/", "_") + ".json", canonical_json({"logical_key": logical, "status": status}).encode(), {"content_type": "application/json"}); effects["drive_writes"] += 1; items.append({**item, "status": status}); continue
                layer_states = Counter()
                for destination, objects in derived.get("layers", {}).items():
                    for name, payload in objects:
                        budget.before_create(); result = self.store.create(destination, name, payload, {"content_type": "application/json", "source_sha256": hashlib.sha256(data).hexdigest()}); layer_states[destination + "_" + result["status"]] += 1; effects["drive_writes"] += result["status"] == "CREATED"
                tasks.extend(derived.get("tasks", [])); items.append({**item, "status": "PASS_ITEM", "layer_states": dict(layer_states), "metrics": derived.get("metrics", {})})
            rec = self._reconcile(tasks, budget, effects, Path(output_dir))
            status = "COMPLETE"
        except RuntimeError as exc:
            if str(exc) != "PARTIAL_BATCH_SAFETY_BUDGET_REACHED": raise
            status = str(exc); rec = {"status": "NOT_EXECUTED_SAFETY_BUDGET", "tasks": len(locals().get("tasks", [])), "requests": budget.counts["reconciliation_get_count"], "status_counts": {}}
            accepted = locals().get("accepted", []); items = locals().get("items", [])
        processed_keys = {x["logical_key"] for x in items}; checkpoint = sorted(x["logical_key"] for x in locals().get("accepted", []) if x["logical_key"] not in processed_keys)
        snapshot_payload = {"inventory": inventory, "items": items, "reconciliation": rec, "checkpoint": checkpoint}; snapshot_id = identity("SNAP-", snapshot_payload)
        run_id = identity("RUN-", {"snapshot_id": snapshot_id, "github_run_id": execution.get("github_run_id"), "github_run_attempt": execution.get("github_run_attempt")})
        result = {"status": status, "systemic_stop": False, "batch_id": batch_id, "snapshot_id": snapshot_id, "run_id": run_id, **provenance, "inventory": inventory, "discovered_count": len(discovered), "items": items, "reconciliation": rec, "telemetry": budget.counts, "effects": effects, "checkpoint": {"remaining_logical_keys": checkpoint}, "publication": {"status": "NOT_EXECUTED", "objects": []}}
        out = Path(output_dir); self._product(out, result)
        return result

    def _reconcile(self, tasks, budget, effects, work):
        eligible = [x for x in tasks if x.get("target_source") == "LIMEIRA_CONTRATOS"]
        blocked = len(tasks) - len(eligible)
        if not eligible: return {"status": "NOT_EXECUTED_NO_ELIGIBLE_TASK", "tasks": len(tasks), "blocked": blocked, "requests": 0, "status_counts": {}}
        if self.reconciler is None: return {"status": "BLOCKED_RECONCILIATION_CONTRACT", "tasks": len(tasks), "blocked": len(tasks), "requests": 0, "status_counts": {}}
        results = []
        for task in eligible:
            remaining = min(budget.config["maximum_live_reconciliation_requests"] - budget.counts["reconciliation_get_count"], budget.config["maximum_total_remote_get_count"] - budget.counts["total_remote_get_count"])
            if remaining <= 0: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
            response = self.reconciler.execute(task, work / "reconciliation" / task["task_id"], remaining)
            result, actual = response if isinstance(response, tuple) else (response, 1)
            budget.add_gets("reconciliation_get_count", actual); effects["live_reconciliation"] += actual; results.append(result)
        return {"status": "PASS_RECONCILIATION_EXECUTION", "tasks": len(tasks), "blocked": blocked, "requests": len(results), "status_counts": dict(Counter(x["status"] for x in results)), "results": results, "financial_identity_auto_promotion": "PROHIBITED"}

    def publish(self, output_dir, result):
        product = Path(output_dir) / "product"; manifest = json.loads((product / "manifest.json").read_text()); names = [x["name"] for x in manifest["files"]]
        if "manifest.json" in names: raise RuntimeError("STOP_MANIFEST_INTEGRITY")
        prefix = result["batch_id"] + "_"; published = []
        for name in sorted(names):
            if result["telemetry"]["drive_create_operations"] >= self.config["hard_safety_ceilings"]["maximum_drive_create_operations"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
            data = (product / name).read_bytes(); record = self.store.create("Outputs", prefix + name, data, {"content_type": "application/octet-stream"}); published.append(record); result["effects"]["publication_writes"] += record["status"] == "CREATED"
            result["telemetry"]["drive_create_operations"] += record["status"] == "CREATED"
        if result["telemetry"]["drive_create_operations"] >= self.config["hard_safety_ceilings"]["maximum_drive_create_operations"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        manifest_data = (product / "manifest.json").read_bytes(); final = self.store.create("Outputs", prefix + "manifest.json", manifest_data, {"content_type": "application/json"}); published.append(final); result["effects"]["publication_writes"] += final["status"] == "CREATED"
        result["telemetry"]["drive_create_operations"] += final["status"] == "CREATED"
        for name in [prefix + x for x in sorted(names)] + [prefix + "manifest.json"]: self.store.readback("Outputs", name)
        result["publication"] = {"status": "PUBLISHED_CREATE_ONLY_READBACK_VERIFIED", "objects": [prefix + x for x in sorted(names)] + [prefix + "manifest.json"], "manifest_written_last": True, "final_readback_required": True}
        completion_name = result["batch_id"] + "_COMPLETED.json"
        if result["telemetry"]["drive_create_operations"] >= self.config["hard_safety_ceilings"]["maximum_drive_create_operations"]: raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        completion = self.store.create("Logs", completion_name, canonical_json({"batch_id": result["batch_id"], "run_id": result["run_id"], "publication": "COMPLETE"}).encode(), {"content_type": "application/json"})
        result["effects"]["drive_writes"] += completion["status"] == "CREATED"
        result["telemetry"]["drive_create_operations"] += completion["status"] == "CREATED"
        (Path(output_dir) / "operational_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        self._audit(Path(output_dir), result); return result

    def _product(self, out, result):
        if out.exists(): raise FileExistsError("STOP_CREATE_ONLY_INVARIANT")
        out.mkdir(parents=True); counts = self._counts(result)
        answer = AnswerContract("ANSWERED", "TASK 018 bounded inventory", canonical_json(counts), "MATCH_CANDIDATE is candidate-only.", "Blocked/quarantined states remain explicit.", "Presentation is not evidence.", tuple())
        report = build_product_report([answer], report_id=result["run_id"], title="Full operational bootstrap", scope=self.config["authorization_scope"], generated_at=datetime.now(timezone.utc).isoformat(), limitations=("MATCH_CANDIDATE is not financial identity.",), notes=f"Batch status: {result['status']}; 0.7.0 ACTIVE; 0.8.0 CANDIDATE", software_version="0.8.0")
        write_product_bundle(report, out / "product"); (out / "operational_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); (out / "operational_summary.md").write_text(self._summary(result, counts)); self._audit(out, result)
    def _counts(self, r):
        statuses = Counter(x["status"] for x in r["items"]); layers = Counter()
        for x in r["items"]: layers.update(x.get("layer_states", {}))
        classes = Counter(x["classification"] for x in r["inventory"])
        return {"families_considered": len(r["inventory"]), "family_classifications": dict(classes), "discovered": r["discovered_count"], "already_proven": sum(x.get("bronze_state") == "REUSED_IDENTICAL" for x in r["items"]), "downloaded": r["telemetry"]["document_get_count"], "bronze_created": sum(x.get("bronze_state") == "CREATED" for x in r["items"]), "bronze_reused": sum(x.get("bronze_state") == "REUSED_IDENTICAL" for x in r["items"]), "processed": statuses["PASS_ITEM"], "derived": dict(layers), "quarantine": sum(x["status"] in ITEM_LOCAL_STOPS for x in r["items"]), "ocr_required": statuses["STOP_OCR_REQUIRED"], "schema_unknown": statuses["STOP_SCHEMA_UNKNOWN"], "item_local_stops": dict(statuses), "reconciliation_tasks": r["reconciliation"]["tasks"], "reconciliation_requests": r["reconciliation"]["requests"], "match_candidate": r["reconciliation"]["status_counts"].get("MATCH_CANDIDATE", 0), "budget": r["telemetry"], "checkpoint": r["checkpoint"], "systemic_stop": r["systemic_stop"], "publication": r["publication"]}
    @staticmethod
    def _summary(r, c): return "# TASK 018 operational summary\n\n" + "\n".join(f"- **{k}:** `{canonical_json(v)}`" for k, v in ({"status": r["status"], "batch_id": r["batch_id"], "snapshot_id": r["snapshot_id"], "run_id": r["run_id"]} | c).items()) + "\n"
    @staticmethod
    def _audit(out, result):
        audit = out.parent / "task-018-audit"; audit.mkdir(parents=True, exist_ok=True)
        (audit / "operational_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        summary = out / "operational_summary.md"
        if summary.exists(): (audit / "operational_summary.md").write_text(summary.read_text())
    def _stopped(self, status, effects, output_dir):
        result = {"status": status, "systemic_stop": True, "effects": effects, "items": [], "telemetry": {k: 0 for k in ("robots_get_count", "index_get_count", "document_get_count", "reconciliation_get_count", "total_remote_get_count", "source_bytes", "drive_create_operations")}}
        out = Path(output_dir); out.mkdir(parents=True, exist_ok=True); (out / "operational_result.json").write_text(json.dumps(result, indent=2) + "\n"); self._audit(out, result); return result
