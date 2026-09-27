"""Bounded, stage-aware TASK 018 orchestration; transports are dependency injected."""
from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from robo_dados_publicos.core.models import AnswerContract
from robo_dados_publicos.product.bundle import build_product_report, write_product_bundle
from robo_dados_publicos.state.registry import StateRegistry

ROOT = Path(__file__).resolve().parents[2]
AUTH_SCOPE = "ALL_CURRENTLY_ELIGIBLE_PROVEN_ITEMS_AT_AUTHORIZATION_SHA"

ITEM_LOCAL_STOPS = {
    "STOP_OCR_REQUIRED",
    "STOP_SCHEMA_UNKNOWN",
    "STOP_DOCUMENT_NOT_PDF",
    "STOP_DOCUMENT_HOST_UNPROVEN",
    "STOP_DOCUMENT_TOO_LARGE",
    "STOP_DOCUMENT_FETCH",
    "STOP_DOCUMENT_HASH_COLLISION",
    "STOP_DISCOVERY_AMBIGUITY",
    "EVIDENCIA_INSUFICIENTE",
    "QUARANTINED",
}
SYSTEMIC_STOPS = {
    "STOP_OWNER_AUTHORIZATION_REQUIRED",
    "STOP_IMPLEMENTATION_SHA_MISMATCH",
    "STOP_CANONICAL_POLICY_DRIFT",
    "STOP_RELEASE_STATE_DRIFT",
    "STOP_REMOTE_EFFECT_POLICY",
    "STOP_CREDENTIAL_CAPABILITY",
    "STOP_DRIVE_LAYOUT_UNPROVEN",
    "STOP_DISCOVERY_CONTRACT_BROKEN",
    "STOP_CREATE_ONLY_INVARIANT",
    "STOP_MANIFEST_INTEGRITY",
    "STOP_BATCH_AUTHORIZATION_CONSUMED",
    "STOP_BATCH_RESERVATION_MISSING",
}


class SourceTransport(Protocol):
    def discover(self, family: dict, maximum_pages: int): ...
    def get(self, url: str, maximum_bytes: int): ...


class CreateOnlyStore(Protocol):
    def lookup(self, destination: str, logical_key: str, suffix: str = ""): ...
    def create(self, destination: str, name: str, data: bytes, metadata: dict): ...
    def readback(self, destination: str, name: str): ...


class Processor(Protocol):
    def process(self, item: dict, data: bytes): ...


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def identity(prefix, value):
    return prefix + hashlib.sha256(canonical_json(value).encode()).hexdigest()[:16].upper()


def authorization_identity(auth: dict) -> str:
    payload = {k: v for k, v in auth.items() if k != "authorization_sha"}
    return identity("AUTH-", payload)


def batch_identity(auth: dict) -> str:
    return identity(
        "BATCH-",
        {
            "implementation": auth.get("implementation_merge_sha"),
            "authorization": authorization_identity(auth),
            "scope": auth.get("scope"),
        },
    )


def validate_authorization(auth: dict) -> str | None:
    required = (
        "source_read_authorized",
        "drive_read_authorized",
        "drive_create_only_authorized",
        "processing_authorized",
        "reconciliation_read_authorized",
        "product_generation_authorized",
        "product_publication_create_only_authorized",
    )
    if (
        not auth.get("authorized")
        or auth.get("status") != "AUTHORIZED"
        or auth.get("scope") != AUTH_SCOPE
        or not auth.get("implementation_merge_sha")
        or any(auth.get(k) is not True for k in required)
    ):
        return "STOP_OWNER_AUTHORIZATION_REQUIRED"
    if (
        auth.get("single_batch_authorized") is not True
        or auth.get("consumed")
        or auth.get("further_execution_authorized")
        or auth.get("retry_authorized")
    ):
        return "STOP_BATCH_AUTHORIZATION_CONSUMED"
    forbidden = (
        "overwrite_authorized",
        "replace_authorized",
        "delete_authorized",
        "automatic_retry_authorized",
        "schedule_authorized",
        "recurrence_authorized",
        "release_promotion_authorized",
        "gold_2025_authorized",
        "siope_2025_series_inclusion_authorized",
    )
    if any(auth.get(k) for k in forbidden):
        return "STOP_REMOTE_EFFECT_POLICY"
    return None


def validate_canonical_projection(config: dict, root: Path = ROOT) -> bool:
    """Cross-check the TASK 018 projection against independent checked-in evidence."""
    try:
        discovery = json.loads(
            (root / "config/limeira_sources_discovery.json").read_text(encoding="utf-8")
        )
        source_gate = json.loads(
            (root / "config/sources.jornal_oficial_7310_gate.json").read_text(
                encoding="utf-8"
            )
        )
        automation = json.loads(
            (root / "config/automation_policy.v1.json").read_text(encoding="utf-8")
        )
        cloud = json.loads((root / "config/cloud.json").read_text(encoding="utf-8"))
        pending = json.loads(
            (
                root
                / "docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json"
            ).read_text(encoding="utf-8")
        )
        closure = json.loads(
            (
                root
                / "docs/evidence/TASK_015_M8_R3_PUBLICATION_CLOSURE_0.8.0.json"
            ).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return False

    surfaces = {x["source_id"]: x for x in discovery.get("surfaces", [])}
    families = {x["source_family"]: x for x in config.get("eligibility", [])}
    source = source_gate.get("sources", [{}])[0]
    canonical = pending.get("canonical_state", {})
    requests = {
        x.get("blocker_id"): x for x in pending.get("requests", []) if isinstance(x, dict)
    }
    gate = next(
        (
            x
            for x in automation.get("gates", [])
            if x.get("id") == "TASK_018_FULL_OPERATIONAL_BOOTSTRAP"
        ),
        {},
    )
    required_cloud = {
        "bronze_id",
        "silver_id",
        "gold_id",
        "documentos_id",
        "rag_id",
        "bancos_id",
        "logs_id",
        "outputs_id",
        "quarantine_id",
    }

    expected_boundary = {
        "active": "0.7.0",
        "active_status": "ACTIVE",
        "candidate": "0.8.0",
        "candidate_status": "CANDIDATE",
        "closed_annual_series": "2016-2024",
        "year_2025": "PROVEN_STRUCTURAL_RECENT",
        "S1_NUM_POPU": "NOT_PROVEN",
        "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "gold_2025": "UNKNOWN/BLOCKED",
        "year_2026": "UNPROVEN_CURRENT_YEAR",
        "B1": "PENDING",
        "B2": "PENDING",
        "B3": "PENDING",
    }
    expected_canonical = {
        "release_0_7_0": "ACTIVE",
        "release_0_8_0": "CANDIDATE",
        "year_2025": "PROVEN_STRUCTURAL_RECENT",
        "S1_NUM_POPU": "NOT_PROVEN",
        "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "closed_annual_series": "2016-2024",
        "gold_2025": "UNKNOWN/BLOCKED",
        "year_2026": "UNPROVEN_CURRENT_YEAR",
    }
    request_checks = (
        requests.get("B1_NUM_POPU", {}).get("response_status") == "PENDING",
        requests.get("B2_DOTACAO_EDU", {}).get("response_status") == "PENDING",
        requests.get("B3_EFFECTIVE_DECLARATION", {}).get("response_status") == "PENDING",
        all(
            requests.get(k, {}).get("promotion_effect") == "NONE_WHILE_PENDING"
            for k in ("B1_NUM_POPU", "B2_DOTACAO_EDU", "B3_EFFECTIVE_DECLARATION")
        ),
    )

    return all(
        (
            config.get("release_boundary") == expected_boundary,
            all(canonical.get(k) == v for k, v in expected_canonical.items()),
            *request_checks,
            surfaces.get("LIMEIRA_JORNAL_OFICIAL", {}).get("status")
            == "LIVE_VALIDATED",
            surfaces.get("LIMEIRA_JORNAL_OFICIAL", {}).get(
                "production_collection_enabled"
            )
            is False,
            surfaces.get("LIMEIRA_TDA_PORTAL", {}).get("status")
            == "BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN",
            families.get("LIMEIRA_TDA_PORTAL", {}).get("classification")
            == "BLOCKED_CONTRACT_UNPROVEN",
            families.get("SIOPE_2016_2024", {}).get("classification")
            == "REUSE_ALREADY_PROVEN",
            families.get("SIOPE_2025", {}).get("classification")
            == "BLOCKED_SEMANTIC_UNPROVEN",
            families.get("SIOPE_2026", {}).get("classification")
            == "BLOCKED_CONTRACT_UNPROVEN",
            families.get("LIMEIRA_JORNAL_OFICIAL", {}).get("scope")
            == "DECLARED_LINKS_IN_PROVEN_MODERN_WINDOW_2026_08",
            families.get("LIMEIRA_JORNAL_OFICIAL", {}).get("year") == 2026,
            families.get("LIMEIRA_JORNAL_OFICIAL", {}).get("month") == 8,
            "ecrie.com.br"
            in families.get("LIMEIRA_JORNAL_OFICIAL", {}).get("allowed_hosts", []),
            config.get("hard_safety_ceilings", {}).get(
                "maximum_index_discovery_pages"
            )
            == 50,
            source.get("url", "").startswith("https://ecrie.com.br/"),
            source.get("expected_sha256")
            == "78a23262023f6233cb59fdc78f1fadc196d0a7bbd52c418bbdd9244229f46680",
            source.get("expected_bytes") == 16952899,
            gate.get("auto_allowed") is False,
            gate.get("owner_authorization_required") is True,
            gate.get("schedule") is False,
            gate.get("recurrence") is False,
            gate.get("automatic_retry") is False,
            required_cloud <= set(cloud),
            closure.get("release_status") == "CANDIDATE",
            closure.get("publication_scope") == "SIOPE_HISTORICAL_2016_2024",
            closure.get("include_2025") is False,
            closure.get("release_promotion_performed") is False,
        )
    )


class Budget:
    GET_KEYS = (
        "robots_get_count",
        "index_get_count",
        "document_get_count",
        "reconciliation_get_count",
    )

    def __init__(self, config, started=None):
        self.config = config
        self.started = started or time.monotonic()
        self.counts = {
            "robots_get_count": 0,
            "index_get_count": 0,
            "document_get_count": 0,
            "reconciliation_get_count": 0,
            "total_remote_get_count": 0,
            "source_bytes": 0,
            "drive_create_operations": 0,
        }

    def seed(self, telemetry: dict | None):
        if not telemetry:
            return
        for key in self.GET_KEYS:
            value = int(telemetry.get(key, 0) or 0)
            if value < 0:
                raise RuntimeError("STOP_REMOTE_EFFECT_POLICY")
            self.counts[key] = value
        self.counts["total_remote_get_count"] = sum(
            self.counts[k] for k in self.GET_KEYS
        )
        self.counts["source_bytes"] = int(telemetry.get("source_bytes", 0) or 0)
        self.counts["drive_create_operations"] = int(
            telemetry.get("drive_create_operations", 0) or 0
        )
        if (
            self.counts["total_remote_get_count"]
            > self.config["maximum_total_remote_get_count"]
            or self.counts["index_get_count"]
            > self.config["maximum_index_discovery_pages"]
            or self.counts["document_get_count"] > self.config["maximum_documents"]
            or self.counts["reconciliation_get_count"]
            > self.config["maximum_live_reconciliation_requests"]
            or self.counts["source_bytes"]
            > self.config["maximum_aggregate_source_bytes"]
            or self.counts["drive_create_operations"]
            > self.config["maximum_drive_create_operations"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")

    def add_gets(self, kind, amount):
        if kind not in self.GET_KEYS:
            raise ValueError("UNKNOWN_GET_KIND")
        amount = int(amount)
        if (
            amount < 0
            or self.counts["total_remote_get_count"] + amount
            > self.config["maximum_total_remote_get_count"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        if (
            kind == "index_get_count"
            and self.counts[kind] + amount
            > self.config["maximum_index_discovery_pages"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        if (
            kind == "reconciliation_get_count"
            and self.counts[kind] + amount
            > self.config["maximum_live_reconciliation_requests"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.counts[kind] += amount
        self.counts["total_remote_get_count"] += amount

    def before_document(self):
        if self.counts["document_get_count"] >= self.config["maximum_documents"]:
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.add_gets("document_get_count", 1)

    def accept_source_bytes(self, amount, *, enforce_per_document=True):
        amount = int(amount)
        if enforce_per_document and amount > self.config["maximum_bytes_per_document"]:
            raise RuntimeError("STOP_DOCUMENT_TOO_LARGE")
        if (
            amount < 0
            or self.counts["source_bytes"] + amount
            > self.config["maximum_aggregate_source_bytes"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.counts["source_bytes"] += amount

    def before_create(self):
        if (
            self.counts["drive_create_operations"]
            >= self.config["maximum_drive_create_operations"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        self.counts["drive_create_operations"] += 1

    def runtime_ok(self):
        if (
            time.monotonic() - self.started
            >= self.config["maximum_runtime_seconds"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")


def eligibility_inventory(config):
    allowed = {
        "ELIGIBLE_LIVE_COLLECTION",
        "REUSE_ALREADY_PROVEN",
        "BLOCKED_CONTRACT_UNPROVEN",
        "BLOCKED_SEMANTIC_UNPROVEN",
        "BLOCKED_AUTHORIZATION_SCOPE",
        "NOT_APPLICABLE",
    }
    rows = sorted(config["eligibility"], key=lambda x: x["source_family"])
    if not rows or any(x.get("classification") not in allowed for x in rows):
        raise ValueError("STOP_CANONICAL_POLICY_DRIFT")
    return rows


def deduplicate_discovery(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["logical_key"]].append(row)
    accepted, ambiguous = [], []
    fields = (
        "url",
        "source_id",
        "publication_date",
        "source_page_url",
        "archive_class",
    )
    for key in sorted(grouped):
        group = grouped[key]
        signatures = {tuple(x.get(f) for f in fields) for x in group}
        if len(signatures) != 1:
            ambiguous.append(
                {
                    **group[0],
                    "status": "STOP_DISCOVERY_AMBIGUITY",
                    "conflicting_provenance": [
                        {f: x.get(f) for f in fields} for x in group
                    ],
                }
            )
        else:
            accepted.append(group[0])
    return accepted, ambiguous


def reserve_one_shot(store, authorization: dict, execution: dict):
    stop = validate_authorization(authorization)
    if stop:
        return {"status": stop, "created": False, "batch_id": None}
    attempt = str(execution.get("github_run_attempt") or "")
    run_id = str(execution.get("github_run_id") or "")
    if attempt != "1" or not run_id:
        return {
            "status": "STOP_BATCH_AUTHORIZATION_CONSUMED",
            "created": False,
            "batch_id": batch_identity(authorization),
        }
    batch_id = batch_identity(authorization)
    prior = store.lookup("Logs", batch_id, ".json")
    if prior:
        return {
            "status": "STOP_BATCH_AUTHORIZATION_CONSUMED",
            "created": False,
            "batch_id": batch_id,
        }
    payload = canonical_json(
        {
            "batch_id": batch_id,
            "state": "STARTED",
            "github_run_id": run_id,
            "github_run_attempt": 1,
            "authorization_evidence_identity": authorization_identity(authorization),
        }
    ).encode()
    created = store.create(
        "Logs",
        batch_id + ".json",
        payload,
        {"content_type": "application/json"},
    )
    if created.get("status") != "CREATED":
        return {
            "status": "STOP_BATCH_AUTHORIZATION_CONSUMED",
            "created": False,
            "batch_id": batch_id,
        }
    return {
        "status": "PASS_BATCH_ONE_SHOT_RESERVED",
        "created": True,
        "batch_id": batch_id,
        "marker_name": batch_id + ".json",
    }


def verify_reservation(store, authorization: dict, execution: dict):
    batch_id = batch_identity(authorization)
    marker = store.lookup("Logs", batch_id, ".json")
    if not marker:
        return "STOP_BATCH_RESERVATION_MISSING"
    try:
        payload = json.loads(marker.get("data", b"{}"))
    except (ValueError, UnicodeDecodeError, TypeError):
        return "STOP_BATCH_RESERVATION_MISSING"
    if (
        str(payload.get("github_run_id")) != str(execution.get("github_run_id"))
        or str(payload.get("github_run_attempt")) != "1"
        or str(execution.get("github_run_attempt")) != "1"
        or payload.get("batch_id") != batch_id
    ):
        return "STOP_BATCH_AUTHORIZATION_CONSUMED"
    return None


def _public_item(item: dict) -> dict:
    private = {"bronze_remote_id", "local_name"}
    return {k: v for k, v in item.items() if k not in private}


class BootstrapBatch:
    def __init__(
        self,
        config,
        source,
        store,
        processor,
        *,
        reconciler=None,
        canonical_validator=validate_canonical_projection,
    ):
        self.config = config
        self.source = source
        self.store = store
        self.processor = processor
        self.reconciler = reconciler
        self.canonical_validator = canonical_validator

    def run(
        self,
        output_dir,
        authorization,
        *,
        execution=None,
        initial_telemetry=None,
        initial_items=None,
        initial_effects=None,
        discovered_count=None,
        state_path=None,
        require_reservation=False,
        upstream_partial=False,
        upstream_checkpoint=None,
    ):
        effects = {
            "source_gets": 0,
            "drive_reads": 0,
            "drive_writes": 0,
            "publication_writes": 0,
            "live_reconciliation": 0,
        }
        if initial_effects:
            for key in effects:
                effects[key] = int(initial_effects.get(key, 0) or 0)

        stop = validate_authorization(authorization)
        if stop:
            return self._stopped(stop, effects, output_dir)
        if not self.canonical_validator(self.config):
            return self._stopped("STOP_CANONICAL_POLICY_DRIFT", effects, output_dir)

        execution = execution or {}
        if str(execution.get("github_run_attempt") or "1") != "1":
            return self._stopped(
                "STOP_BATCH_AUTHORIZATION_CONSUMED", effects, output_dir
            )
        if require_reservation:
            reservation_stop = verify_reservation(
                self.store, authorization, execution
            )
            effects["drive_reads"] += 1
            if reservation_stop:
                return self._stopped(reservation_stop, effects, output_dir)

        provenance = {
            "implementation_merge_sha": authorization.get(
                "implementation_merge_sha"
            ),
            "authorization_evidence_identity": authorization_identity(
                authorization
            ),
            **execution,
        }
        batch_id = batch_identity(authorization)
        budget = Budget(self.config["hard_safety_ceilings"])
        try:
            budget.seed(initial_telemetry)
        except RuntimeError as exc:
            return self._stopped(str(exc), effects, output_dir)

        inventory = eligibility_inventory(self.config)
        discovered = []
        items = [_public_item(x) for x in (initial_items or [])]
        tasks = []
        accepted = []
        state_path = Path(
            state_path or (Path(output_dir).parent / "task-018-state.sqlite")
        )

        try:
            for family in inventory:
                if family["classification"] != "ELIGIBLE_LIVE_COLLECTION":
                    continue
                rows, telemetry = self.source.discover(
                    family,
                    budget.config["maximum_index_discovery_pages"],
                )
                for key in ("robots_get_count", "index_get_count"):
                    amount = int(telemetry.get(key, 0) or 0)
                    if amount:
                        budget.add_gets(key, amount)
                        effects["source_gets"] += amount
                discovered.extend(rows)

            accepted, ambiguous = deduplicate_discovery(discovered)
            items.extend(_public_item(x) for x in ambiguous)

            for item in accepted:
                budget.runtime_ok()
                logical = item["logical_key"]
                data = None

                if item.get("bronze_remote_id") and hasattr(
                    self.store, "get_by_id"
                ):
                    existing = self.store.get_by_id(
                        item["bronze_remote_id"], cache_key=logical
                    )
                    effects["drive_reads"] += 1
                    data = existing["data"]
                    if (
                        item.get("expected_sha256")
                        and existing.get("sha256") != item["expected_sha256"]
                    ):
                        items.append(
                            {
                                **_public_item(item),
                                "status": "STOP_DOCUMENT_HASH_COLLISION",
                            }
                        )
                        continue
                    item["bronze_state"] = "REUSED_IDENTICAL"
                else:
                    existing = self.store.lookup("Bronze", logical, ".pdf")
                    effects["drive_reads"] += 1
                    if existing:
                        data = existing.get("data")
                        item["bronze_state"] = "REUSED_IDENTICAL"
                        if getattr(self.source, "is_staged", False):
                            staged, staged_meta = self.source.get(
                                item["url"],
                                budget.config["maximum_bytes_per_document"],
                            )
                            if hashlib.sha256(staged).hexdigest() != existing.get(
                                "sha256"
                            ):
                                items.append(
                                    {
                                        **_public_item(item),
                                        "status": "STOP_DOCUMENT_HASH_COLLISION",
                                    }
                                )
                                continue
                            data = existing.get("data") or staged
                    else:
                        remote = not getattr(self.source, "is_staged", False)
                        if remote:
                            budget.before_document()
                            effects["source_gets"] += 1
                        try:
                            data, meta = self.source.get(
                                item["url"],
                                budget.config["maximum_bytes_per_document"],
                            )
                        except Exception:
                            items.append(
                                {
                                    **_public_item(item),
                                    "status": "STOP_DOCUMENT_FETCH",
                                }
                            )
                            continue

                        remote_get_count = int(
                            meta.get("remote_get_count", 1 if remote else 0) or 0
                        )
                        if remote and remote_get_count != 1:
                            raise RuntimeError("STOP_REMOTE_EFFECT_POLICY")

                        if remote:
                            if (
                                len(data)
                                > budget.config["maximum_bytes_per_document"]
                            ):
                                budget.accept_source_bytes(
                                    len(data), enforce_per_document=False
                                )
                                items.append(
                                    {
                                        **_public_item(item),
                                        "status": "STOP_DOCUMENT_TOO_LARGE",
                                    }
                                )
                                continue
                            budget.accept_source_bytes(
                                len(data), enforce_per_document=True
                            )

                        host = (meta.get("final_host") or "").lower()
                        if (
                            not meta.get("https")
                            or host not in item["allowed_hosts"]
                        ):
                            items.append(
                                {
                                    **_public_item(item),
                                    "status": "STOP_DOCUMENT_HOST_UNPROVEN",
                                }
                            )
                            continue
                        if (
                            not data.startswith(b"%PDF")
                            or meta.get("content_type") != "application/pdf"
                        ):
                            items.append(
                                {
                                    **_public_item(item),
                                    "status": "STOP_DOCUMENT_NOT_PDF",
                                }
                            )
                            continue

                        digest = hashlib.sha256(data).hexdigest()
                        if (
                            item.get("expected_sha256")
                            and digest != item["expected_sha256"]
                        ):
                            items.append(
                                {
                                    **_public_item(item),
                                    "status": "STOP_DOCUMENT_HASH_COLLISION",
                                }
                            )
                            continue
                        budget.before_create()
                        created = self.store.create(
                            "Bronze",
                            logical.replace("/", "_") + ".pdf",
                            data,
                            {
                                "content_type": "application/pdf",
                                "logical_key": logical,
                                "source_url": item["url"],
                                "sha256": digest,
                            },
                        )
                        effects["drive_writes"] += (
                            created.get("status") == "CREATED"
                        )
                        item["bronze_state"] = created.get("status")

                if data is None:
                    items.append(
                        {
                            **_public_item(item),
                            "status": "STOP_DOCUMENT_FETCH",
                        }
                    )
                    continue

                try:
                    derived = self.processor.process(item, data)
                except Exception as exc:
                    status = getattr(exc, "status", "STOP_SCHEMA_UNKNOWN")
                    budget.before_create()
                    q = self.store.create(
                        "Quarantine",
                        logical.replace("/", "_") + ".json",
                        canonical_json(
                            {"logical_key": logical, "status": status}
                        ).encode(),
                        {"content_type": "application/json"},
                    )
                    effects["drive_writes"] += q.get("status") == "CREATED"
                    items.append(
                        {
                            **_public_item(item),
                            "status": (
                                status
                                if status in ITEM_LOCAL_STOPS
                                else "QUARANTINED"
                            ),
                        }
                    )
                    continue

                layer_states = Counter()
                for destination, objects in derived.get("layers", {}).items():
                    if destination == "Bancos":
                        raise RuntimeError("STOP_CANONICAL_POLICY_DRIFT")
                    for name, payload in objects:
                        budget.before_create()
                        record = self.store.create(
                            destination,
                            name,
                            payload,
                            {
                                "content_type": (
                                    "application/x-ndjson"
                                    if name.endswith(".jsonl")
                                    else "application/json"
                                ),
                                "source_sha256": hashlib.sha256(data).hexdigest(),
                            },
                        )
                        layer_states[
                            destination + "_" + record["status"]
                        ] += 1
                        effects["drive_writes"] += (
                            record["status"] == "CREATED"
                        )
                tasks.extend(derived.get("tasks", []))
                items.append(
                    {
                        **_public_item(item),
                        "status": "PASS_ITEM",
                        "bronze_state": item.get("bronze_state"),
                        "layer_states": dict(layer_states),
                        "metrics": derived.get("metrics", {}),
                    }
                )

            self._upsert_tasks_state(state_path, tasks, batch_id)
            rec = self._reconcile(
                tasks, budget, effects, Path(output_dir), state_path
            )
            state_snapshot = self._persist_state_snapshot(
                state_path, batch_id, budget, effects
            )
            status = (
                "PARTIAL_BATCH_SAFETY_BUDGET_REACHED"
                if upstream_partial
                else "COMPLETE"
            )

        except RuntimeError as exc:
            if str(exc) != "PARTIAL_BATCH_SAFETY_BUDGET_REACHED":
                raise
            status = str(exc)
            rec = {
                "status": "NOT_EXECUTED_SAFETY_BUDGET",
                "tasks": len(tasks),
                "requests": budget.counts["reconciliation_get_count"],
                "status_counts": {},
            }
            state_snapshot = {"status": "NOT_PERSISTED_SAFETY_BUDGET"}

        terminal_keys = {
            x["logical_key"] for x in items if isinstance(x, dict) and x.get("logical_key")
        }
        checkpoint = sorted(
            set(upstream_checkpoint or [])
            | {
                x["logical_key"]
                for x in accepted
                if x["logical_key"] not in terminal_keys
            }
        )
        snapshot_payload = {
            "inventory": inventory,
            "items": items,
            "reconciliation": rec,
            "checkpoint": checkpoint,
            "state_snapshot": state_snapshot,
        }
        snapshot_id = identity("SNAP-", snapshot_payload)
        run_id = identity(
            "RUN-",
            {
                "snapshot_id": snapshot_id,
                "github_run_id": execution.get("github_run_id"),
                "github_run_attempt": execution.get("github_run_attempt"),
            },
        )
        result = {
            "status": status,
            "systemic_stop": False,
            "batch_id": batch_id,
            "snapshot_id": snapshot_id,
            "run_id": run_id,
            **provenance,
            "inventory": inventory,
            "discovered_count": (
                int(discovered_count)
                if discovered_count is not None
                else len(discovered) + len(initial_items or [])
            ),
            "items": items,
            "reconciliation": rec,
            "state_snapshot": state_snapshot,
            "telemetry": budget.counts,
            "effects": effects,
            "checkpoint": {"remaining_logical_keys": checkpoint},
            "publication": {"status": "NOT_EXECUTED", "objects": []},
        }
        out = Path(output_dir)
        self._product(out, result)
        return result

    @staticmethod
    def _upsert_tasks_state(state_path: Path, tasks, batch_id):
        with StateRegistry(state_path) as state:
            state.set_meta("TASK_018_BATCH_ID", batch_id)
            for task in tasks:
                state.upsert_reconciliation_task(task)

    def _reconcile(self, tasks, budget, effects, work, state_path):
        task_ids = {x.get("task_id") for x in tasks}
        with StateRegistry(state_path) as state:
            ready = [
                x
                for x in state.list_reconciliation_tasks(status="READY_SEARCH")
                if x["task_id"] in task_ids
            ]

        eligible = [
            x for x in ready if x.get("target_source") == "LIMEIRA_CONTRATOS"
        ]
        blocked = len(ready) - len(eligible)
        if not eligible:
            return {
                "status": "NOT_EXECUTED_NO_ELIGIBLE_TASK",
                "tasks": len(tasks),
                "blocked": blocked,
                "requests": 0,
                "status_counts": {},
            }
        if self.reconciler is None:
            return {
                "status": "BLOCKED_RECONCILIATION_CONTRACT",
                "tasks": len(tasks),
                "blocked": len(tasks),
                "requests": 0,
                "status_counts": {},
            }

        results = []
        for task in eligible:
            remaining = min(
                budget.config["maximum_live_reconciliation_requests"]
                - budget.counts["reconciliation_get_count"],
                budget.config["maximum_total_remote_get_count"]
                - budget.counts["total_remote_get_count"],
            )
            if remaining <= 0:
                raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
            response = self.reconciler.execute(
                task, work / "reconciliation" / task["task_id"], remaining
            )
            result, actual = (
                response if isinstance(response, tuple) else (response, 1)
            )
            budget.add_gets("reconciliation_get_count", actual)
            effects["live_reconciliation"] += actual
            results.append(result)
            with StateRegistry(state_path) as state:
                state.update_reconciliation_task(
                    task["task_id"], result["status"], result
                )

        return {
            "status": "PASS_RECONCILIATION_EXECUTION",
            "tasks": len(tasks),
            "blocked": blocked,
            "requests": budget.counts["reconciliation_get_count"],
            "status_counts": dict(Counter(x["status"] for x in results)),
            "results": results,
            "financial_identity_auto_promotion": "PROHIBITED",
        }

    def _persist_state_snapshot(self, state_path, batch_id, budget, effects):
        if not state_path.exists():
            return {"status": "NOT_AVAILABLE"}
        budget.before_create()
        name = batch_id + "__ROBOT_STATE.sqlite"
        record = self.store.create(
            "Bancos",
            name,
            state_path.read_bytes(),
            {"content_type": "application/x-sqlite3"},
        )
        effects["drive_writes"] += record.get("status") == "CREATED"
        return {
            "status": record.get("status"),
            "name": name,
            "schema": "StateRegistry",
        }

    def publish(self, output_dir, result):
        product = Path(output_dir) / "product"
        manifest = json.loads(
            (product / "manifest.json").read_text(encoding="utf-8")
        )
        names = [x["name"] for x in manifest["files"]]
        if "manifest.json" in names:
            raise RuntimeError("STOP_MANIFEST_INTEGRITY")

        prefix = result["batch_id"] + "_"
        published = []
        for name in sorted(names):
            if (
                result["telemetry"]["drive_create_operations"]
                >= self.config["hard_safety_ceilings"][
                    "maximum_drive_create_operations"
                ]
            ):
                raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
            data = (product / name).read_bytes()
            record = self.store.create(
                "Outputs",
                prefix + name,
                data,
                {"content_type": "application/octet-stream"},
            )
            published.append(record)
            result["effects"]["publication_writes"] += (
                record["status"] == "CREATED"
            )
            result["telemetry"]["drive_create_operations"] += (
                record["status"] == "CREATED"
            )

        if (
            result["telemetry"]["drive_create_operations"]
            >= self.config["hard_safety_ceilings"]["maximum_drive_create_operations"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        manifest_data = (product / "manifest.json").read_bytes()
        final = self.store.create(
            "Outputs",
            prefix + "manifest.json",
            manifest_data,
            {"content_type": "application/json"},
        )
        published.append(final)
        result["effects"]["publication_writes"] += final["status"] == "CREATED"
        result["telemetry"]["drive_create_operations"] += (
            final["status"] == "CREATED"
        )

        remote_names = [prefix + x for x in sorted(names)] + [
            prefix + "manifest.json"
        ]
        for name in remote_names:
            self.store.readback("Outputs", name)

        result["publication"] = {
            "status": "PUBLISHED_CREATE_ONLY_READBACK_VERIFIED",
            "objects": remote_names,
            "manifest_written_last": True,
            "final_readback_required": True,
            "batch_status": result["status"],
        }

        completion_name = result["batch_id"] + "_PUBLICATION_COMPLETED.json"
        if (
            result["telemetry"]["drive_create_operations"]
            >= self.config["hard_safety_ceilings"]["maximum_drive_create_operations"]
        ):
            raise RuntimeError("PARTIAL_BATCH_SAFETY_BUDGET_REACHED")
        completion = self.store.create(
            "Logs",
            completion_name,
            canonical_json(
                {
                    "batch_id": result["batch_id"],
                    "run_id": result["run_id"],
                    "publication": "COMPLETE",
                    "batch_status": result["status"],
                }
            ).encode(),
            {"content_type": "application/json"},
        )
        result["effects"]["drive_writes"] += completion["status"] == "CREATED"
        result["telemetry"]["drive_create_operations"] += (
            completion["status"] == "CREATED"
        )
        (Path(output_dir) / "operational_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self._audit(Path(output_dir), result)
        return result

    def _product(self, out, result):
        if out.exists():
            raise FileExistsError("STOP_CREATE_ONLY_INVARIANT")
        out.mkdir(parents=True)
        counts = self._counts(result)
        answer = AnswerContract(
            "ANSWERED",
            "TASK 018 bounded inventory",
            canonical_json(counts),
            "MATCH_CANDIDATE is candidate-only.",
            "Blocked/quarantined states remain explicit.",
            "Presentation is not evidence.",
            tuple(),
        )
        report = build_product_report(
            [answer],
            report_id=result["run_id"],
            title="Full operational bootstrap",
            scope=self.config["authorization_scope"],
            generated_at=datetime.now(timezone.utc).isoformat(),
            limitations=("MATCH_CANDIDATE is not financial identity.",),
            notes=(
                f"Batch status: {result['status']}; "
                "0.7.0 ACTIVE; 0.8.0 CANDIDATE"
            ),
            software_version="0.8.0",
        )
        write_product_bundle(report, out / "product")
        (out / "operational_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out / "operational_summary.md").write_text(
            self._summary(result, counts), encoding="utf-8"
        )
        self._audit(out, result)

    def _counts(self, r):
        statuses = Counter(x["status"] for x in r["items"])
        layers = Counter()
        for x in r["items"]:
            layers.update(x.get("layer_states", {}))
        classes = Counter(x["classification"] for x in r["inventory"])
        return {
            "families_considered": len(r["inventory"]),
            "family_classifications": dict(classes),
            "discovered": r["discovered_count"],
            "already_proven": sum(
                x.get("bronze_state") == "REUSED_IDENTICAL" for x in r["items"]
            ),
            "downloaded": r["telemetry"]["document_get_count"],
            "bronze_created": sum(
                x.get("bronze_state") == "CREATED" for x in r["items"]
            ),
            "bronze_reused": sum(
                x.get("bronze_state") == "REUSED_IDENTICAL"
                for x in r["items"]
            ),
            "processed": statuses["PASS_ITEM"],
            "derived": dict(layers),
            "item_local_failures": sum(
                x.get("status") in ITEM_LOCAL_STOPS for x in r["items"]
            ),
            "ocr_required": statuses["STOP_OCR_REQUIRED"],
            "schema_unknown": statuses["STOP_SCHEMA_UNKNOWN"],
            "document_fetch_failures": statuses["STOP_DOCUMENT_FETCH"],
            "document_too_large": statuses["STOP_DOCUMENT_TOO_LARGE"],
            "discovery_ambiguities": statuses["STOP_DISCOVERY_AMBIGUITY"],
            "item_local_stops": dict(statuses),
            "reconciliation_tasks": r["reconciliation"]["tasks"],
            "reconciliation_requests": r["reconciliation"]["requests"],
            "match_candidate": r["reconciliation"]["status_counts"].get(
                "MATCH_CANDIDATE", 0
            ),
            "state_snapshot": r["state_snapshot"],
            "budget": r["telemetry"],
            "checkpoint": r["checkpoint"],
            "systemic_stop": r["systemic_stop"],
            "publication": r["publication"],
        }

    @staticmethod
    def _summary(r, c):
        payload = {
            "status": r["status"],
            "batch_id": r["batch_id"],
            "snapshot_id": r["snapshot_id"],
            "run_id": r["run_id"],
            **c,
        }
        return "# TASK 018 operational summary\n\n" + "\n".join(
            f"- **{k}:** `{canonical_json(v)}`" for k, v in payload.items()
        ) + "\n"

    @staticmethod
    def _audit(out, result):
        audit = out.parent / "task-018-audit"
        audit.mkdir(parents=True, exist_ok=True)
        (audit / "operational_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        summary = out / "operational_summary.md"
        if summary.exists():
            (audit / "operational_summary.md").write_text(
                summary.read_text(encoding="utf-8"), encoding="utf-8"
            )

    def _stopped(self, status, effects, output_dir):
        result = {
            "status": status,
            "systemic_stop": True,
            "effects": effects,
            "items": [],
            "telemetry": {
                k: 0
                for k in (
                    "robots_get_count",
                    "index_get_count",
                    "document_get_count",
                    "reconciliation_get_count",
                    "total_remote_get_count",
                    "source_bytes",
                    "drive_create_operations",
                )
            },
        }
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "operational_result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        self._audit(out, result)
        return result
