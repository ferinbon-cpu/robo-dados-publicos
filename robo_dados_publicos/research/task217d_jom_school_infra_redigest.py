from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

from robo_dados_publicos.analytics.task217_jom_school_identity_bridge import (
    normalize_text,
)
from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.operational.bootstrap_adapters import JornalSourceAdapter
from robo_dados_publicos.research.task217b_jom_2026_school_infrastructure_expansion import (
    adjudicate_event_rows,
    build_discovery_plan,
    screen_page_text,
)
from robo_dados_publicos.research.task217c_jom_2026_discovery_runtime import (
    LiveJournalDiscoverySource,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task217d_jom_school_infra_redigest.v1.json"


class Task217DStop(RuntimeError):
    pass


class DiscoverySource(Protocol):
    network_capable: bool
    def discover_month(self, year: int, month: int, *, max_pages: int) -> dict[str, Any]: ...


class DocumentSource(Protocol):
    network_capable: bool
    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict[str, Any]]: ...


class LiveDocumentSource:
    network_capable = True

    def __init__(self):
        self.adapter = JornalSourceAdapter()

    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict[str, Any]]:
        return self.adapter.get(url, maximum_bytes)


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task217DStop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK217D_JOM_SCHOOL_INFRA_REDIGEST_V1", "TASK217D_SCHEMA")
    _stop(obj.get("issue") == 680, "TASK217D_ISSUE")
    _stop(
        obj.get("base_main_sha") == "3951b2178006a136102cf62f21699f0a6608cfd8",
        "TASK217D_BASE",
    )
    parts = obj["partitions"]
    editions = [edition for rows in parts.values() for edition in rows]
    _stop(len(editions) == 87, "TASK217D_PARTITION_COUNT")
    _stop(len(set(editions)) == 87, "TASK217D_PARTITION_DUPLICATE")
    _stop(not set(editions).intersection(obj["canonical_discovery"]["existing_editions"]), "TASK217D_EXISTING_OVERLAP")
    _stop(obj["network"]["max_document_download_count"] == 87, "TASK217D_DOWNLOAD_COUNT")
    _stop(obj["network"]["max_total_remote_get_count"] == 105, "TASK217D_REMOTE_BOUND")
    _stop(obj["network"]["automatic_retry"] is False, "TASK217D_RETRY")
    _stop(obj["processing"]["raw_pdf_persisted"] is False, "TASK217D_RAW_PDF")
    _stop(obj["processing"]["raw_page_text_persisted"] is False, "TASK217D_RAW_PAGE")
    _stop(obj["authorization"]["live_authorized"] is False, "TASK217D_LIVE_DEFAULT")
    _stop(obj["authorization"]["task018_authorization_reuse_allowed"] is False, "TASK217D_TASK018")
    _stop(obj["promotion"]["runtime_may_promote"] is False, "TASK217D_RUNTIME_PROMOTION")
    _stop(all(v is False for v in obj["pre_authorization_remote_effects"].values()), "TASK217D_T0_EFFECTS")
    return obj


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def reconstruct_discovery(
    source: DiscoverySource,
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    reports = [
        source.discover_month(2026, month, max_pages=int(cfg["network"]["max_index_pages_per_month"]))
        for month in range(1, 10)
    ]
    plan = build_discovery_plan(reports)
    result = {
        "schema": "TASK217C_JOM_2026_DISCOVERY_RESULT_V1",
        "status": "PASS_COMPLETE_2026_JOM_DISCOVERY_READY_FOR_REDIGEST",
        "complete_scope": True,
        "scope": plan["scope"],
        "total_index_pages": plan["total_index_pages"],
        "estimated_remote_get_count": plan["total_index_pages"] * 2,
        "document_count": plan["document_count"],
        "documents": plan["documents"],
        "document_download_count": 0,
        "raw_html_persisted": False,
        "raw_pdf_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "absence_inference_allowed": False,
        "next_step": "TASK_217D_BOUNDED_DOCUMENT_REDIGEST_REQUIRES_SEPARATE_CANONIZED_SCOPE",
    }
    observed = _canonical_sha(result)
    _stop(
        observed == cfg["canonical_discovery"]["result_sha256"],
        "TASK217D_DISCOVERY_HASH_DRIFT",
    )
    _stop(result["document_count"] == cfg["canonical_discovery"]["document_count"], "TASK217D_DISCOVERY_COUNT")
    return result


def select_new_documents(
    discovery_result: Mapping[str, Any],
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> list[dict[str, Any]]:
    cfg = load_config(config_path)
    existing = set(cfg["canonical_discovery"]["existing_editions"])
    docs = [dict(row) for row in discovery_result["documents"] if int(row["edition"]) not in existing]
    _stop(len(docs) == cfg["canonical_discovery"]["new_document_count"], "TASK217D_NEW_DOC_COUNT")
    expected = {edition for rows in cfg["partitions"].values() for edition in rows}
    observed = {int(row["edition"]) for row in docs}
    _stop(observed == expected, "TASK217D_NEW_DOC_IDENTITIES")
    return docs


def partition_id_for_edition(edition: int, *, config_path: str | Path = DEFAULT_CONFIG) -> str:
    cfg = load_config(config_path)
    for partition_id, editions in cfg["partitions"].items():
        if int(edition) in editions:
            return partition_id
    raise Task217DStop("TASK217D_EDITION_NOT_IN_PARTITION")


def _bounded_excerpt(text: str, terms: list[str], max_chars: int) -> str:
    compact = " ".join(str(text or "").split())
    if not compact:
        return ""
    folded = normalize_text(compact)
    positions = []
    for term in terms:
        pos = folded.find(normalize_text(term))
        if pos >= 0:
            positions.append(pos)
    center = min(positions) if positions else 0
    start = max(0, center - max_chars // 3)
    end = min(len(compact), start + max_chars)
    return compact[start:end].strip()


def screen_derived_rows(
    page_rows: list[Mapping[str, Any]],
    event_rows: list[Mapping[str, Any]],
    *,
    excerpt_max_chars: int = 600,
) -> dict[str, Any]:
    page_candidates = []
    for row in page_rows:
        screen = screen_page_text(str(row.get("text_redacted") or ""))
        if not screen["candidate_page"]:
            continue
        terms = (
            list(screen["infrastructure_markers"])
            + list(screen["generic_school_markers"])
        )
        page_candidates.append(
            {
                "source_id": row.get("source_id"),
                "edition": row.get("edition"),
                "publication_date": row.get("publication_date"),
                "page_number": row.get("page_number"),
                "source_sha256": row.get("source_sha256"),
                "organ_hint": row.get("organ_hint"),
                "exact_school_codes_present": screen["exact_school_codes_present"],
                "generic_school_markers": screen["generic_school_markers"],
                "infrastructure_markers": screen["infrastructure_markers"],
                "excerpt_redacted": _bounded_excerpt(
                    str(row.get("text_redacted") or ""),
                    terms,
                    excerpt_max_chars,
                ),
                "page_screening_created_school_identity": False,
            }
        )
    adjudicated = adjudicate_event_rows([dict(row) for row in event_rows])
    event_by_id = {str(row.get("event_id")): row for row in event_rows}

    def enrich(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for row in rows:
            source = event_by_id.get(str(row.get("event_id"))) or {}
            terms = list(row.get("infrastructure_markers") or [])
            resolved = row.get("resolved_school") or {}
            if resolved.get("school_name"):
                terms.append(str(resolved["school_name"]))
            terms.extend(row.get("generic_school_markers") or [])
            out.append(
                {
                    **row,
                    "event_type": source.get("event_type"),
                    "organ": source.get("organ"),
                    "act_number": source.get("act_number"),
                    "contract_number": source.get("contract_number"),
                    "process_number": source.get("process_number"),
                    "source_url": source.get("source_url"),
                    "evidence_excerpt_redacted": _bounded_excerpt(
                        str(source.get("excerpt_redacted") or ""),
                        terms,
                        excerpt_max_chars,
                    ),
                    "raw_object_text_persisted": False,
                }
            )
        return out

    exact_events = enrich(
        adjudicated["resolved_exact_school_infrastructure_events"]
    )
    generic_events = enrich(
        adjudicated["generic_unassigned_school_infrastructure_events"]
    )
    return {
        "page_candidates": page_candidates,
        "resolved_exact_school_infrastructure_events": exact_events,
        "generic_unassigned_school_infrastructure_events": generic_events,
        "counts": {
            "page_candidate_count": len(page_candidates),
            "resolved_exact_school_infrastructure_count": len(exact_events),
            "generic_unassigned_school_infrastructure_count": len(generic_events),
        },
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def process_document(
    item: Mapping[str, Any],
    data: bytes,
    *,
    processor: JournalPdfProcessor | None = None,
    excerpt_max_chars: int = 600,
) -> dict[str, Any]:
    processor = processor or JournalPdfProcessor()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pdf = root / "source.pdf"
        pdf.write_bytes(data)
        out = root / "derived"
        manifest = processor.process(
            pdf,
            edition=int(item["edition"]),
            publication_date=item.get("publication_date"),
            source_url=item.get("document_url"),
            out_dir=out,
            stage_bronze=False,
            plan_reconciliation=False,
            emit_semantic_facets=False,
        )
        summary = {
            "source_id": item.get("source_id"),
            "edition": int(item["edition"]),
            "publication_date": item.get("publication_date"),
            "source_url": item.get("document_url"),
            "source_sha256": manifest.get("source_sha256"),
            "processing_status": manifest.get("status"),
            "text_extraction": manifest.get("text_extraction"),
            "silver_pages": manifest.get("silver_pages"),
            "gold_events": manifest.get("gold_events"),
        }
        if manifest.get("status") != "PASS_DOCUMENT_PROCESSING":
            return {
                "status": "DOCUMENT_NOT_FULLY_PROCESSABLE",
                "summary": summary,
                "screen": {
                    "page_candidates": [],
                    "resolved_exact_school_infrastructure_events": [],
                    "generic_unassigned_school_infrastructure_events": [],
                    "counts": {
                        "page_candidate_count": 0,
                        "resolved_exact_school_infrastructure_count": 0,
                        "generic_unassigned_school_infrastructure_count": 0,
                    },
                },
            }
        screened = screen_derived_rows(
            _read_jsonl(out / "pages_silver.jsonl"),
            _read_jsonl(out / "events_gold.jsonl"),
            excerpt_max_chars=excerpt_max_chars,
        )
        return {"status": "PASS_DOCUMENT", "summary": summary, "screen": screened}


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    if not authorization:
        return {"status": "STOP_LIVE_NOT_AUTHORIZED"}
    if authorization.get("task") == "TASK_018" or authorization.get("task018_authorization_reused") is True:
        return {"status": "STOP_TASK018_AUTHORIZATION_REUSE"}
    if authorization.get("synthetic_test_only") is True:
        return {"status": "STOP_SYNTHETIC_AUTHORIZATION_NOT_OPERATIONAL"}
    if not re.fullmatch(r"[0-9a-f]{40}", expected_implementation_sha or ""):
        return {"status": "STOP_IMPLEMENTATION_SHA_FORMAT"}
    required = {
        "task": cfg["authorization"]["required_task"],
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "implementation_branch": "main",
        "runtime_branch": cfg["runtime"]["branch"],
        "implementation_sha": expected_implementation_sha,
        "source": "LIMEIRA_JORNAL_OFICIAL",
        "operation": cfg["authorization"]["required_operation"],
        "canonical_discovery_result_sha256": cfg["canonical_discovery"]["result_sha256"],
        "max_index_remote_get_count": cfg["network"]["max_index_remote_get_count"],
        "max_document_download_count": cfg["network"]["max_document_download_count"],
        "max_total_remote_get_count": cfg["network"]["max_total_remote_get_count"],
        "max_bytes_per_document": cfg["network"]["max_bytes_per_document"],
        "max_aggregate_document_bytes": cfg["network"]["max_aggregate_document_bytes"],
        "attempt_count": 1,
        "owner_authorized": True,
        "task018_authorization_reused": False,
        "document_downloads_authorized": True,
        "drive_write_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        return {"status": "STOP_LIVE_AUTHORIZATION_CONTRACT_MISMATCH"}
    return {"status": "PASS_LIVE_AUTHORIZATION"}


def _validate_download(
    item: Mapping[str, Any],
    data: bytes,
    meta: Mapping[str, Any],
    *,
    cfg: Mapping[str, Any],
) -> None:
    _stop(meta.get("https") is True, "TASK217D_DOWNLOAD_HTTPS")
    _stop(meta.get("final_host") == cfg["network"]["allowed_document_host"], "TASK217D_DOWNLOAD_HOST")
    _stop(meta.get("content_type") == "application/pdf", "TASK217D_DOWNLOAD_CONTENT_TYPE")
    _stop(int(meta.get("remote_get_count") or 0) == 1, "TASK217D_DOWNLOAD_GET_COUNT")
    _stop(len(data) <= int(cfg["network"]["max_bytes_per_document"]), "TASK217D_DOCUMENT_BYTES")
    parsed = urlparse(str(item.get("document_url") or ""))
    _stop(parsed.scheme == "https", "TASK217D_DECLARED_URL_HTTPS")
    _stop((parsed.hostname or "").lower() == cfg["network"]["allowed_document_host"], "TASK217D_DECLARED_URL_HOST")


def execute_redigest(
    config: Mapping[str, Any],
    *,
    discovery_source: DiscoverySource,
    document_source: DocumentSource,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
    processor: JournalPdfProcessor | None = None,
) -> dict[str, Any]:
    if offline_test_mode:
        if getattr(discovery_source, "network_capable", True) or getattr(document_source, "network_capable", True):
            return {"status": "STOP_OFFLINE_TEST_NETWORK_CAPABLE", "complete_scope": False}
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return {"status": "STOP_OFFLINE_TEST_AUTHORIZATION", "complete_scope": False}
    else:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
        )
        if auth["status"] != "PASS_LIVE_AUTHORIZATION":
            return {**auth, "complete_scope": False}
        if not getattr(discovery_source, "network_capable", False):
            return {"status": "STOP_LIVE_DISCOVERY_SOURCE_NOT_NETWORK_CAPABLE", "complete_scope": False}
        if not getattr(document_source, "network_capable", False):
            return {"status": "STOP_LIVE_DOCUMENT_SOURCE_NOT_NETWORK_CAPABLE", "complete_scope": False}

    try:
        discovery = reconstruct_discovery(discovery_source)
        documents = select_new_documents(discovery)
    except Exception as exc:
        return {
            "schema": "TASK217D_REDIGEST_RESULT_V1",
            "status": "STOP_DISCOVERY_RECONSTRUCTION",
            "complete_scope": False,
            "error_class": type(exc).__name__,
            "document_download_count": 0,
            "absence_inference_allowed": False,
            "promotion_performed": False,
        }

    cfg = dict(config)
    aggregate_bytes = 0
    download_count = 0
    document_get_attempt_count = 0
    document_results = []
    failures = []

    for item in documents:
        edition = int(item["edition"])
        partition_id = partition_id_for_edition(edition)
        try:
            document_get_attempt_count += 1
            _stop(
                document_get_attempt_count <= int(cfg["network"]["max_document_download_count"]),
                "TASK217D_DOWNLOAD_ATTEMPT_BUDGET",
            )
            data, meta = document_source.get(
                str(item["document_url"]),
                int(cfg["network"]["max_bytes_per_document"]),
            )
            _validate_download(item, data, meta, cfg=cfg)
            download_count += int(meta.get("remote_get_count") or 0)
            aggregate_bytes += len(data)
            _stop(download_count <= int(cfg["network"]["max_document_download_count"]), "TASK217D_DOWNLOAD_BUDGET")
            _stop(aggregate_bytes <= int(cfg["network"]["max_aggregate_document_bytes"]), "TASK217D_AGGREGATE_BYTES")
            processed = process_document(
                item,
                data,
                processor=processor,
                excerpt_max_chars=int(cfg["processing"]["candidate_excerpt_max_chars"]),
            )
            record = {
                "partition_id": partition_id,
                **processed["summary"],
                "screen": processed["screen"],
            }
            document_results.append(record)
            if processed["status"] != "PASS_DOCUMENT":
                failures.append(
                    {
                        "edition": edition,
                        "partition_id": partition_id,
                        "reason": processed["summary"].get("processing_status"),
                    }
                )
        except Exception as exc:
            failures.append(
                {
                    "edition": edition,
                    "partition_id": partition_id,
                    "reason": type(exc).__name__,
                }
            )
            document_results.append(
                {
                    "partition_id": partition_id,
                    "edition": edition,
                    "publication_date": item.get("publication_date"),
                    "source_id": item.get("source_id"),
                    "source_url": item.get("document_url"),
                    "processing_status": "STOP_EXCEPTION",
                    "error_class": type(exc).__name__,
                    "screen": {
                        "page_candidates": [],
                        "resolved_exact_school_infrastructure_events": [],
                        "generic_unassigned_school_infrastructure_events": [],
                        "counts": {
                            "page_candidate_count": 0,
                            "resolved_exact_school_infrastructure_count": 0,
                            "generic_unassigned_school_infrastructure_count": 0,
                        },
                    },
                }
            )

    exact_events = [
        event
        for row in document_results
        for event in row.get("screen", {}).get("resolved_exact_school_infrastructure_events", [])
    ]
    generic_events = [
        event
        for row in document_results
        for event in row.get("screen", {}).get("generic_unassigned_school_infrastructure_events", [])
    ]
    page_candidates = [
        page
        for row in document_results
        for page in row.get("screen", {}).get("page_candidates", [])
    ]

    complete = len(document_results) == 87 and not failures
    return {
        "schema": "TASK217D_REDIGEST_RESULT_V1",
        "status": (
            "PASS_COMPLETE_87_DOCUMENT_REDIGEST"
            if complete
            else "PARTIAL_DOCUMENT_FAILURES_NO_ABSENCE_INFERENCE"
        ),
        "complete_scope": complete,
        "canonical_discovery_result_sha256": cfg["canonical_discovery"]["result_sha256"],
        "discovered_document_count": discovery["document_count"],
        "excluded_existing_document_count": len(cfg["canonical_discovery"]["existing_editions"]),
        "target_document_count": len(documents),
        "document_get_attempt_count": document_get_attempt_count,
        "document_download_count": download_count,
        "estimated_total_remote_get_count": (
            int(discovery.get("estimated_remote_get_count") or 0)
            + document_get_attempt_count
        ),
        "aggregate_document_bytes": aggregate_bytes,
        "document_results": document_results,
        "failures": failures,
        "counts": {
            "processed_document_result_count": len(document_results),
            "failure_count": len(failures),
            "page_candidate_count": len(page_candidates),
            "resolved_exact_school_infrastructure_event_count": len(exact_events),
            "generic_unassigned_school_infrastructure_event_count": len(generic_events),
        },
        "resolved_exact_school_infrastructure_events": exact_events,
        "generic_unassigned_school_infrastructure_events": generic_events,
        "page_candidates": page_candidates,
        "raw_pdf_persisted": False,
        "raw_page_text_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "absence_inference_allowed": False,
        "canonization_required": bool(exact_events) or complete,
        "remote_get_budget_respected": (
            int(discovery.get("estimated_remote_get_count") or 0)
            + document_get_attempt_count
            <= int(cfg["network"]["max_total_remote_get_count"])
        ),
    }


def validate_offline_carrier(config_path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = load_config(config_path)
    return {
        "schema": "TASK217D_OFFLINE_CARRIER_VALIDATION_V1",
        "status": "PASS",
        "new_document_count": cfg["canonical_discovery"]["new_document_count"],
        "partition_count": len(cfg["partitions"]),
        "partition_document_count": sum(len(v) for v in cfg["partitions"].values()),
        "live_authorized": cfg["authorization"]["live_authorized"],
        "document_downloads_authorized_by_default": cfg["authorization"]["document_downloads_authorized_by_default"],
        "network": False,
        "drive_write": False,
        "promotion": False,
    }
