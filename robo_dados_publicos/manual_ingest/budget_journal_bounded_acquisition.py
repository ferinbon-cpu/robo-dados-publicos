"""Bounded, fail-closed acquisition boundary for F01 Jornal Oficial originals.

TASK 032 implements the future live operation but does not embed authorization.
Offline tests use injected non-network transports/stores. A real invocation must
carry a fresh owner authorization bound to the exact implementation SHA.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pypdf import PdfReader

from robo_dados_publicos.storage.drive_rest import DriveRESTClient


EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
EXPECTED_BRANCH = "main"
EXPECTED_SOURCE = "LIMEIRA_JORNAL_OFICIAL"
EXPECTED_TARGET_FOLDER_ID = "1CdL4T1CVIPqNph3f5xHbiU8KgxgPpkl5"
ALLOWED_HOST = "ecrie.com.br"


class BudgetJournalAcquisitionStop(RuntimeError):
    pass


class SourceTransport(Protocol):
    network_capable: bool

    def fetch(self, *, url: str, destination: Path) -> dict[str, Any]: ...


class CustodyStore(Protocol):
    network_capable: bool

    def inventory(self, *, parent_id: str) -> dict[str, Any]: ...
    def create(self, *, local_path: Path, remote_name: str, parent_id: str) -> dict[str, Any]: ...
    def readback(self, *, file_id: str, destination: Path) -> dict[str, Any]: ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


@dataclass
class ExactPinnedHttpTransport:
    """Exact-URL HTTP GET transport with redirects disabled."""

    user_agent: str = "ROBO_DADOS_PUBLICOS/0.8.0 TASK032"
    timeout: int = 120
    network_capable: bool = True

    def fetch(self, *, url: str, destination: Path) -> dict[str, Any]:
        opener = build_opener(_NoRedirect())
        req = Request(url, headers={"User-Agent": self.user_agent}, method="GET")
        destination.parent.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha256()
        total = 0
        try:
            with opener.open(req, timeout=self.timeout) as resp, destination.open("wb") as out:
                status = int(getattr(resp, "status", 200) or 200)
                final_url = str(resp.geturl())
                content_type = str(resp.headers.get("Content-Type") or "")
                while True:
                    block = resp.read(1024 * 1024)
                    if not block:
                        break
                    out.write(block)
                    h.update(block)
                    total += len(block)
        except HTTPError as exc:
            raise BudgetJournalAcquisitionStop(f"SOURCE_HTTP_{exc.code}") from exc
        return {
            "http_status": status,
            "requested_url": url,
            "final_url": final_url,
            "content_type": content_type,
            "bytes": total,
            "sha256": h.hexdigest(),
            "path": str(destination),
        }


@dataclass
class DriveCustodyStore:
    """Small create-only adapter around the repository's Drive REST client."""

    client: DriveRESTClient
    network_capable: bool = True

    def inventory(self, *, parent_id: str) -> dict[str, Any]:
        page = self.client.list_children_single_page(parent_id, page_size=1000)
        return {"items": page["files"], "next_page_token": page.get("next_page_token")}

    def create(self, *, local_path: Path, remote_name: str, parent_id: str) -> dict[str, Any]:
        return self.client.put(local_path, remote_name, parent_id, mime_type="application/pdf")

    def readback(self, *, file_id: str, destination: Path) -> dict[str, Any]:
        return self.client.get(file_id, destination)


def stop(code: str, **details: object) -> dict[str, Any]:
    return {
        "status": code,
        "live_attempt_completed": False,
        "source_gets": int(details.pop("source_gets", 0)),
        "drive_inventory_requests": int(details.pop("drive_inventory_requests", 0)),
        "drive_creates": int(details.pop("drive_creates", 0)),
        "drive_readbacks": int(details.pop("drive_readbacks", 0)),
        "cleanup_performed": False,
        "retry_performed": False,
        "owner_decision_required": bool(details.pop("owner_decision_required", False)),
        "bronze_created": 0,
        "silver_created": 0,
        "gold_created": 0,
        **details,
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _pdf_pages(path: Path) -> int:
    try:
        return len(PdfReader(str(path), strict=False).pages)
    except Exception as exc:  # pypdf exposes several parser exception types
        raise BudgetJournalAcquisitionStop("SOURCE_PDF_PARSE_FAILED") from exc


def validate_contract(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("task") != "TASK_032_BUDGET_JOURNAL_BOUNDED_ACQUISITION":
        raise BudgetJournalAcquisitionStop("CONTRACT_TASK_MISMATCH")
    if data.get("mode") != "T0_OFFLINE_IMPLEMENTATION_LIVE_DISABLED_BY_DEFAULT":
        raise BudgetJournalAcquisitionStop("CONTRACT_MODE_MISMATCH")
    if data.get("repository") != EXPECTED_REPOSITORY or data.get("branch") != EXPECTED_BRANCH:
        raise BudgetJournalAcquisitionStop("CONTRACT_REPOSITORY_MISMATCH")
    if data.get("source") != EXPECTED_SOURCE:
        raise BudgetJournalAcquisitionStop("CONTRACT_SOURCE_MISMATCH")

    target = data.get("target") or {}
    if target.get("folder_id") != EXPECTED_TARGET_FOLDER_ID:
        raise BudgetJournalAcquisitionStop("CONTRACT_TARGET_FOLDER_MISMATCH")
    if target.get("write_mode") != "CREATE_ONLY":
        raise BudgetJournalAcquisitionStop("CONTRACT_WRITE_MODE_MISMATCH")

    limits = data.get("limits") or {}
    expected_limits = {
        "source_gets": 3,
        "drive_inventory_requests": 1,
        "drive_creates": 3,
        "drive_readbacks": 3,
        "automatic_retry": False,
        "pagination_expansion": False,
        "alternate_url_discovery": False,
    }
    if any(limits.get(k) != v for k, v in expected_limits.items()):
        raise BudgetJournalAcquisitionStop("CONTRACT_LIMIT_MISMATCH")
    max_bytes = limits.get("max_pdf_bytes_each")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1_000_000 <= max_bytes <= 150_000_000:
        raise BudgetJournalAcquisitionStop("CONTRACT_MAX_BYTES_INVALID")

    documents = data.get("documents")
    if not isinstance(documents, list) or len(documents) != 3:
        raise BudgetJournalAcquisitionStop("CONTRACT_DOCUMENT_COUNT")
    expected = {
        "LDO": ("7.141/2025", 7024, "2025-07-08", 79, "u_137_07072025191855.pdf", "SOURCE_JOM_7024_2025-07-08_LDO_7141_2025.pdf"),
        "PPA": ("7.213/2025", 7119, "2025-11-15", 107, "u_137_14112025171148.pdf", "SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf"),
        "LOA": ("7.223/2025", 7127, "2025-11-29", 631, "u_137_28112025211140.pdf", "SOURCE_JOM_7127_2025-11-29_LOA_7223_2025.pdf"),
    }
    by_family = {d.get("family"): d for d in documents if isinstance(d, dict)}
    if set(by_family) != set(expected):
        raise BudgetJournalAcquisitionStop("CONTRACT_DOCUMENT_FAMILY")
    seen_urls: set[str] = set()
    seen_names: set[str] = set()
    for family, values in expected.items():
        law, edition, date, pages, suffix, filename = values
        doc = by_family[family]
        if (doc.get("law_number"), doc.get("edition"), doc.get("publication_date"), doc.get("expected_pages")) != (law, edition, date, pages):
            raise BudgetJournalAcquisitionStop(f"CONTRACT_{family}_IDENTITY")
        url = str(doc.get("url") or "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST or not url.endswith(suffix):
            raise BudgetJournalAcquisitionStop(f"CONTRACT_{family}_URL")
        if doc.get("target_filename") != filename:
            raise BudgetJournalAcquisitionStop(f"CONTRACT_{family}_FILENAME")
        if url in seen_urls or filename in seen_names:
            raise BudgetJournalAcquisitionStop("CONTRACT_DUPLICATE_TARGET")
        seen_urls.add(url)
        seen_names.add(filename)

    prohibited = data.get("prohibited") or {}
    required_true = {"overwrite", "replace", "delete", "cleanup", "retry", "ocr", "parser", "bronze", "silver", "gold", "serving", "publication", "schedule", "recurrence"}
    if any(prohibited.get(k) is not True for k in required_true):
        raise BudgetJournalAcquisitionStop("CONTRACT_PROHIBITION_WEAKENED")
    auth = data.get("authorization") or {}
    if auth.get("embedded_live_authorization") is not False or auth.get("owner_authorization_required") is not True or auth.get("implementation_sha_must_match") is not True or auth.get("authorization_consumed_after_first_live_attempt") is not True:
        raise BudgetJournalAcquisitionStop("CONTRACT_AUTHORIZATION_WEAKENED")
    return {"status": "PASS_TASK_032_CONTRACT", "documents": 3}


def validate_live_authorization(authorization: dict[str, Any] | None, *, expected_sha: str) -> dict[str, Any]:
    if not authorization:
        return stop("STOP_TASK_032_LIVE_NOT_AUTHORIZED")
    if authorization.get("synthetic_test_only") is True:
        return stop("STOP_TASK_032_SYNTHETIC_AUTH_NOT_LIVE")
    required = {
        "task": "TASK_032_BUDGET_JOURNAL_BOUNDED_ACQUISITION",
        "repository": EXPECTED_REPOSITORY,
        "branch": EXPECTED_BRANCH,
        "implementation_sha": expected_sha,
        "source": EXPECTED_SOURCE,
        "operation": "EXACT_3_JOM_PDF_GETS_CREATE_ONLY_CUSTODY_READBACK",
        "target_folder_id": EXPECTED_TARGET_FOLDER_ID,
        "max_source_gets": 3,
        "max_drive_inventory_requests": 1,
        "max_drive_creates": 3,
        "max_drive_readbacks": 3,
        "automatic_retry": False,
        "overwrite": False,
        "replace": False,
        "delete": False,
        "cleanup": False,
        "ocr": False,
        "parser": False,
        "bronze": False,
        "silver": False,
        "gold": False,
        "serving": False,
        "publication": False,
        "schedule": False,
        "recurrence": False,
        "owner_authorized": True,
        "consumed": False,
    }
    if any(authorization.get(k) != v for k, v in required.items()):
        return stop("STOP_TASK_032_AUTHORIZATION_CONTRACT_MISMATCH")
    return {"status": "PASS_TASK_032_LIVE_AUTHORIZATION"}


def _validate_download(*, result: dict[str, Any], doc: dict[str, Any], max_bytes: int) -> dict[str, Any]:
    if result.get("http_status") != 200:
        raise BudgetJournalAcquisitionStop("SOURCE_HTTP_NOT_200")
    if result.get("requested_url") != doc["url"] or result.get("final_url") != doc["url"]:
        raise BudgetJournalAcquisitionStop("SOURCE_URL_REDIRECT_OR_DRIFT")
    ctype = str(result.get("content_type") or "").split(";", 1)[0].strip().lower()
    if ctype != "application/pdf":
        raise BudgetJournalAcquisitionStop("SOURCE_CONTENT_TYPE_NOT_PDF")
    path = Path(str(result.get("path") or ""))
    if not path.is_file():
        raise BudgetJournalAcquisitionStop("SOURCE_FILE_MISSING")
    size = path.stat().st_size
    if size <= 0 or size > max_bytes or result.get("bytes") != size:
        raise BudgetJournalAcquisitionStop("SOURCE_BYTE_COUNT_INVALID")
    with path.open("rb") as src:
        if src.read(5) != b"%PDF-":
            raise BudgetJournalAcquisitionStop("SOURCE_PDF_SIGNATURE_INVALID")
    sha = _sha256_file(path)
    if result.get("sha256") != sha:
        raise BudgetJournalAcquisitionStop("SOURCE_HASH_TRANSPORT_MISMATCH")
    pages = _pdf_pages(path)
    if pages != doc["expected_pages"]:
        raise BudgetJournalAcquisitionStop("SOURCE_PAGE_COUNT_MISMATCH")
    return {"family": doc["family"], "edition": doc["edition"], "filename": doc["target_filename"], "bytes": size, "sha256": sha, "pages": pages, "path": path}


def _check_inventory(result: dict[str, Any], *, target_names: set[str]) -> None:
    if result.get("next_page_token") not in (None, ""):
        raise BudgetJournalAcquisitionStop("DRIVE_INVENTORY_PAGINATION_NOT_ALLOWED")
    items = result.get("items")
    if not isinstance(items, list):
        raise BudgetJournalAcquisitionStop("DRIVE_INVENTORY_INVALID")
    names = [str(x.get("name")) for x in items if isinstance(x, dict)]
    collisions = sorted(target_names.intersection(names))
    if collisions:
        raise BudgetJournalAcquisitionStop("DRIVE_TARGET_NAME_COLLISION")


def _verify_readback(*, result: dict[str, Any], source: dict[str, Any]) -> None:
    path = Path(str(result.get("path") or ""))
    if not path.is_file():
        raise BudgetJournalAcquisitionStop("DRIVE_READBACK_FILE_MISSING")
    if result.get("bytes") != source["bytes"] or path.stat().st_size != source["bytes"]:
        raise BudgetJournalAcquisitionStop("DRIVE_READBACK_BYTES_MISMATCH")
    sha = _sha256_file(path)
    if result.get("sha256") != source["sha256"] or sha != source["sha256"]:
        raise BudgetJournalAcquisitionStop("DRIVE_READBACK_SHA256_MISMATCH")
    if _pdf_pages(path) != source["pages"]:
        raise BudgetJournalAcquisitionStop("DRIVE_READBACK_PAGE_COUNT_MISMATCH")


def run_acquisition(*, contract: dict[str, Any], source: SourceTransport, store: CustodyStore,
                    authorization: dict[str, Any] | None, expected_sha: str,
                    work_dir: str | Path | None = None, offline_test_mode: bool = False) -> dict[str, Any]:
    """Run the exact-three custody proof after authorization or with synthetic fakes."""
    try:
        validate_contract(contract)
    except BudgetJournalAcquisitionStop as exc:
        return stop(f"STOP_TASK_032_{exc}")

    if offline_test_mode:
        if getattr(source, "network_capable", True) or getattr(store, "network_capable", True):
            return stop("STOP_TASK_032_OFFLINE_NETWORK_CAPABLE_DEPENDENCY")
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return stop("STOP_TASK_032_OFFLINE_SYNTHETIC_AUTH_REQUIRED")
    else:
        auth = validate_live_authorization(authorization, expected_sha=expected_sha)
        if auth["status"] != "PASS_TASK_032_LIVE_AUTHORIZATION":
            return auth

    root = Path(work_dir) if work_dir is not None else Path(tempfile.mkdtemp(prefix="task032_jom_"))
    root.mkdir(parents=True, exist_ok=True)
    source_gets = inventory_requests = creates = readbacks = 0
    validated: list[dict[str, Any]] = []
    max_bytes = int(contract["limits"]["max_pdf_bytes_each"])

    for doc in contract["documents"]:
        destination = root / ("source__" + doc["target_filename"])
        try:
            raw = source.fetch(url=doc["url"], destination=destination)
            source_gets += 1
            validated.append(_validate_download(result=raw, doc=doc, max_bytes=max_bytes))
        except Exception as exc:
            code = str(exc) if isinstance(exc, BudgetJournalAcquisitionStop) else "SOURCE_REMOTE_OPERATION_FAILED"
            return stop(f"STOP_TASK_032_{code}", source_gets=source_gets)

    target_names = {x["filename"] for x in validated}
    try:
        inv = store.inventory(parent_id=contract["target"]["folder_id"])
        inventory_requests += 1
        _check_inventory(inv, target_names=target_names)
    except Exception as exc:
        code = str(exc) if isinstance(exc, BudgetJournalAcquisitionStop) else "DRIVE_INVENTORY_REMOTE_OPERATION_FAILED"
        return stop(f"STOP_TASK_032_{code}", source_gets=source_gets, drive_inventory_requests=inventory_requests)

    custody: list[dict[str, Any]] = []
    for item in validated:
        try:
            created = store.create(local_path=item["path"], remote_name=item["filename"], parent_id=contract["target"]["folder_id"])
            creates += 1
            if created.get("name") != item["filename"] or created.get("mimeType") != "application/pdf":
                raise BudgetJournalAcquisitionStop("DRIVE_CREATE_METADATA_MISMATCH")
            parents = created.get("parents") or []
            if contract["target"]["folder_id"] not in parents:
                raise BudgetJournalAcquisitionStop("DRIVE_CREATE_PARENT_MISMATCH")
            file_id = created.get("id")
            if not isinstance(file_id, str) or not file_id:
                raise BudgetJournalAcquisitionStop("DRIVE_CREATE_ID_MISSING")
            rb_path = root / ("readback__" + item["filename"])
            rb = store.readback(file_id=file_id, destination=rb_path)
            readbacks += 1
            _verify_readback(result=rb, source=item)
            custody.append({k: item[k] for k in ("family", "edition", "filename", "bytes", "sha256", "pages")})
        except Exception as exc:
            code = str(exc) if isinstance(exc, BudgetJournalAcquisitionStop) else "DRIVE_REMOTE_OPERATION_FAILED"
            return stop(
                f"STOP_TASK_032_{code}",
                source_gets=source_gets,
                drive_inventory_requests=inventory_requests,
                drive_creates=creates,
                drive_readbacks=readbacks,
                owner_decision_required=creates > 0,
                partial_custody=creates > 0,
            )

    return {
        "status": "PASS_TASK_032_JOM_EXACT_3_SOURCE_CUSTODY_READBACK_VERIFIED",
        "live_attempt_completed": not offline_test_mode,
        "source_gets": source_gets,
        "drive_inventory_requests": inventory_requests,
        "drive_creates": creates,
        "drive_readbacks": readbacks,
        "custody": custody,
        "cleanup_performed": False,
        "retry_performed": False,
        "owner_decision_required": False,
        "parser_executed": False,
        "ocr_executed": False,
        "bronze_created": 0,
        "silver_created": 0,
        "gold_created": 0,
        "serving_mutated": False,
        "publication_performed": False,
    }


def load_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_contract(data)
    return data


def expected_sha_from_environment() -> str:
    sha = os.getenv("GITHUB_SHA", "").strip()
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha.lower()):
        raise BudgetJournalAcquisitionStop("GITHUB_SHA_INVALID")
    return sha.lower()
