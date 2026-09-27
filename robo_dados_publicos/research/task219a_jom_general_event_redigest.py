from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

from robo_dados_publicos.journal.processing import JournalPdfProcessor
from robo_dados_publicos.journal.semantic_layers import classify_event
from robo_dados_publicos.research.task216_pncp_strong_identity_bridge import (
    load_config as load_task216_config,
    normalize_admin_identifier,
)
from robo_dados_publicos.research.task217d_jom_school_infra_redigest import (
    LiveDocumentSource,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task219a_jom_general_event_redigest.v1.json"


class Task219AStop(RuntimeError):
    pass


class DocumentSource(Protocol):
    network_capable: bool

    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict[str, Any]]: ...


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219AStop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK219A_JOM_GENERAL_EVENT_REDIGEST_V1", "TASK219A_SCHEMA")
    _stop(obj.get("issue") == 691, "TASK219A_ISSUE")
    _stop(
        obj.get("base_main_sha") == "8eee468c934362db5e8633ecee56d60c896a1d41",
        "TASK219A_BASE",
    )
    _stop(
        obj.get("mode")
        == "T0_IMPLEMENTED_LIVE_DISABLED_UNTIL_SEPARATE_OWNER_AUTHORIZATION",
        "TASK219A_MODE",
    )

    discovery = obj["canonical_discovery"]
    _stop(discovery["result_sha256"] == "7c31c9791793c889a8c76e27bcf0d6b6b26f23a3b6bec07fbd95d8c1fba29510", "TASK219A_DISCOVERY_SHA")
    _stop(discovery["document_count"] == 99, "TASK219A_DISCOVERY_COUNT")
    _stop(discovery["existing_event_rows"] == 303, "TASK219A_EXISTING_ROWS")
    _stop(len(discovery["existing_editions"]) == 12, "TASK219A_EXISTING_EDITIONS")
    _stop(discovery["new_document_count"] == 87, "TASK219A_NEW_DOCUMENTS")
    _stop(
        discovery["pinned_target_fixture"]
        == "docs/evidence/fixtures/task219/TASK_219A_CANONICAL_87_DOCUMENT_TARGETS.csv",
        "TASK219A_TARGET_FIXTURE",
    )
    _stop(
        discovery["pinned_target_fixture_git_blob_sha"]
        == "766069f41ae785010d91de888bc71b3dd504a1a9",
        "TASK219A_TARGET_FIXTURE_BLOB",
    )
    _stop(discovery["rediscovery_required"] is False, "TASK219A_REDISCOVERY_GUARD")

    prior = obj["prior_recovery_budget_evidence"]
    observed_sum = (
        int(prior["task217d_aggregate_document_bytes"])
        + int(prior["task217f_aggregate_document_bytes"])
        + int(prior["task217g_aggregate_document_bytes"])
    )
    _stop(
        observed_sum == int(prior["overlap_inclusive_upper_bound_bytes"]),
        "TASK219A_PRIOR_BYTE_SUM",
    )
    _stop(prior["upper_bound_below_new_cap"] is True, "TASK219A_PRIOR_CAP_FLAG")
    _stop(
        observed_sum < int(prior["new_aggregate_cap_bytes"]),
        "TASK219A_PRIOR_CAP_MATH",
    )

    network = obj["network"]
    _stop(network["allowed_document_host"] == "ecrie.com.br", "TASK219A_HOST")
    _stop(network["max_index_remote_get_count"] == 0, "TASK219A_INDEX_GETS")
    _stop(network["max_document_get_attempt_count"] == 87, "TASK219A_DOCUMENT_GETS")
    _stop(network["max_total_remote_get_count"] == 87, "TASK219A_TOTAL_GETS")
    _stop(
        network["max_index_remote_get_count"]
        + network["max_document_get_attempt_count"]
        == network["max_total_remote_get_count"],
        "TASK219A_GET_BUDGET_MATH",
    )
    _stop(network["max_bytes_per_document"] == 262144000, "TASK219A_DOCUMENT_BYTES")
    _stop(network["max_aggregate_document_bytes"] == 4294967296, "TASK219A_AGGREGATE_BYTES")
    _stop(network["automatic_retry"] is False, "TASK219A_RETRY")

    processing = obj["processing"]
    _stop(processing["stage_bronze"] is False, "TASK219A_BRONZE")
    _stop(processing["plan_reconciliation"] is False, "TASK219A_RECONCILIATION")
    _stop(processing["emit_semantic_facets"] is False, "TASK219A_PROCESSOR_SEMANTICS")
    _stop(processing["derive_semantic_classification_after_event_parse"] is True, "TASK219A_DERIVED_SEMANTICS")
    _stop(processing["persist_events_gold_sanitized"] is True, "TASK219A_EVENTS")
    _stop(processing["persist_event_semantics_sanitized"] is True, "TASK219A_SEMANTICS")
    _stop(processing["persist_strong_identity_anchors"] is True, "TASK219A_ANCHORS")
    _stop(processing["persist_accounting_query_tasks"] is False, "TASK219A_ACCOUNTING_TASKS")
    _stop(processing["raw_pdf_persisted"] is False, "TASK219A_RAW_PDF")
    _stop(processing["raw_page_text_persisted"] is False, "TASK219A_RAW_PAGE")
    _stop(processing["rag_chunks_persisted"] is False, "TASK219A_RAG")

    strong = obj["strong_identity"]
    task216 = load_task216_config(ROOT / strong["task216_config"])
    rules = task216["jom_anchor_rules"]
    _stop(set(strong["allowed_event_types"]) == set(rules["event_types"]), "TASK219A_ANCHOR_TYPES")
    _stop(strong["complete_process_regex"] == rules["complete_process_regex"], "TASK219A_PROCESS_REGEX")
    _stop(strong["complete_contract_regex"] == rules["complete_contract_regex"], "TASK219A_CONTRACT_REGEX")
    for key in (
        "cnpj_alone_may_anchor",
        "amount_may_anchor",
        "date_may_anchor",
        "object_text_may_anchor",
        "semantic_similarity_may_anchor",
    ):
        _stop(strong[key] is False, f"TASK219A_FORBIDDEN_IDENTITY:{key}")

    auth = obj["authorization"]
    _stop(auth["live_authorized"] is False, "TASK219A_LIVE_DEFAULT")
    _stop(auth["task217d_authorization_reuse_allowed"] is False, "TASK219A_217D_REUSE")
    _stop(auth["task217f_authorization_reuse_allowed"] is False, "TASK219A_217F_REUSE")
    _stop(auth["task217g_authorization_reuse_allowed"] is False, "TASK219A_217G_REUSE")
    _stop(obj["promotion"]["runtime_may_promote"] is False, "TASK219A_PROMOTION")
    _stop(all(v is False for v in obj["pre_authorization_remote_effects"].values()), "TASK219A_T0_EFFECT")
    return obj


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_pinned_targets(
    config_path: str | Path = DEFAULT_CONFIG,
) -> list[dict[str, Any]]:
    cfg = load_config(config_path)
    discovery = cfg["canonical_discovery"]
    path = ROOT / discovery["pinned_target_fixture"]
    data = path.read_bytes()
    _stop(
        _git_blob_sha1(data) == discovery["pinned_target_fixture_git_blob_sha"],
        "TASK219A_TARGET_FIXTURE_HASH",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _stop(
            reader.fieldnames
            == ["edition", "publication_date", "source_id", "document_url"],
            "TASK219A_TARGET_FIXTURE_COLUMNS",
        )
        rows = [dict(row) for row in reader]

    _stop(len(rows) == 87, "TASK219A_PINNED_TARGET_COUNT")
    editions: list[int] = []
    out: list[dict[str, Any]] = []
    for row in rows:
        edition = int(row["edition"])
        editions.append(edition)
        _stop(
            row["source_id"] == f"LIMEIRA_JO_{edition:05d}",
            "TASK219A_PINNED_SOURCE_ID",
        )
        _stop(
            re.fullmatch(r"2026-\d{2}-\d{2}", row["publication_date"] or "") is not None,
            "TASK219A_PINNED_PUBLICATION_DATE",
        )
        parsed = urlparse(row["document_url"])
        _stop(parsed.scheme == "https", "TASK219A_PINNED_URL_HTTPS")
        _stop(
            (parsed.hostname or "").lower() == cfg["network"]["allowed_document_host"],
            "TASK219A_PINNED_URL_HOST",
        )
        _stop(parsed.path.lower().endswith(".pdf"), "TASK219A_PINNED_URL_PDF")
        out.append(
            {
                "edition": edition,
                "publication_date": row["publication_date"],
                "source_id": row["source_id"],
                "document_url": row["document_url"],
            }
        )

    _stop(len(set(editions)) == 87, "TASK219A_PINNED_TARGET_DUPLICATE")
    _stop(
        not set(editions).intersection(discovery["existing_editions"]),
        "TASK219A_PINNED_EXISTING_OVERLAP",
    )
    task217d = _load(ROOT / discovery["task217d_config"])
    expected = {
        int(edition)
        for partition in task217d["partitions"].values()
        for edition in partition
    }
    _stop(set(editions) == expected, "TASK219A_PINNED_TARGET_IDENTITY_DRIFT")
    return out


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def extract_strong_anchors(
    event_rows: list[Mapping[str, Any]],
    *,
    config_path: str | Path = DEFAULT_CONFIG,
) -> list[dict[str, Any]]:
    cfg = load_config(config_path)
    strong = cfg["strong_identity"]
    allowed_types = set(strong["allowed_event_types"])
    anchors: list[dict[str, Any]] = []

    for raw in event_rows:
        event = dict(raw)
        if str(event.get("event_type") or "") not in allowed_types:
            continue
        process = normalize_admin_identifier(event.get("process_number"))
        contract = normalize_admin_identifier(event.get("contract_number"))
        supplier = re.sub(r"\D", "", str(event.get("cnpj") or ""))
        supplier = supplier if len(supplier) == 14 else None
        base = {
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "edition": event.get("edition"),
            "publication_date": event.get("publication_date"),
            "page_number": event.get("page_number"),
            "source_sha256": event.get("source_sha256"),
            "supplier_cnpj": supplier,
        }
        if process and re.fullmatch(strong["complete_process_regex"], process):
            anchors.append(
                {
                    **base,
                    "anchor_type": "PROCESS_IDENTITY",
                    "anchor_value": process,
                }
            )
        if contract and re.fullmatch(strong["complete_contract_regex"], contract):
            anchors.append(
                {
                    **base,
                    "anchor_type": "CONTRACT_IDENTITY",
                    "anchor_value": contract,
                }
            )

    anchors.sort(
        key=lambda row: (
            str(row.get("event_id") or ""),
            str(row.get("anchor_type") or ""),
            str(row.get("anchor_value") or ""),
        )
    )
    return anchors


def process_document_general(
    item: Mapping[str, Any],
    data: bytes,
    *,
    processor: JournalPdfProcessor | None = None,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
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
                "events": [],
                "semantics": [],
                "strong_anchors": [],
            }

        events = _read_jsonl(out / "events_gold.jsonl")
        semantics = [classify_event(row) for row in events]
        anchors = extract_strong_anchors(events, config_path=config_path)
        _stop(
            not (out / "event_semantics_gold.jsonl").exists(),
            "TASK219A_PROCESSOR_SEMANTICS_UNEXPECTED",
        )
        _stop(
            not (out / "accounting_query_tasks.jsonl").exists(),
            "TASK219A_ACCOUNTING_TASKS_UNEXPECTED",
        )
        return {
            "status": "PASS_DOCUMENT",
            "summary": summary,
            "events": events,
            "semantics": semantics,
            "strong_anchors": anchors,
        }


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    if not authorization:
        return {"status": "STOP_LIVE_NOT_AUTHORIZED"}
    if authorization.get("task217d_authorization_reused") is True:
        return {"status": "STOP_TASK217D_AUTHORIZATION_REUSE"}
    if authorization.get("task217f_authorization_reused") is True:
        return {"status": "STOP_TASK217F_AUTHORIZATION_REUSE"}
    if authorization.get("task217g_authorization_reused") is True:
        return {"status": "STOP_TASK217G_AUTHORIZATION_REUSE"}
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
        "max_document_get_attempt_count": cfg["network"]["max_document_get_attempt_count"],
        "pinned_target_fixture_git_blob_sha": cfg["canonical_discovery"]["pinned_target_fixture_git_blob_sha"],
        "max_total_remote_get_count": cfg["network"]["max_total_remote_get_count"],
        "max_bytes_per_document": cfg["network"]["max_bytes_per_document"],
        "max_aggregate_document_bytes": cfg["network"]["max_aggregate_document_bytes"],
        "attempt_count": 1,
        "owner_authorized": True,
        "task217d_authorization_reused": False,
        "task217f_authorization_reused": False,
        "task217g_authorization_reused": False,
        "document_downloads_authorized": True,
        "rediscovery_authorized": False,
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
    _stop(meta.get("https") is True, "TASK219A_DOWNLOAD_HTTPS")
    _stop(
        meta.get("final_host") == cfg["network"]["allowed_document_host"],
        "TASK219A_DOWNLOAD_HOST",
    )
    _stop(
        meta.get("content_type") == "application/pdf",
        "TASK219A_DOWNLOAD_CONTENT_TYPE",
    )
    _stop(
        int(meta.get("remote_get_count") or 0) == 1,
        "TASK219A_DOWNLOAD_GET_COUNT",
    )
    _stop(
        len(data) <= int(cfg["network"]["max_bytes_per_document"]),
        "TASK219A_DOCUMENT_BYTES",
    )
    parsed = urlparse(str(item.get("document_url") or ""))
    _stop(parsed.scheme == "https", "TASK219A_DECLARED_URL_HTTPS")
    _stop(
        (parsed.hostname or "").lower() == cfg["network"]["allowed_document_host"],
        "TASK219A_DECLARED_URL_HOST",
    )


def execute_general_redigest(
    config: Mapping[str, Any],
    *,
    document_source: DocumentSource,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
    processor: JournalPdfProcessor | None = None,
) -> dict[str, Any]:
    cfg = dict(config)
    if offline_test_mode:
        if getattr(document_source, "network_capable", True):
            return {"status": "STOP_OFFLINE_TEST_DOCUMENT_NETWORK_CAPABLE", "complete_scope": False}
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return {"status": "STOP_OFFLINE_TEST_AUTHORIZATION", "complete_scope": False}
    else:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
        )
        if auth["status"] != "PASS_LIVE_AUTHORIZATION":
            return {**auth, "complete_scope": False}
        if not getattr(document_source, "network_capable", False):
            return {"status": "STOP_LIVE_DOCUMENT_SOURCE_NOT_NETWORK_CAPABLE", "complete_scope": False}

    try:
        documents = load_pinned_targets()
        _stop(len(documents) == 87, "TASK219A_SELECTED_DOCUMENT_COUNT")
    except Exception as exc:
        return {
            "schema": "TASK219A_GENERAL_EVENT_REDIGEST_RESULT_V1",
            "status": "STOP_PINNED_TARGET_VALIDATION",
            "complete_scope": False,
            "error_class": type(exc).__name__,
            "stop_code": str(exc),
            "document_get_attempt_count": 0,
            "validated_download_count": 0,
            "absence_inference_allowed": False,
            "promotion_performed": False,
        }

    aggregate_bytes = 0
    attempt_count = 0
    validated_download_count = 0
    document_results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    all_semantics: list[dict[str, Any]] = []
    all_anchors: list[dict[str, Any]] = []

    for item in documents:
        edition = int(item["edition"])
        attempt_count += 1
        try:
            _stop(
                attempt_count <= int(cfg["network"]["max_document_get_attempt_count"]),
                "TASK219A_DOCUMENT_GET_BUDGET",
            )
            data, meta = document_source.get(
                str(item["document_url"]),
                int(cfg["network"]["max_bytes_per_document"]),
            )
            _validate_download(item, data, meta, cfg=cfg)
            validated_download_count += 1
            aggregate_bytes += len(data)
            _stop(
                aggregate_bytes <= int(cfg["network"]["max_aggregate_document_bytes"]),
                "TASK219A_AGGREGATE_BYTES",
            )
            processed = process_document_general(
                item,
                data,
                processor=processor,
            )
            summary = {
                **processed["summary"],
                "event_count": len(processed["events"]),
                "semantic_count": len(processed["semantics"]),
                "strong_anchor_count": len(processed["strong_anchors"]),
            }
            document_results.append(summary)
            if processed["status"] != "PASS_DOCUMENT":
                failures.append(
                    {
                        "edition": edition,
                        "error_class": "PROCESSING_STATUS",
                        "stop_code": str(processed["summary"].get("processing_status")),
                    }
                )
                continue
            all_events.extend(processed["events"])
            all_semantics.extend(processed["semantics"])
            all_anchors.extend(processed["strong_anchors"])
        except Exception as exc:
            failures.append(
                {
                    "edition": edition,
                    "error_class": type(exc).__name__,
                    "stop_code": str(exc),
                }
            )
            document_results.append(
                {
                    "source_id": item.get("source_id"),
                    "edition": edition,
                    "publication_date": item.get("publication_date"),
                    "source_url": item.get("document_url"),
                    "processing_status": "STOP_EXCEPTION",
                    "error_class": type(exc).__name__,
                    "stop_code": str(exc),
                    "event_count": 0,
                    "semantic_count": 0,
                    "strong_anchor_count": 0,
                }
            )

    all_events.sort(
        key=lambda row: (
            int(row.get("edition") or 0),
            int(row.get("page_number") or 0),
            str(row.get("event_id") or ""),
        )
    )
    all_semantics.sort(key=lambda row: str(row.get("semantic_id") or ""))
    all_anchors.sort(
        key=lambda row: (
            str(row.get("event_id") or ""),
            str(row.get("anchor_type") or ""),
            str(row.get("anchor_value") or ""),
        )
    )
    document_results.sort(key=lambda row: int(row.get("edition") or 0))
    failures.sort(key=lambda row: int(row.get("edition") or 0))

    total_remote_gets = attempt_count
    _stop(
        total_remote_gets <= int(cfg["network"]["max_total_remote_get_count"]),
        "TASK219A_TOTAL_REMOTE_GET_BUDGET",
    )
    complete = (
        len(document_results) == 87
        and validated_download_count == 87
        and not failures
    )
    procurement_types = set(cfg["strong_identity"]["allowed_event_types"])
    procurement_shaped = [
        row for row in all_events if row.get("event_type") in procurement_types
    ]
    events_with_cnpj = [
        row
        for row in procurement_shaped
        if len(re.sub(r"\D", "", str(row.get("cnpj") or ""))) == 14
    ]

    return {
        "schema": "TASK219A_GENERAL_EVENT_REDIGEST_RESULT_V1",
        "status": (
            "PASS_COMPLETE_87_DOCUMENT_GENERAL_EVENT_REDIGEST"
            if complete
            else "PARTIAL_GENERAL_EVENT_REDIGEST_NO_ABSENCE_INFERENCE"
        ),
        "complete_scope": complete,
        "canonical_discovery_result_sha256": cfg["canonical_discovery"]["result_sha256"],
        "discovered_document_count": cfg["canonical_discovery"]["document_count"],
        "excluded_existing_document_count": 12,
        "target_document_count": 87,
        "pinned_target_fixture_git_blob_sha": cfg["canonical_discovery"]["pinned_target_fixture_git_blob_sha"],
        "index_remote_get_count": 0,
        "document_get_attempt_count": attempt_count,
        "validated_download_count": validated_download_count,
        "total_remote_get_count": total_remote_gets,
        "aggregate_document_bytes": aggregate_bytes,
        "document_results": document_results,
        "failures": failures,
        "counts": {
            "failure_count": len(failures),
            "new_event_count": len(all_events),
            "semantic_row_count": len(all_semantics),
            "procurement_shaped_event_count": len(procurement_shaped),
            "procurement_shaped_event_with_cnpj_count": len(events_with_cnpj),
            "strong_anchor_count": len(all_anchors),
            "strong_anchor_event_count": len({row.get("event_id") for row in all_anchors}),
            "process_anchor_count": sum(1 for row in all_anchors if row.get("anchor_type") == "PROCESS_IDENTITY"),
            "contract_anchor_count": sum(1 for row in all_anchors if row.get("anchor_type") == "CONTRACT_IDENTITY"),
        },
        "events": all_events,
        "semantics": all_semantics,
        "strong_anchors": all_anchors,
        "raw_pdf_persisted": False,
        "raw_page_text_persisted": False,
        "rag_chunks_persisted": False,
        "accounting_query_tasks_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "absence_inference_allowed": False,
        "strong_anchor_proves_end_to_end_identity_chain": False,
        "canonization_required": True,
    }


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    payload = b"".join(
        _canonical_bytes(dict(row)) + b"\n"
        for row in rows
    )
    path.write_bytes(payload)
    return {
        "file": path.name,
        "row_count": len(rows),
        "bytes": len(payload),
        "sha256": _sha256_bytes(payload),
    }


def write_sanitized_bundle(
    result: Mapping[str, Any],
    out_dir: str | Path,
) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    events_info = _write_jsonl(
        out / "task219a_events_gold_sanitized.jsonl",
        list(result.get("events") or []),
    )
    semantics_info = _write_jsonl(
        out / "task219a_event_semantics_sanitized.jsonl",
        list(result.get("semantics") or []),
    )
    anchors_info = _write_jsonl(
        out / "task219a_strong_identity_anchors.jsonl",
        list(result.get("strong_anchors") or []),
    )

    manifest = {
        key: value
        for key, value in dict(result).items()
        if key not in {"events", "semantics", "strong_anchors"}
    }
    manifest["files"] = {
        "events": events_info,
        "semantics": semantics_info,
        "strong_anchors": anchors_info,
    }
    manifest_material = {
        "status": manifest.get("status"),
        "complete_scope": manifest.get("complete_scope"),
        "counts": manifest.get("counts"),
        "files": manifest["files"],
        "failures": manifest.get("failures"),
    }
    manifest["bundle_sha256"] = _sha256_bytes(_canonical_bytes(manifest_material))
    manifest_bytes = json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    manifest_path = out / "task219a_manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    manifest["manifest_file_sha256"] = _sha256_bytes(manifest_bytes)
    return manifest


def validate_offline_carrier(
    config_path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    prior = cfg["prior_recovery_budget_evidence"]
    return {
        "schema": "TASK219A_OFFLINE_CARRIER_VALIDATION_V1",
        "status": "PASS",
        "target_document_count": cfg["canonical_discovery"]["new_document_count"],
        "max_total_remote_get_count": cfg["network"]["max_total_remote_get_count"],
        "max_bytes_per_document": cfg["network"]["max_bytes_per_document"],
        "aggregate_cap_bytes": cfg["network"]["max_aggregate_document_bytes"],
        "prior_overlap_inclusive_upper_bound_bytes": prior["overlap_inclusive_upper_bound_bytes"],
        "prior_upper_bound_below_cap": (
            prior["overlap_inclusive_upper_bound_bytes"]
            < cfg["network"]["max_aggregate_document_bytes"]
        ),
        "live_authorized": cfg["authorization"]["live_authorized"],
        "network": False,
        "drive_write": False,
        "promotion": False,
    }


__all__ = [
    "LiveDocumentSource",
    "Task219AStop",
    "execute_general_redigest",
    "extract_strong_anchors",
    "load_config",
    "load_pinned_targets",
    "process_document_general",
    "validate_live_authorization",
    "validate_offline_carrier",
    "write_sanitized_bundle",
]
