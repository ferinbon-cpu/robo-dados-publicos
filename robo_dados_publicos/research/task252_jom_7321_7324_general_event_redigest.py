"""TASK252: canonize TASK251 and prepare exact hash-pinned JOM 7321-7324 general redigest."""
from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pypdf import PdfReader

from robo_dados_publicos.research.task219a_jom_general_event_redigest import (
    process_document_general,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task252_jom_7321_7324_general_event_redigest.v1.json"
DEFAULT_EVIDENCE = ROOT / "docs/evidence/TASK_252_TASK251_RECOVERY_CANONICAL_0.8.0.json"

EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
EXPECTED_SOURCE = "LIMEIRA_JORNAL_OFICIAL"
EXPECTED_EDITIONS = [7321, 7322, 7323, 7324]
ALLOWED_HOST = "ecrie.com.br"
PASS_STATUS = "PASS_COMPLETE_4_DOCUMENT_GENERAL_EVENT_REDIGEST"


class Task252Stop(RuntimeError):
    pass


class DocumentSource(Protocol):
    network_capable: bool

    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict[str, Any]]: ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


class LivePinnedPdfSource:
    network_capable = True

    def __init__(self, *, timeout: int = 180, user_agent: str = "ROBO_DADOS_PUBLICOS/0.8.0 TASK252"):
        self.timeout = timeout
        self.user_agent = user_agent

    def get(self, url: str, maximum_bytes: int) -> tuple[bytes, dict[str, Any]]:
        request = Request(url, headers={"User-Agent": self.user_agent}, method="GET")
        opener = build_opener(_NoRedirect())
        digest = hashlib.sha256()
        chunks: list[bytes] = []
        total = 0
        try:
            with opener.open(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200) or 200)
                final_url = str(response.geturl())
                content_type = str(response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                while True:
                    remaining = maximum_bytes - total
                    if remaining < 0:
                        raise Task252Stop("SOURCE_STREAM_BYTE_CAP_EXCEEDED")
                    block = response.read(min(1024 * 1024, remaining + 1))
                    if not block:
                        break
                    if len(block) > remaining:
                        raise Task252Stop("SOURCE_STREAM_BYTE_CAP_EXCEEDED")
                    digest.update(block)
                    chunks.append(block)
                    total += len(block)
        except HTTPError as exc:
            raise Task252Stop(f"SOURCE_HTTP_{exc.code}") from exc
        parsed = urlparse(final_url)
        return b"".join(chunks), {
            "http_status": status,
            "requested_url": url,
            "final_url": final_url,
            "https": parsed.scheme == "https",
            "final_host": (parsed.hostname or "").lower(),
            "content_type": content_type,
            "bytes": total,
            "sha256": digest.hexdigest(),
            "remote_get_count": 1,
        }


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task252Stop(code)


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return _read_json(path)


def load_canonical_evidence(path: str | Path = DEFAULT_EVIDENCE) -> dict[str, Any]:
    return _read_json(path)


def validate_canonical_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    _stop(evidence.get("task") == "TASK_252", "EVIDENCE_TASK")
    _stop(evidence.get("schema") == "TASK252_TASK251_RECOVERY_CANONICAL_V1", "EVIDENCE_SCHEMA")
    _stop(
        evidence.get("status") == "PASS_TASK251_RECOVERY_CANONIZED_AND_4_OF_4_BINARY_SCOPE_COMPLETE",
        "EVIDENCE_STATUS",
    )
    _stop(
        evidence.get("task251_implementation_sha") == "ce0ef6348546c3ac1d48f69a6100e9907df98e8b",
        "EVIDENCE_IMPLEMENTATION_SHA",
    )
    _stop(
        evidence.get("task251_runtime_head_sha") == "bff49e947de78b63a716e7d9589e52b65b9d69ad",
        "EVIDENCE_RUNTIME_SHA",
    )
    _stop(
        evidence.get("run")
        == {
            "id": 35248412098,
            "attempt": 1,
            "conclusion": "success",
            "job_id": 105294374835,
            "job_conclusion": "success",
        },
        "EVIDENCE_RUN",
    )
    artifact = evidence.get("artifact") or {}
    _stop(artifact.get("id") == 10508475804, "EVIDENCE_ARTIFACT_ID")
    _stop(
        artifact.get("name") == "task-251-jom-7323-7324-oversized-recovery-sanitized",
        "EVIDENCE_ARTIFACT_NAME",
    )
    _stop(
        artifact.get("zip_sha256") == "20c3c7261c88ba2896060fbfe8f5c2e99099c575891c4fc332e719fbf2cdafd7",
        "EVIDENCE_ARTIFACT_ZIP_SHA",
    )
    _stop(
        artifact.get("json_sha256") == "fb750704960cdb251c210f901fca3ba174831c493b155744a1a0f4e90d6dc244",
        "EVIDENCE_ARTIFACT_JSON_SHA",
    )

    result = dict(evidence.get("task251_sanitized_result") or {})
    embedded_hash = result.pop("result_sha256", None)
    _stop(
        embedded_hash == "4656c5230475385cf0bae9e960d2362c2978b16bf5ce7e2ae6d5f1e2d864a295",
        "EVIDENCE_RESULT_HASH_IDENTITY",
    )
    _stop(_canonical_hash(result) == embedded_hash, "EVIDENCE_RESULT_HASH_RECOMPUTE")
    _stop(result.get("status") == "PASS_TASK251_BOUNDED_OVERSIZED_RECOVERY", "EVIDENCE_TASK251_STATUS")
    _stop(result.get("source_gets") == 2, "EVIDENCE_SOURCE_GETS")
    _stop(result.get("document_download_count") == 2, "EVIDENCE_DOWNLOAD_COUNT")
    _stop(result.get("aggregate_pdf_bytes") == 142538817, "EVIDENCE_TASK251_AGGREGATE")
    _stop(result.get("drive_write_count") == 0, "EVIDENCE_DRIVE_WRITE")
    _stop(result.get("raw_pdf_persisted") is False, "EVIDENCE_RAW_PDF")
    _stop(result.get("retry_performed") is False, "EVIDENCE_RETRY")
    _stop(result.get("redirect_followed") is False, "EVIDENCE_REDIRECT")
    _stop(result.get("alternate_url_discovery_performed") is False, "EVIDENCE_ALTERNATE_DISCOVERY")

    scope = evidence.get("binary_scope") or {}
    _stop(scope.get("status") == "COMPLETE_4_OF_4_BINARY_IDENTITIES_PROVEN", "EVIDENCE_SCOPE_STATUS")
    _stop(scope.get("editions") == EXPECTED_EDITIONS, "EVIDENCE_SCOPE_EDITIONS")
    _stop(scope.get("aggregate_expected_bytes") == 230331629, "EVIDENCE_SCOPE_BYTES")
    _stop(scope.get("absence_inference_allowed") is False, "EVIDENCE_ABSENCE_GUARD")
    _stop(scope.get("semantic_content_proven") is False, "EVIDENCE_SEMANTIC_GUARD")
    documents = scope.get("documents") or []
    _stop([row.get("edition") for row in documents] == EXPECTED_EDITIONS, "EVIDENCE_DOCUMENT_ORDER")
    expected = {
        7321: (4307520, 11, "099732bf08ed922c5547daba32c18eaba87b6e3384709a46872604ce9926dc89", "TASK249_RUN_35174078683"),
        7322: (83485292, 109, "30ce94f2de2c8b1fe37b7f0bafbafc3ac7ab5f3d243752f965b63ad53e0b4993", "TASK249_RUN_35174078683"),
        7323: (126648737, 438, "058fd702325f6447db75b6b60066448789d35261d3152dfaab3962081c2ad940", "TASK251_RUN_35248412098"),
        7324: (15890080, 64, "66fbb723128311d919509802d270a112d7f9f44bd5447e315db9f8933ccb194b", "TASK251_RUN_35248412098"),
    }
    for row in documents:
        edition = int(row["edition"])
        exp = expected[edition]
        _stop((row.get("bytes"), row.get("pages"), row.get("sha256"), row.get("evidence_source")) == exp, f"EVIDENCE_DOCUMENT_{edition}")
        _stop(row.get("source_id") == f"LIMEIRA_JO_{edition:05d}", f"EVIDENCE_SOURCE_ID_{edition}")
        parsed = urlparse(str(row.get("document_url") or ""))
        _stop(parsed.scheme == "https" and (parsed.hostname or "").lower() == ALLOWED_HOST, f"EVIDENCE_URL_{edition}")
    _stop(sum(int(row["bytes"]) for row in documents) == 230331629, "EVIDENCE_AGGREGATE_RECOMPUTE")

    guards = evidence.get("guards") or {}
    _stop(guards.get("source_gets_in_task252_implementation") == 0, "EVIDENCE_TASK252_OFFLINE")
    _stop(guards.get("task251_canonization_ne_semantic_content_proof") is True, "EVIDENCE_CONTENT_GUARD")
    _stop(guards.get("schedule_authorized") is False, "EVIDENCE_SCHEDULE_GUARD")
    _stop(guards.get("recurrence_authorized") is False, "EVIDENCE_RECURRENCE_GUARD")
    return {"status": "PASS_TASK252_CANONICAL_EVIDENCE", "task251_result_sha256": embedded_hash}


def validate_config(config: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    validate_canonical_evidence(evidence)
    _stop(config.get("task") == "TASK_252", "CONFIG_TASK")
    _stop(config.get("schema") == "TASK252_JOM_7321_7324_GENERAL_EVENT_REDIGEST_V1", "CONFIG_SCHEMA")
    _stop(config.get("issue") == 837, "CONFIG_ISSUE")
    _stop(config.get("base_main_sha") == "ce0ef6348546c3ac1d48f69a6100e9907df98e8b", "CONFIG_BASE")
    _stop(
        config.get("mode") == "T1_READONLY_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION",
        "CONFIG_MODE",
    )
    canonical = config.get("canonical_recovery") or {}
    _stop(
        canonical.get("evidence") == "docs/evidence/TASK_252_TASK251_RECOVERY_CANONICAL_0.8.0.json",
        "CONFIG_EVIDENCE_PATH",
    )
    _stop(
        canonical.get("task251_result_sha256") == "4656c5230475385cf0bae9e960d2362c2978b16bf5ce7e2ae6d5f1e2d864a295",
        "CONFIG_EVIDENCE_HASH",
    )
    _stop(canonical.get("expected_aggregate_bytes") == 230331629, "CONFIG_EXPECTED_AGGREGATE")

    targets = config.get("targets") or []
    _stop([row.get("edition") for row in targets] == EXPECTED_EDITIONS, "CONFIG_TARGET_EDITIONS")
    evidence_docs = (evidence.get("binary_scope") or {}).get("documents") or []
    _stop(targets == evidence_docs, "CONFIG_TARGETS_NE_CANONICAL_SCOPE")
    _stop(len({row.get("document_url") for row in targets}) == 4, "CONFIG_TARGET_URL_DUPLICATE")

    network = config.get("network") or {}
    expected_network = {
        "allowed_document_host": ALLOWED_HOST,
        "max_index_remote_get_count": 0,
        "max_document_get_attempt_count": 4,
        "max_total_remote_get_count": 4,
        "max_bytes_per_document": 262144000,
        "max_aggregate_document_bytes": 230331629,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
    }
    _stop(all(network.get(k) == v for k, v in expected_network.items()), "CONFIG_NETWORK")

    processing = config.get("processing") or {}
    _stop(processing.get("processor") == "JournalPdfProcessor", "CONFIG_PROCESSOR")
    _stop(processing.get("general_event_precedent") == "TASK219A", "CONFIG_PRECEDENT")
    for key in (
        "stage_bronze",
        "plan_reconciliation",
        "emit_semantic_facets_in_processor",
        "persist_accounting_query_tasks",
        "raw_pdf_persisted",
        "raw_page_text_persisted",
        "rag_chunks_persisted",
        "continue_after_document_failure",
    ):
        _stop(processing.get(key) is False, f"CONFIG_FALSE_{key}")
    for key in (
        "derive_semantic_classification_after_event_parse",
        "persist_events_gold_sanitized",
        "persist_event_semantics_sanitized",
        "persist_strong_identity_anchors",
        "persist_document_summaries",
        "partial_redigest_ne_absence",
    ):
        _stop(processing.get(key) is True, f"CONFIG_TRUE_{key}")

    strong = config.get("strong_identity") or {}
    _stop(strong.get("precedent_config") == "config/task219a_jom_general_event_redigest.v1.json", "CONFIG_STRONG_PRECEDENT")
    _stop(strong.get("strong_anchor_ne_end_to_end_identity") is True, "CONFIG_ANCHOR_GUARD")
    _stop(strong.get("pncp_tce_join_authorized") is False, "CONFIG_JOIN_GUARD")

    auth = config.get("authorization") or {}
    _stop(auth.get("required_task") == "TASK_252_LIVE_AUTHORIZATION", "CONFIG_AUTH_TASK")
    _stop(auth.get("required_operation") == "EXACT_4_HASH_PINNED_JOM_7321_7324_GENERAL_EVENT_REDIGEST", "CONFIG_AUTH_OPERATION")
    _stop(auth.get("attempt_count") == 1, "CONFIG_AUTH_ATTEMPT")
    for key, value in auth.items():
        if key.endswith("_authorized"):
            _stop(value is False, f"CONFIG_AUTH_DEFAULT_{key}")
    _stop(all(v is False for v in (config.get("pre_authorization_remote_effects") or {}).values()), "CONFIG_REMOTE_EFFECT")
    return {"status": "PASS_TASK252_CONFIG", "targets": 4}


def _base_stop(code: str, *, source_gets: int = 0, documents: list[dict[str, Any]] | None = None, **extra: Any) -> dict[str, Any]:
    return {
        "schema": "TASK252_GENERAL_EVENT_REDIGEST_RESULT_V1",
        "status": code,
        "complete_scope": False,
        "source_gets": source_gets,
        "documents": documents or [],
        "events": [],
        "semantics": [],
        "strong_anchors": [],
        "raw_pdf_persisted": False,
        "raw_page_text_persisted": False,
        "rag_chunks_persisted": False,
        "accounting_query_tasks_persisted": False,
        "drive_write_count": 0,
        "bronze_created": 0,
        "silver_created": 0,
        "gold_created": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "retry_performed": False,
        "redirect_followed": False,
        "alternate_url_discovery_performed": False,
        "absence_inference_allowed": False,
        **extra,
    }


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if not authorization:
        return _base_stop("STOP_TASK252_LIVE_NOT_AUTHORIZED")
    if authorization.get("synthetic_test_only") is True:
        return _base_stop("STOP_TASK252_SYNTHETIC_AUTH_NOT_LIVE")
    if any(authorization.get(k) is True for k in ("task249_authorization_reused", "task250_authorization_reused", "task251_authorization_reused")):
        return _base_stop("STOP_TASK252_PRIOR_AUTHORIZATION_REUSE")
    if re.fullmatch(r"[0-9a-f]{40}", expected_implementation_sha or "") is None:
        return _base_stop("STOP_TASK252_IMPLEMENTATION_SHA_FORMAT")
    required = {
        "task": "TASK_252_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "implementation_branch": "main",
        "runtime_branch": config["runtime"]["branch"],
        "implementation_sha": expected_implementation_sha,
        "source": EXPECTED_SOURCE,
        "operation": "EXACT_4_HASH_PINNED_JOM_7321_7324_GENERAL_EVENT_REDIGEST",
        "editions": EXPECTED_EDITIONS,
        "expected_aggregate_bytes": 230331629,
        "max_index_remote_get_count": 0,
        "max_document_get_attempt_count": 4,
        "max_total_remote_get_count": 4,
        "max_bytes_per_document": 262144000,
        "max_aggregate_document_bytes": 230331629,
        "attempt_count": 1,
        "owner_authorized": True,
        "document_downloads_authorized": True,
        "rediscovery_authorized": False,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
        "task249_authorization_reused": False,
        "task250_authorization_reused": False,
        "task251_authorization_reused": False,
        "drive_write_authorized": False,
        "bronze_authorized": False,
        "silver_authorized": False,
        "gold_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
        "consumed": False,
    }
    if any(authorization.get(k) != v for k, v in required.items()):
        return _base_stop("STOP_TASK252_AUTHORIZATION_CONTRACT_MISMATCH")
    return {"status": "PASS_TASK252_LIVE_AUTHORIZATION"}


def _validate_download(item: Mapping[str, Any], data: bytes, meta: Mapping[str, Any], *, maximum_bytes: int) -> dict[str, Any]:
    edition = int(item["edition"])
    _stop(meta.get("http_status") == 200, f"DOWNLOAD_HTTP_{edition}")
    _stop(meta.get("requested_url") == item["document_url"], f"DOWNLOAD_REQUEST_URL_{edition}")
    _stop(meta.get("final_url") == item["document_url"], f"DOWNLOAD_REDIRECT_OR_URL_DRIFT_{edition}")
    _stop(meta.get("https") is True, f"DOWNLOAD_HTTPS_{edition}")
    _stop(meta.get("final_host") == ALLOWED_HOST, f"DOWNLOAD_HOST_{edition}")
    _stop(meta.get("content_type") == "application/pdf", f"DOWNLOAD_CONTENT_TYPE_{edition}")
    _stop(meta.get("remote_get_count") == 1, f"DOWNLOAD_GET_COUNT_{edition}")
    _stop(0 < len(data) <= maximum_bytes, f"DOWNLOAD_BYTE_CAP_{edition}")
    _stop(len(data) == int(item["bytes"]), f"DOWNLOAD_EXPECTED_BYTES_{edition}")
    digest = hashlib.sha256(data).hexdigest()
    _stop(digest == item["sha256"], f"DOWNLOAD_EXPECTED_SHA256_{edition}")
    _stop(meta.get("sha256") in (None, digest), f"DOWNLOAD_TRANSPORT_SHA256_{edition}")
    _stop(data.startswith(b"%PDF-"), f"DOWNLOAD_PDF_SIGNATURE_{edition}")
    reader = PdfReader(io.BytesIO(data))
    pages = len(reader.pages)
    _stop(pages > 0, f"DOWNLOAD_PAGE_COUNT_POSITIVE_{edition}")
    _stop(pages == int(item["pages"]), f"DOWNLOAD_EXPECTED_PAGES_{edition}")
    return {
        "edition": edition,
        "bytes": len(data),
        "pages": pages,
        "sha256": digest,
        "content_type": meta.get("content_type"),
        "document_url": item["document_url"],
        "source_id": item["source_id"],
        "logical_key": item["logical_key"],
        "publication_date": item["publication_date"],
    }


def _default_document_processor(item: Mapping[str, Any], data: bytes) -> dict[str, Any]:
    return process_document_general(item, data)


def execute_general_redigest(
    config: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    document_source: DocumentSource,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
    document_processor: Callable[[Mapping[str, Any], bytes], dict[str, Any]] | None = None,
    download_validator: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    try:
        validate_config(config, evidence)
    except Exception as exc:
        return _base_stop("STOP_TASK252_CONFIG_OR_EVIDENCE", stop_code=str(exc), error_class=type(exc).__name__)

    if offline_test_mode:
        if getattr(document_source, "network_capable", True):
            return _base_stop("STOP_TASK252_OFFLINE_SOURCE_NETWORK_CAPABLE")
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return _base_stop("STOP_TASK252_OFFLINE_TEST_AUTHORIZATION")
    else:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
            config=config,
        )
        if auth["status"] != "PASS_TASK252_LIVE_AUTHORIZATION":
            return auth
        if not getattr(document_source, "network_capable", False):
            return _base_stop("STOP_TASK252_LIVE_SOURCE_NOT_NETWORK_CAPABLE")

    processor = document_processor or _default_document_processor
    validator = download_validator or _validate_download
    document_results: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    all_semantics: list[dict[str, Any]] = []
    all_anchors: list[dict[str, Any]] = []
    aggregate_bytes = 0
    source_gets = 0

    for item in config["targets"]:
        try:
            _stop(source_gets < 4, "SOURCE_GET_BUDGET_EXCEEDED")
            data, meta = document_source.get(item["document_url"], int(config["network"]["max_bytes_per_document"]))
            source_gets += 1
            validated = validator(
                item,
                data,
                meta,
                maximum_bytes=int(config["network"]["max_bytes_per_document"]),
            )
            aggregate_bytes += int(validated["bytes"])
            _stop(
                aggregate_bytes <= int(config["network"]["max_aggregate_document_bytes"]),
                "AGGREGATE_BYTE_CAP_EXCEEDED",
            )
            processed = processor(item, data)
            summary = dict(processed.get("summary") or {})
            if summary.get("source_sha256") is not None:
                _stop(summary.get("source_sha256") == item["sha256"], f"PROCESSOR_SOURCE_SHA_DRIFT_{item['edition']}")
            _stop(processed.get("status") == "PASS_DOCUMENT", f"PROCESSOR_STATUS_{item['edition']}")
            events = [dict(row) for row in (processed.get("events") or [])]
            semantics = [dict(row) for row in (processed.get("semantics") or [])]
            anchors = [dict(row) for row in (processed.get("strong_anchors") or [])]
            document_results.append(
                {
                    **validated,
                    "processing_status": summary.get("processing_status", "PASS_DOCUMENT_PROCESSING"),
                    "text_extraction": summary.get("text_extraction"),
                    "silver_pages": summary.get("silver_pages"),
                    "gold_events": summary.get("gold_events"),
                    "event_count": len(events),
                    "semantic_count": len(semantics),
                    "strong_anchor_count": len(anchors),
                }
            )
            all_events.extend(events)
            all_semantics.extend(semantics)
            all_anchors.extend(anchors)
        except Exception as exc:
            return _base_stop(
                "STOP_TASK252_DOCUMENT_FAILURE",
                source_gets=source_gets,
                documents=document_results,
                failed_edition=int(item["edition"]),
                error_class=type(exc).__name__,
                stop_code=str(exc),
                aggregate_document_bytes=aggregate_bytes,
            )

    _stop(source_gets == 4, "FINAL_SOURCE_GET_COUNT")
    _stop(aggregate_bytes == 230331629, "FINAL_AGGREGATE_BYTES")
    _stop([row["edition"] for row in document_results] == EXPECTED_EDITIONS, "FINAL_DOCUMENT_SCOPE")

    all_events.sort(key=lambda row: (int(row.get("edition") or 0), int(row.get("page_number") or 0), str(row.get("event_id") or "")))
    all_semantics.sort(key=lambda row: str(row.get("semantic_id") or ""))
    all_anchors.sort(key=lambda row: (str(row.get("event_id") or ""), str(row.get("anchor_type") or ""), str(row.get("anchor_value") or "")))

    return {
        "schema": "TASK252_GENERAL_EVENT_REDIGEST_RESULT_V1",
        "status": PASS_STATUS,
        "complete_scope": True,
        "canonical_binary_scope": EXPECTED_EDITIONS,
        "source_gets": source_gets,
        "document_download_count": source_gets,
        "aggregate_document_bytes": aggregate_bytes,
        "documents": document_results,
        "counts": {
            "event_count": len(all_events),
            "semantic_count": len(all_semantics),
            "strong_anchor_count": len(all_anchors),
            "strong_anchor_event_count": len({row.get("event_id") for row in all_anchors}),
        },
        "events": all_events,
        "semantics": all_semantics,
        "strong_anchors": all_anchors,
        "raw_pdf_persisted": False,
        "raw_page_text_persisted": False,
        "rag_chunks_persisted": False,
        "accounting_query_tasks_persisted": False,
        "drive_write_count": 0,
        "bronze_created": 0,
        "silver_created": 0,
        "gold_created": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "promotion_performed": False,
        "retry_performed": False,
        "redirect_followed": False,
        "alternate_url_discovery_performed": False,
        "absence_inference_allowed": False,
        "strong_anchor_ne_end_to_end_identity": True,
        "canonization_required": True,
        "next_gate": "CANONIZE_TASK252_REDIGEST_BEFORE_ANY_JOIN_SERVING_OR_PUBLICATION",
    }
