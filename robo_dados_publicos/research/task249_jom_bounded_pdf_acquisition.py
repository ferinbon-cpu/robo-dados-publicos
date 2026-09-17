"""Bounded read-only acquisition proof for JOM editions 7321-7324.

TASK249 is deliberately narrower than the older TASK032 custody flow:
it performs exact source GETs, validates the PDFs, emits sanitized metadata,
and persists no raw PDF or downstream product.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pypdf import PdfReader

EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
EXPECTED_BRANCH = "main"
EXPECTED_SOURCE = "LIMEIRA_JORNAL_OFICIAL"
ALLOWED_HOST = "ecrie.com.br"
EXPECTED_EDITIONS = [7321, 7322, 7323, 7324]
PASS_STATUS = "PASS_TASK249_BOUNDED_PDF_ACQUISITION"


class Task249Stop(RuntimeError):
    pass


class PdfSource(Protocol):
    network_capable: bool

    def fetch(self, *, url: str, destination: Path) -> dict[str, Any]: ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


@dataclass
class LiveExactPdfSource:
    user_agent: str = "ROBO_DADOS_PUBLICOS/0.8.0 TASK249"
    timeout: int = 120
    network_capable: bool = True

    def fetch(self, *, url: str, destination: Path) -> dict[str, Any]:
        opener = build_opener(_NoRedirect())
        request = Request(url, headers={"User-Agent": self.user_agent}, method="GET")
        destination.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        total = 0
        try:
            with opener.open(request, timeout=self.timeout) as response, destination.open("wb") as output:
                status = int(getattr(response, "status", 200) or 200)
                final_url = str(response.geturl())
                content_type = str(response.headers.get("Content-Type") or "")
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    output.write(block)
                    digest.update(block)
                    total += len(block)
        except HTTPError as exc:
            raise Task249Stop(f"SOURCE_HTTP_{exc.code}") from exc
        return {
            "http_status": status,
            "requested_url": url,
            "final_url": final_url,
            "content_type": content_type,
            "bytes": total,
            "sha256": digest.hexdigest(),
            "path": str(destination),
        }


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path: str | Path = "config/task249_jom_bounded_pdf_acquisition.v1.json") -> dict[str, Any]:
    return _read_json(path)


def load_queue(path: str | Path = "config/task248_jom_bounded_ingestion_queue.v1.json") -> dict[str, Any]:
    return _read_json(path)


def _stop(code: str, *, source_gets: int = 0, **details: object) -> dict[str, Any]:
    return {
        "status": code,
        "live_attempt_completed": False,
        "source_gets": source_gets,
        "document_download_count": source_gets,
        "retry_performed": False,
        "redirect_followed": False,
        "alternate_url_discovery_performed": False,
        "raw_pdf_persisted": False,
        "drive_write_count": 0,
        "bronze_created": 0,
        "silver_created": 0,
        "gold_created": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        **details,
    }


def _validate_queue(config: dict[str, Any], queue: dict[str, Any]) -> list[dict[str, Any]]:
    if queue.get("schema") != "TASK248_JOM_BOUNDED_INGESTION_QUEUE_V1":
        raise Task249Stop("QUEUE_SCHEMA_MISMATCH")
    if queue.get("status") != "INERT_OFFLINE_QUEUE_READY_FOR_SEPARATE_AUTHORIZATION":
        raise Task249Stop("QUEUE_STATUS_MISMATCH")
    items = queue.get("items")
    if not isinstance(items, list) or len(items) != 4:
        raise Task249Stop("QUEUE_COUNT_MISMATCH")
    editions = [item.get("edition") for item in items if isinstance(item, dict)]
    if editions != EXPECTED_EDITIONS:
        raise Task249Stop("QUEUE_EDITIONS_MISMATCH")
    if config.get("scope", {}).get("editions") != EXPECTED_EDITIONS:
        raise Task249Stop("CONFIG_EDITIONS_MISMATCH")
    if config.get("scope", {}).get("document_count") != 4:
        raise Task249Stop("CONFIG_DOCUMENT_COUNT_MISMATCH")
    seen_urls: set[str] = set()
    seen_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise Task249Stop("QUEUE_ITEM_INVALID")
        url = str(item.get("document_url") or "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
            raise Task249Stop("QUEUE_URL_INVALID")
        source_id = str(item.get("source_id") or "")
        if not source_id or url in seen_urls or source_id in seen_ids:
            raise Task249Stop("QUEUE_DUPLICATE_OR_EMPTY_ID")
        seen_urls.add(url)
        seen_ids.add(source_id)
    effects = queue.get("effects") or {}
    if any(bool(value) for value in effects.values()):
        raise Task249Stop("TASK248_QUEUE_EFFECTS_NOT_INERT")
    return items


def validate_config(config: dict[str, Any], queue: dict[str, Any]) -> dict[str, Any]:
    if config.get("task") != "TASK_249" or config.get("schema") != "TASK249_JOM_BOUNDED_PDF_ACQUISITION_V1":
        raise Task249Stop("CONFIG_IDENTITY_MISMATCH")
    if config.get("mode") != "T1_READONLY_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION":
        raise Task249Stop("CONFIG_MODE_MISMATCH")
    if config.get("implementation_branch") != EXPECTED_BRANCH:
        raise Task249Stop("CONFIG_BRANCH_MISMATCH")
    source = config.get("source") or {}
    if source.get("family") != EXPECTED_SOURCE or source.get("allowed_document_hosts") != [ALLOWED_HOST]:
        raise Task249Stop("CONFIG_SOURCE_MISMATCH")
    limits = config.get("limits") or {}
    expected_limits = {
        "max_source_gets": 4,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
    }
    if any(limits.get(key) != value for key, value in expected_limits.items()):
        raise Task249Stop("CONFIG_LIMIT_MISMATCH")
    max_bytes = limits.get("max_pdf_bytes_each")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1_000_000 <= max_bytes <= 150_000_000:
        raise Task249Stop("CONFIG_MAX_BYTES_INVALID")
    persistence = config.get("persistence") or {}
    if persistence.get("sanitized_result_artifact") is not True or persistence.get("artifact_retention_days") != 1:
        raise Task249Stop("CONFIG_SANITIZED_PERSISTENCE_MISMATCH")
    for key in ("raw_pdf_artifact", "raw_pdf_repository", "drive_write", "serving_write", "publication"):
        if persistence.get(key) is not False:
            raise Task249Stop("CONFIG_PROHIBITED_PERSISTENCE_ENABLED")
    auth = config.get("authorization") or {}
    if auth.get("required_task") != "TASK_249_LIVE_AUTHORIZATION" or auth.get("required_operation") != "EXACT_4_JOM_PDF_GETS_SANITIZED_METADATA_ONLY":
        raise Task249Stop("CONFIG_AUTH_IDENTITY_MISMATCH")
    if auth.get("attempt_count") != 1 or auth.get("owner_authorized") is not True:
        raise Task249Stop("CONFIG_AUTH_BOUND_MISMATCH")
    for key, value in auth.items():
        if key.endswith("_authorized") and key != "owner_authorized" and value is not False:
            raise Task249Stop("CONFIG_DOWNSTREAM_AUTHORIZATION_ENABLED")
    items = _validate_queue(config, queue)
    return {"status": "PASS_TASK249_CONFIG", "documents": len(items)}


def validate_live_authorization(authorization: dict[str, Any] | None, *, expected_sha: str) -> dict[str, Any]:
    if not authorization:
        return _stop("STOP_TASK249_LIVE_NOT_AUTHORIZED")
    if authorization.get("synthetic_test_only") is True:
        return _stop("STOP_TASK249_SYNTHETIC_AUTH_NOT_LIVE")
    required = {
        "task": "TASK_249_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "branch": EXPECTED_BRANCH,
        "implementation_sha": expected_sha,
        "source": EXPECTED_SOURCE,
        "operation": "EXACT_4_JOM_PDF_GETS_SANITIZED_METADATA_ONLY",
        "max_source_gets": 4,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
        "drive_write": False,
        "bronze": False,
        "silver": False,
        "gold": False,
        "ocr": False,
        "semantic_parser": False,
        "serving": False,
        "publication": False,
        "promotion": False,
        "schedule": False,
        "recurrence": False,
        "owner_authorized": True,
        "consumed": False,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        return _stop("STOP_TASK249_AUTHORIZATION_CONTRACT_MISMATCH")
    if authorization.get("editions") != EXPECTED_EDITIONS:
        return _stop("STOP_TASK249_AUTHORIZATION_SCOPE_MISMATCH")
    return {"status": "PASS_TASK249_LIVE_AUTHORIZATION"}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _pdf_pages(path: Path) -> int:
    try:
        pages = len(PdfReader(str(path), strict=False).pages)
    except Exception as exc:
        raise Task249Stop("SOURCE_PDF_PARSE_FAILED") from exc
    if pages <= 0:
        raise Task249Stop("SOURCE_PDF_PAGE_COUNT_NOT_POSITIVE")
    return pages


def _validate_download(result: dict[str, Any], item: dict[str, Any], *, max_bytes: int) -> dict[str, Any]:
    if result.get("http_status") != 200:
        raise Task249Stop("SOURCE_HTTP_NOT_200")
    expected_url = item["document_url"]
    if result.get("requested_url") != expected_url or result.get("final_url") != expected_url:
        raise Task249Stop("SOURCE_URL_REDIRECT_OR_DRIFT")
    ctype = str(result.get("content_type") or "").split(";", 1)[0].strip().lower()
    if ctype not in {"application/pdf", "application/octet-stream"}:
        raise Task249Stop("SOURCE_CONTENT_TYPE_UNEXPECTED")
    path = Path(str(result.get("path") or ""))
    if not path.is_file():
        raise Task249Stop("SOURCE_FILE_MISSING")
    size = path.stat().st_size
    if size <= 0 or size > max_bytes or result.get("bytes") != size:
        raise Task249Stop("SOURCE_BYTE_COUNT_INVALID")
    with path.open("rb") as source:
        if source.read(5) != b"%PDF-":
            raise Task249Stop("SOURCE_PDF_SIGNATURE_INVALID")
    sha = _sha256_file(path)
    if result.get("sha256") != sha:
        raise Task249Stop("SOURCE_HASH_TRANSPORT_MISMATCH")
    pages = _pdf_pages(path)
    return {
        "edition": item["edition"],
        "publication_date": item["publication_date"],
        "source_id": item["source_id"],
        "logical_key": item["logical_key"],
        "document_url": expected_url,
        "content_type": ctype,
        "bytes": size,
        "sha256": sha,
        "pages": pages,
    }


def execute(
    config: dict[str, Any],
    queue: dict[str, Any],
    *,
    source: PdfSource,
    authorization: dict[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    try:
        validate_config(config, queue)
    except Task249Stop as exc:
        return _stop(f"STOP_TASK249_{exc}")

    if offline_test_mode:
        if getattr(source, "network_capable", True):
            return _stop("STOP_TASK249_OFFLINE_NETWORK_CAPABLE_SOURCE")
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return _stop("STOP_TASK249_OFFLINE_SYNTHETIC_AUTH_REQUIRED")
    else:
        if not getattr(source, "network_capable", False):
            return _stop("STOP_TASK249_LIVE_SOURCE_NOT_NETWORK_CAPABLE")
        auth = validate_live_authorization(authorization, expected_sha=expected_implementation_sha)
        if auth["status"] != "PASS_TASK249_LIVE_AUTHORIZATION":
            return auth

    items = queue["items"]
    max_bytes = int(config["limits"]["max_pdf_bytes_each"])
    source_gets = 0
    documents: list[dict[str, Any]] = []
    try:
        with tempfile.TemporaryDirectory(prefix="task249_") as temp_dir:
            root = Path(temp_dir)
            for item in items:
                if source_gets >= 4:
                    raise Task249Stop("SOURCE_GET_BUDGET_EXCEEDED")
                destination = root / f"jom_{item['edition']}.pdf"
                result = source.fetch(url=item["document_url"], destination=destination)
                source_gets += 1
                documents.append(_validate_download(result, item, max_bytes=max_bytes))
            if sorted(path.name for path in root.glob("*.pdf")) != [f"jom_{edition}.pdf" for edition in EXPECTED_EDITIONS]:
                raise Task249Stop("TEMPORARY_PDF_SET_MISMATCH")
    except Task249Stop as exc:
        return _stop(f"STOP_TASK249_{exc}", source_gets=source_gets, documents=documents)

    if source_gets != 4 or len(documents) != 4:
        return _stop("STOP_TASK249_INCOMPLETE_DOCUMENT_SET", source_gets=source_gets, documents=documents)

    return {
        "status": PASS_STATUS,
        "live_attempt_completed": not offline_test_mode,
        "source_gets": source_gets,
        "document_download_count": 4,
        "documents": documents,
        "retry_performed": False,
        "redirect_followed": False,
        "alternate_url_discovery_performed": False,
        "raw_pdf_persisted": False,
        "drive_write_count": 0,
        "bronze_created": 0,
        "silver_created": 0,
        "gold_created": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "absence_inference_allowed": False,
        "next_gate": "CANONIZE_TASK249_RESULT_BEFORE_CUSTODY_OR_PARSE",
    }
