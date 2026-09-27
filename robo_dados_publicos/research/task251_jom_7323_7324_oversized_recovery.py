"""TASK251: canonize TASK250 oversize proof and prepare bounded recovery for JOM 7323-7324."""
from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task251_jom_7323_7324_oversized_recovery.v1.json"
DEFAULT_EVIDENCE = ROOT / "docs/evidence/TASK_251_TASK250_OVERSIZE_CANONICAL_0.8.0.json"

EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
EXPECTED_BRANCH = "main"
EXPECTED_SOURCE = "LIMEIRA_JORNAL_OFICIAL"
EXPECTED_EDITIONS = [7323, 7324]
ALLOWED_HOST = "ecrie.com.br"
PASS_STATUS = "PASS_TASK251_BOUNDED_OVERSIZED_RECOVERY"


class Task251Stop(RuntimeError):
    pass


class PdfSource(Protocol):
    network_capable: bool

    def fetch(self, *, url: str, destination: Path, max_bytes: int) -> dict[str, Any]: ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


@dataclass
class LiveExactPdfSource:
    user_agent: str = "ROBO_DADOS_PUBLICOS/0.8.0 TASK251"
    timeout: int = 180
    network_capable: bool = True

    def fetch(self, *, url: str, destination: Path, max_bytes: int) -> dict[str, Any]:
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
                    remaining = max_bytes - total
                    if remaining < 0:
                        raise Task251Stop("SOURCE_STREAM_BYTE_CAP_EXCEEDED")
                    block = response.read(min(1024 * 1024, remaining + 1))
                    if not block:
                        break
                    if len(block) > remaining:
                        raise Task251Stop("SOURCE_STREAM_BYTE_CAP_EXCEEDED")
                    output.write(block)
                    digest.update(block)
                    total += len(block)
        except HTTPError as exc:
            raise Task251Stop(f"SOURCE_HTTP_{exc.code}") from exc
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


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return _read_json(path)


def load_canonical_evidence(path: str | Path = DEFAULT_EVIDENCE) -> dict[str, Any]:
    return _read_json(path)


def validate_canonical_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    if evidence.get("task") != "TASK_251" or evidence.get("schema") != "TASK251_TASK250_OVERSIZE_CANONICAL_V1":
        raise Task251Stop("EVIDENCE_IDENTITY_MISMATCH")
    if evidence.get("status") != "PASS_TASK250_OVERSIZE_RESULT_CANONIZED":
        raise Task251Stop("EVIDENCE_STATUS_MISMATCH")
    expected = {
        "implementation_sha": "40ce45d28ed18af0a2ce24d6bd2d651b87a5a2c5",
        "runtime_head": "563f5cfe2d381b2a2d3359603836dae1ea0bbf07",
    }
    if any(evidence.get(key) != value for key, value in expected.items()):
        raise Task251Stop("EVIDENCE_PROVENANCE_MISMATCH")
    run = evidence.get("run") or {}
    if run != {"id": 35236892194, "conclusion": "success", "attempt": 1}:
        raise Task251Stop("EVIDENCE_RUN_MISMATCH")
    artifact = evidence.get("artifact") or {}
    if artifact.get("id") != 10502829335:
        raise Task251Stop("EVIDENCE_ARTIFACT_ID_MISMATCH")
    if artifact.get("name") != "task-250-jom-7323-bytecount-diagnostic-sanitized":
        raise Task251Stop("EVIDENCE_ARTIFACT_NAME_MISMATCH")
    if artifact.get("zip_sha256") != "013e44c8711f444d884dd157639bd02d5839fc7337b1713c002f7ce45ad2ea8a":
        raise Task251Stop("EVIDENCE_ARTIFACT_HASH_MISMATCH")

    result = dict(evidence.get("sanitized_result") or {})
    embedded_hash = result.pop("result_sha256", None)
    recomputed = _canonical_hash(result)
    if embedded_hash != "70e0de78992bc555cac65a6e5fec0096aa20d98364d06a4c30e1f59c0e560065":
        raise Task251Stop("EVIDENCE_RESULT_HASH_IDENTITY_MISMATCH")
    if recomputed != embedded_hash:
        raise Task251Stop("EVIDENCE_RESULT_HASH_RECOMPUTE_MISMATCH")
    if result.get("status") != "PASS_TASK250_7323_BYTECOUNT_DIAGNOSTIC":
        raise Task251Stop("EVIDENCE_TASK250_STATUS_MISMATCH")
    if result.get("source_gets") != 1 or result.get("drive_write_count") != 0:
        raise Task251Stop("EVIDENCE_EFFECT_COUNT_MISMATCH")
    if result.get("raw_pdf_persisted") is not False or result.get("retry_performed") is not False:
        raise Task251Stop("EVIDENCE_PROHIBITED_EFFECT_MISMATCH")
    if result.get("redirect_followed") is not False:
        raise Task251Stop("EVIDENCE_REDIRECT_MISMATCH")

    diagnostic = result.get("diagnostic") or {}
    required_diag = {
        "edition": 7323,
        "source_id": "LIMEIRA_JO_07323",
        "logical_key": "limeira/jornal_oficial/edicao/7323",
        "document_url": "https://ecrie.com.br/Sistema/Conteudos/DiarioOficial/upload/u_137_10092026192416.pdf",
        "http_status": 200,
        "content_type": "application/pdf",
        "transport_bytes": 126648737,
        "temporary_stat_bytes": 126648737,
        "configured_max_bytes": 100000000,
        "byte_count_outcome": "OVER_MAX_BYTES",
    }
    if any(diagnostic.get(key) != value for key, value in required_diag.items()):
        raise Task251Stop("EVIDENCE_DIAGNOSTIC_MISMATCH")
    if diagnostic["transport_bytes"] != diagnostic["temporary_stat_bytes"]:
        raise Task251Stop("EVIDENCE_TRANSPORT_STAT_MISMATCH")
    if diagnostic["transport_bytes"] <= diagnostic["configured_max_bytes"]:
        raise Task251Stop("EVIDENCE_OVERSIZE_NOT_PROVEN")

    context = evidence.get("task249_context") or {}
    proven = context.get("proven_documents") or []
    if [row.get("edition") for row in proven] != [7321, 7322]:
        raise Task251Stop("EVIDENCE_TASK249_PROVEN_SET_MISMATCH")
    if context.get("blocked_edition") != 7323 or context.get("unattempted_editions") != [7324]:
        raise Task251Stop("EVIDENCE_TASK249_REMAINDER_MISMATCH")

    adjudication = evidence.get("adjudication") or {}
    if adjudication.get("cause") != "OVER_MAX_BYTES":
        raise Task251Stop("EVIDENCE_ADJUDICATION_MISMATCH")
    if adjudication.get("observed_bytes") != 126648737 or adjudication.get("old_cap_bytes") != 100000000:
        raise Task251Stop("EVIDENCE_ADJUDICATION_BYTES_MISMATCH")
    if adjudication.get("transport_stat_match") is not True:
        raise Task251Stop("EVIDENCE_ADJUDICATION_COUNTER_MISMATCH")
    return {"status": "PASS_TASK251_CANONICAL_EVIDENCE", "result_sha256": recomputed}


def validate_config(config: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    validate_canonical_evidence(evidence)
    if config.get("task") != "TASK_251" or config.get("schema") != "TASK251_JOM_7323_7324_OVERSIZED_RECOVERY_V1":
        raise Task251Stop("CONFIG_IDENTITY_MISMATCH")
    if config.get("base_main_sha") != "40ce45d28ed18af0a2ce24d6bd2d651b87a5a2c5":
        raise Task251Stop("CONFIG_BASE_MISMATCH")
    if config.get("mode") != "T1_READONLY_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION":
        raise Task251Stop("CONFIG_MODE_MISMATCH")
    source = config.get("source") or {}
    if source.get("family") != EXPECTED_SOURCE or source.get("allowed_document_hosts") != [ALLOWED_HOST]:
        raise Task251Stop("CONFIG_SOURCE_MISMATCH")
    targets = config.get("targets")
    if not isinstance(targets, list) or len(targets) != 2:
        raise Task251Stop("CONFIG_TARGET_COUNT_MISMATCH")
    if [row.get("edition") for row in targets] != EXPECTED_EDITIONS:
        raise Task251Stop("CONFIG_TARGET_EDITION_MISMATCH")
    if any(row.get("edition") in {7321, 7322} for row in targets):
        raise Task251Stop("CONFIG_PROVEN_EDITION_REDOWNLOAD_FORBIDDEN")
    expected_ids = ["LIMEIRA_JO_07323", "LIMEIRA_JO_07324"]
    expected_dates = ["2026-09-11", "2026-09-12"]
    if [row.get("source_id") for row in targets] != expected_ids:
        raise Task251Stop("CONFIG_TARGET_SOURCE_ID_MISMATCH")
    if [row.get("publication_date") for row in targets] != expected_dates:
        raise Task251Stop("CONFIG_TARGET_DATE_MISMATCH")
    if len({row.get("document_url") for row in targets}) != 2:
        raise Task251Stop("CONFIG_TARGET_URL_DUPLICATE")
    for row in targets:
        parsed = urlparse(str(row.get("document_url") or ""))
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != ALLOWED_HOST:
            raise Task251Stop("CONFIG_TARGET_URL_INVALID")

    limits = config.get("limits") or {}
    expected_limits = {
        "max_source_gets": 2,
        "max_pdf_bytes_each": 262144000,
        "max_aggregate_pdf_bytes": 524288000,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
    }
    if any(limits.get(key) != value for key, value in expected_limits.items()):
        raise Task251Stop("CONFIG_LIMIT_MISMATCH")
    if limits["max_pdf_bytes_each"] * 2 > limits["max_aggregate_pdf_bytes"]:
        raise Task251Stop("CONFIG_BUDGET_MATH_INVALID")

    validation = config.get("validation") or {}
    if validation.get("streaming_byte_cap_enforced") is not True:
        raise Task251Stop("CONFIG_STREAM_CAP_NOT_ENFORCED")
    if validation.get("transport_stat_bytes_must_match") is not True:
        raise Task251Stop("CONFIG_COUNTER_CONSISTENCY_NOT_REQUIRED")

    persistence = config.get("persistence") or {}
    if persistence.get("sanitized_result_artifact") is not True or persistence.get("artifact_retention_days") != 1:
        raise Task251Stop("CONFIG_SANITIZED_ARTIFACT_MISMATCH")
    for key in ("raw_pdf_artifact", "raw_pdf_repository", "drive_write", "serving_write", "publication"):
        if persistence.get(key) is not False:
            raise Task251Stop("CONFIG_PROHIBITED_PERSISTENCE_ENABLED")

    auth = config.get("authorization") or {}
    if auth.get("required_task") != "TASK_251_LIVE_AUTHORIZATION":
        raise Task251Stop("CONFIG_AUTH_TASK_MISMATCH")
    if auth.get("required_operation") != "EXACT_2_JOM_7323_7324_OVERSIZED_PDF_GETS_SANITIZED_METADATA_ONLY":
        raise Task251Stop("CONFIG_AUTH_OPERATION_MISMATCH")
    if auth.get("attempt_count") != 1:
        raise Task251Stop("CONFIG_AUTH_ATTEMPT_MISMATCH")
    if auth.get("task249_authorization_reuse_allowed") is not False or auth.get("task250_authorization_reuse_allowed") is not False:
        raise Task251Stop("CONFIG_AUTH_REUSE_ENABLED")
    for key, value in auth.items():
        if key.endswith("_authorized") and value is not False:
            raise Task251Stop("CONFIG_DOWNSTREAM_AUTHORIZATION_ENABLED")
    return {"status": "PASS_TASK251_CONFIG", "targets": 2}


def _stop(code: str, *, source_gets: int = 0, documents: list[dict[str, Any]] | None = None, **details: object) -> dict[str, Any]:
    return {
        "status": code,
        "live_attempt_completed": False,
        "source_gets": source_gets,
        "document_download_count": source_gets,
        "documents": documents or [],
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


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_sha: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if not authorization:
        return _stop("STOP_TASK251_LIVE_NOT_AUTHORIZED")
    if authorization.get("synthetic_test_only") is True:
        return _stop("STOP_TASK251_SYNTHETIC_AUTH_NOT_LIVE")
    if authorization.get("task249_authorization_reused") is True or authorization.get("task250_authorization_reused") is True:
        return _stop("STOP_TASK251_PRIOR_AUTHORIZATION_REUSE")
    limits = config["limits"]
    required = {
        "task": "TASK_251_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "branch": EXPECTED_BRANCH,
        "runtime_branch": config["runtime"]["branch"],
        "implementation_sha": expected_sha,
        "source": EXPECTED_SOURCE,
        "operation": "EXACT_2_JOM_7323_7324_OVERSIZED_PDF_GETS_SANITIZED_METADATA_ONLY",
        "editions": EXPECTED_EDITIONS,
        "max_source_gets": 2,
        "max_pdf_bytes_each": limits["max_pdf_bytes_each"],
        "max_aggregate_pdf_bytes": limits["max_aggregate_pdf_bytes"],
        "attempt_count": 1,
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
        "task249_authorization_reused": False,
        "task250_authorization_reused": False,
        "owner_authorized": True,
        "consumed": False,
    }
    if any(authorization.get(key) != value for key, value in required.items()):
        return _stop("STOP_TASK251_AUTHORIZATION_CONTRACT_MISMATCH")
    return {"status": "PASS_TASK251_LIVE_AUTHORIZATION"}


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
        raise Task251Stop("SOURCE_PDF_PARSE_FAILED") from exc
    if pages <= 0:
        raise Task251Stop("SOURCE_PDF_PAGE_COUNT_NOT_POSITIVE")
    return pages


def _validate_download(result: Mapping[str, Any], item: Mapping[str, Any], *, max_bytes: int) -> dict[str, Any]:
    if result.get("http_status") != 200:
        raise Task251Stop("SOURCE_HTTP_NOT_200")
    expected_url = item["document_url"]
    if result.get("requested_url") != expected_url or result.get("final_url") != expected_url:
        raise Task251Stop("SOURCE_URL_REDIRECT_OR_DRIFT")
    ctype = str(result.get("content_type") or "").split(";", 1)[0].strip().lower()
    if ctype not in {"application/pdf", "application/octet-stream"}:
        raise Task251Stop("SOURCE_CONTENT_TYPE_UNEXPECTED")
    path = Path(str(result.get("path") or ""))
    if not path.is_file():
        raise Task251Stop("SOURCE_FILE_MISSING")
    stat_bytes = path.stat().st_size
    transport_bytes = result.get("bytes")
    if stat_bytes <= 0:
        raise Task251Stop("SOURCE_EMPTY_FILE")
    if stat_bytes > max_bytes:
        raise Task251Stop("SOURCE_BYTE_CAP_EXCEEDED")
    if transport_bytes != stat_bytes:
        raise Task251Stop("SOURCE_TRANSPORT_STAT_MISMATCH")
    with path.open("rb") as source:
        if source.read(5) != b"%PDF-":
            raise Task251Stop("SOURCE_PDF_SIGNATURE_INVALID")
    sha = _sha256_file(path)
    if result.get("sha256") != sha:
        raise Task251Stop("SOURCE_HASH_TRANSPORT_MISMATCH")
    pages = _pdf_pages(path)
    return {
        "edition": item["edition"],
        "publication_date": item["publication_date"],
        "source_id": item["source_id"],
        "logical_key": item["logical_key"],
        "document_url": expected_url,
        "content_type": ctype,
        "bytes": stat_bytes,
        "sha256": sha,
        "pages": pages,
    }


def execute(
    config: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    source: PdfSource,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    try:
        validate_config(config, evidence)
    except Task251Stop as exc:
        return _stop(f"STOP_TASK251_{exc}")

    if offline_test_mode:
        if getattr(source, "network_capable", True):
            return _stop("STOP_TASK251_OFFLINE_NETWORK_CAPABLE_SOURCE")
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return _stop("STOP_TASK251_OFFLINE_SYNTHETIC_AUTH_REQUIRED")
    else:
        if not getattr(source, "network_capable", False):
            return _stop("STOP_TASK251_LIVE_SOURCE_NOT_NETWORK_CAPABLE")
        auth = validate_live_authorization(
            authorization,
            expected_sha=expected_implementation_sha,
            config=config,
        )
        if auth["status"] != "PASS_TASK251_LIVE_AUTHORIZATION":
            return auth

    limits = config["limits"]
    max_bytes = int(limits["max_pdf_bytes_each"])
    aggregate_cap = int(limits["max_aggregate_pdf_bytes"])
    source_gets = 0
    aggregate_bytes = 0
    documents: list[dict[str, Any]] = []

    try:
        with tempfile.TemporaryDirectory(prefix="task251_") as temp_dir:
            root = Path(temp_dir)
            for item in config["targets"]:
                if source_gets >= int(limits["max_source_gets"]):
                    raise Task251Stop("SOURCE_GET_BUDGET_EXCEEDED")
                destination = root / f"jom_{item['edition']}.pdf"
                source_gets += 1
                result = source.fetch(url=item["document_url"], destination=destination, max_bytes=max_bytes)
                validated = _validate_download(result, item, max_bytes=max_bytes)
                aggregate_bytes += int(validated["bytes"])
                if aggregate_bytes > aggregate_cap:
                    raise Task251Stop("SOURCE_AGGREGATE_BYTE_CAP_EXCEEDED")
                documents.append(validated)
            expected_names = [f"jom_{edition}.pdf" for edition in EXPECTED_EDITIONS]
            if sorted(path.name for path in root.glob("*.pdf")) != sorted(expected_names):
                raise Task251Stop("TEMPORARY_PDF_SET_MISMATCH")
    except Task251Stop as exc:
        return _stop(
            f"STOP_TASK251_{exc}",
            source_gets=source_gets,
            documents=documents,
            aggregate_pdf_bytes=aggregate_bytes,
        )

    if source_gets != 2 or len(documents) != 2:
        return _stop(
            "STOP_TASK251_INCOMPLETE_DOCUMENT_SET",
            source_gets=source_gets,
            documents=documents,
            aggregate_pdf_bytes=aggregate_bytes,
        )

    return {
        "status": PASS_STATUS,
        "live_attempt_completed": not offline_test_mode,
        "source_gets": source_gets,
        "document_download_count": 2,
        "documents": documents,
        "aggregate_pdf_bytes": aggregate_bytes,
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
        "canonization_required": True,
        "next_gate": "CANONIZE_TASK251_LIVE_RESULT_BEFORE_CUSTODY_OR_PARSE",
    }


def validate_offline_carrier(
    config_path: str | Path = DEFAULT_CONFIG,
    evidence_path: str | Path = DEFAULT_EVIDENCE,
) -> dict[str, Any]:
    config = load_config(config_path)
    evidence = load_canonical_evidence(evidence_path)
    validation = validate_config(config, evidence)
    return {
        "schema": "TASK251_OFFLINE_CARRIER_VALIDATION_V1",
        "status": "PASS_TASK251_OFFLINE_CARRIER",
        "evidence_status": validate_canonical_evidence(evidence)["status"],
        "config_status": validation["status"],
        "target_editions": [row["edition"] for row in config["targets"]],
        "max_source_gets": config["limits"]["max_source_gets"],
        "max_pdf_bytes_each": config["limits"]["max_pdf_bytes_each"],
        "max_aggregate_pdf_bytes": config["limits"]["max_aggregate_pdf_bytes"],
        "live_authorized": False,
        "network_performed": False,
        "drive_write": False,
        "serving_write": False,
        "publication": False,
        "schedule": False,
        "recurrence": False,
    }
