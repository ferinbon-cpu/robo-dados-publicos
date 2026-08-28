"""Fail-closed TASK 009C probe for the resolved same-origin SIOPE 2025 metadata ZIP path."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

PREP_SCHEMA = "SIOPE_2025_METADATA_RESOLVED_PATH_PROBE_PREPARATION_V1"
AUTH_SCHEMA = "SIOPE_2025_METADATA_RESOLVED_PATH_PROBE_AUTHORIZATION_V1"
AUTH_PATH = "config/siope_2025_metadata_resolved_path_probe_authorization.v1.json"
MAIN_REF = "refs/heads/main"
ERROR = "STOP_SIOPE_2025_METADATA_RESOLVED_PATH_PROBE"
RESOLVED_URL = "https://fnde.sharepoint.com/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip"
HOST = "fnde.sharepoint.com"
RANGE_HEADER = "bytes=0-4095"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_AUTH_ID = re.compile(r"^SIOPE2025-METADATA-DIRECT-PROBE-[A-Z0-9_-]{4,64}$")
_CONTENT_RANGE = re.compile(r"^bytes\s+(\d+)-(\d+)/(\d+|\*)$", re.IGNORECASE)
_ALLOWED_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


class MetadataResolvedPathProbeError(RuntimeError):
    def __init__(self, message: str, *, request_count: int = 0):
        super().__init__(message)
        self.request_count = request_count


def _stop(condition: bool, code: str, *, request_count: int = 0) -> None:
    if not condition:
        raise MetadataResolvedPathProbeError(f"{ERROR}_{code}", request_count=request_count)


def _parse_utc(value: object, code: str) -> datetime:
    _stop(isinstance(value, str) and value.endswith("Z"), code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except (TypeError, ValueError):
        raise MetadataResolvedPathProbeError(f"{ERROR}_{code}") from None
    return parsed.astimezone(timezone.utc)


def _source_identity() -> dict:
    return {
        "provider": "FNDE",
        "year": 2025,
        "scope": "MUNICIPAL_METADATA_RESOLVED_PATH",
        "host": HOST,
        "resolved_package_url": RESOLVED_URL,
    }


def _request_contract() -> dict:
    return {
        "method": "GET",
        "range_header": RANGE_HEADER,
        "maximum_source_get_count": 1,
        "maximum_response_bytes": 4096,
        "timeout_seconds": 60,
        "max_attempts": 1,
        "retry_authorized": False,
        "follow_redirects": False,
        "allowed_redirect_hosts": [],
    }


def validate_preparation_contract(preparation: dict, authorization_template: dict, automation_policy: dict) -> None:
    _stop(preparation.get("schema") == PREP_SCHEMA, "PREPARATION_SCHEMA")
    _stop(preparation.get("task") == "TASK_009C", "PREPARATION_TASK")
    _stop(preparation.get("task_phase") == "OFFLINE_PREPARATION_ONLY", "PREPARATION_PHASE")
    _stop(preparation.get("current_task_execution_tier") == "T0_OFFLINE", "PREPARATION_TIER")
    _stop(preparation.get("tier_design_target") == "T1_REMOTE_READONLY", "TARGET_TIER")
    _stop(preparation.get("live_execution_authorized_by_task_009c") is False, "LIVE_AUTH")
    _stop(preparation.get("source_get_authorized_by_task_009c") is False, "SOURCE_AUTH")
    _stop(preparation.get("future_batch_execution_authorized") is False, "BATCH")

    basis = preparation.get("evidence_basis", {})
    _stop(basis.get("observed_http_status") == 302, "EVIDENCE_HTTP")
    _stop(
        basis.get("observed_relative_location")
        == "/sites/SIOPE/Documentos%20Compartilhados/Metadados_Mun_2025.zip",
        "EVIDENCE_LOCATION",
    )
    _stop(basis.get("resolution_kind") == "OFFLINE_RELATIVE_URI_RESOLUTION_ONLY", "EVIDENCE_RESOLUTION")

    _stop(preparation.get("source_identity") == _source_identity(), "SOURCE_IDENTITY")
    auth = preparation.get("authorization", {})
    _stop(auth.get("fixed_artifact_path") == AUTH_PATH, "AUTH_PATH")
    _stop(auth.get("artifact_must_be_absent_in_task_009c") is True, "AUTH_ABSENT")
    _stop(auth.get("one_shot_required") is True and auth.get("max_live_runs") == 1, "ONE_SHOT")

    probe = preparation.get("probe_contract", {})
    _stop(probe.get("method") == "GET", "METHOD")
    _stop(probe.get("range_header") == RANGE_HEADER, "RANGE")
    _stop(probe.get("maximum_source_get_count") == 1, "GET_COUNT")
    _stop(probe.get("maximum_response_bytes") == 4096, "RESPONSE_LIMIT")
    _stop(probe.get("timeout_seconds") == 60 and probe.get("max_attempts") == 1, "TIMEOUT_ATTEMPTS")
    _stop(probe.get("retry_authorized") is False and probe.get("follow_redirects") is False, "RETRY_REDIRECT")
    _stop(probe.get("allowed_redirect_hosts") == [], "REDIRECT_HOSTS")
    _stop(probe.get("persist_raw_body") is False and probe.get("emit_raw_body") is False, "RAW_BODY")

    effects = preparation.get("effects_task_009c", {})
    _stop(
        effects
        == {
            "source_get_count": 0,
            "operational_receipt_status_query_count": 0,
            "siope_fiscal_odata_get_count": 0,
            "drive_read_count": 0,
            "drive_write_count": 0,
            "response_persistence": False,
            "archive_persistence": False,
            "bronze_silver_gold_creation": False,
            "publication": False,
        },
        "PREPARATION_EFFECTS",
    )

    guards = preparation.get("semantic_guards", {})
    _stop(guards.get("annual_closure_status") == "UNKNOWN", "CLOSURE")
    _stop(guards.get("semantic_comparability_status") == "UNKNOWN", "COMPARABILITY")
    _stop(guards.get("gold_metrics_status") == "UNKNOWN", "GOLD")
    _stop(guards.get("closed_annual_series_last_year") == 2024, "SERIES")
    _stop(guards.get("include_2026_authorized") is False, "YEAR_2026")

    _stop(authorization_template.get("schema") == AUTH_SCHEMA, "AUTH_TEMPLATE_SCHEMA")
    _stop(authorization_template.get("authorized") is False, "AUTH_TEMPLATE_MUST_BLOCK")
    _stop(authorization_template.get("source_identity") == _source_identity(), "AUTH_TEMPLATE_SOURCE")
    _stop(authorization_template.get("request_contract") == _request_contract(), "AUTH_TEMPLATE_REQUEST")
    _stop(authorization_template.get("one_shot") is True and authorization_template.get("max_live_runs") == 1, "AUTH_TEMPLATE_ONE_SHOT")

    _stop(automation_policy.get("default_decision") == "BLOCK", "POLICY_DEFAULT")
    invariants = automation_policy.get("policy_invariants", {})
    _stop(invariants.get("agent_may_authorize_remote_execution") is False, "POLICY_AGENT_AUTH")
    _stop(invariants.get("future_batch_execution_authorized") is False, "POLICY_BATCH")


def validate_authorization_document(
    authorization: dict | None,
    *,
    requested_authorization_id: str,
    current_head_sha: str,
    current_parent_sha: str,
    changed_paths_since_base: list[str],
    current_workflow_run_number: int,
    current_workflow_run_attempt: int,
    current_workflow_ref: str,
    now_utc: datetime | None = None,
) -> None:
    _stop(bool(authorization), "LIVE_NOT_AUTHORIZED")
    assert authorization is not None
    _stop(authorization.get("schema") == AUTH_SCHEMA, "AUTH_SCHEMA")
    _stop(authorization.get("authorized") is True, "LIVE_NOT_AUTHORIZED")
    auth_id = authorization.get("authorization_id")
    _stop(isinstance(auth_id, str) and _AUTH_ID.fullmatch(auth_id) is not None, "AUTH_ID")
    _stop(auth_id == requested_authorization_id, "AUTH_ID_MISMATCH")
    _stop(authorization.get("approval_kind") == "OWNER_EXPLICIT_SINGLE_BOUNDED_RUN", "APPROVAL_KIND")
    _stop(authorization.get("approved_by") == "ferinbon-cpu", "APPROVED_BY")
    _stop(authorization.get("one_shot") is True and authorization.get("max_live_runs") == 1, "ONE_SHOT")
    _stop(authorization.get("authorized_workflow_run_number") == current_workflow_run_number, "RUN_NUMBER_MISMATCH")
    _stop(authorization.get("authorized_workflow_run_attempt") == 1 and current_workflow_run_attempt == 1, "RERUN_BLOCKED")
    _stop(authorization.get("authorized_workflow_ref") == MAIN_REF and current_workflow_ref == MAIN_REF, "REF_MISMATCH")

    base = authorization.get("authorized_base_sha")
    _stop(isinstance(base, str) and _SHA40.fullmatch(base) is not None, "BASE_SHA")
    _stop(isinstance(current_head_sha, str) and _SHA40.fullmatch(current_head_sha) is not None, "HEAD_SHA")
    _stop(isinstance(current_parent_sha, str) and _SHA40.fullmatch(current_parent_sha) is not None, "PARENT_SHA")
    _stop(current_parent_sha == base, "PARENT_NOT_AUTHORIZED_BASE")
    _stop(current_head_sha != base, "AUTHORIZATION_COMMIT_REQUIRED")
    _stop(changed_paths_since_base == [AUTH_PATH], "AUTHORIZATION_ONLY_DIFF")
    _stop(authorization.get("source_identity") == _source_identity(), "AUTH_SOURCE")
    _stop(authorization.get("request_contract") == _request_contract(), "AUTH_REQUEST")
    _stop(
        authorization.get("effects")
        == {
            "operational_receipt_status_query_count": 0,
            "siope_fiscal_odata_get_count": 0,
            "drive_read_count": 0,
            "drive_write_count": 0,
            "response_persistence": False,
            "archive_persistence": False,
            "bronze_silver_gold_creation": False,
            "publication": False,
            "future_batch_execution_authorized": False,
        },
        "AUTH_EFFECTS",
    )
    _stop(
        authorization.get("semantic_guards")
        == {
            "annual_closure_status": "UNKNOWN",
            "semantic_comparability_status": "UNKNOWN",
            "gold_metrics_status": "UNKNOWN",
            "closed_annual_series_last_year": 2024,
            "include_2026_authorized": False,
        },
        "AUTH_GUARDS",
    )
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    approved = _parse_utc(authorization.get("approved_at_utc"), "APPROVED_AT")
    expires = _parse_utc(authorization.get("expires_at_utc"), "EXPIRES_AT")
    _stop(approved <= now < expires, "AUTH_TIME_WINDOW")
    _stop(expires > approved, "AUTH_TIME_ORDER")


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _default_open(req: Request, timeout: int):
    return build_opener(_NoRedirectHandler()).open(req, timeout=timeout)


def _header_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(str(value).strip())
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _content_range_total(value: object) -> int | None:
    if not value:
        return None
    match = _CONTENT_RANGE.fullmatch(str(value).strip())
    if not match or match.group(3) == "*":
        return None
    return int(match.group(3))


def _sanitize_location(value: object) -> tuple[str | None, str | None, str | None]:
    if not value:
        return None, None, None
    parsed = urlparse(str(value))
    return parsed.scheme or None, parsed.hostname.lower() if parsed.hostname else None, parsed.path or None


@dataclass(frozen=True)
class ResolvedPathObservation:
    result_kind: str
    request_count: int
    http_status: int
    content_type: str | None
    response_byte_count: int
    content_length_header: int | None
    content_range_total: int | None
    zip_magic_present: bool
    sample_sha256: str | None
    redirect_scheme: str | None = None
    redirect_host: str | None = None
    redirect_path: str | None = None

    def sanitized(self) -> dict:
        return {
            "result_kind": self.result_kind,
            "source_get_count": self.request_count,
            "http_status": self.http_status,
            "content_type": self.content_type,
            "response_byte_count": self.response_byte_count,
            "content_length_header": self.content_length_header,
            "content_range_total": self.content_range_total,
            "zip_magic_present": self.zip_magic_present,
            "sample_sha256": self.sample_sha256,
            "redirect_scheme": self.redirect_scheme,
            "redirect_host": self.redirect_host,
            "redirect_path": self.redirect_path,
            "raw_body_persisted": False,
            "archive_persisted": False,
        }


class MetadataResolvedPathProbe:
    def __init__(self, opener: Callable[[Request, int], object] | None = None):
        self._opener = opener or _default_open

    def run(self, *, url: str = RESOLVED_URL, timeout_seconds: int = 60, max_response_bytes: int = 4096) -> ResolvedPathObservation:
        parsed = urlparse(url)
        _stop(url == RESOLVED_URL, "URL_DRIFT")
        _stop(parsed.scheme == "https" and parsed.hostname == HOST, "HOST_DRIFT")
        _stop(timeout_seconds == 60, "TIMEOUT_DRIFT")
        _stop(max_response_bytes == 4096, "RESPONSE_LIMIT_DRIFT")
        req = Request(
            url,
            headers={
                "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 (+public-transparency-research)",
                "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
                "Range": RANGE_HEADER,
                "Cache-Control": "no-cache",
            },
            method="GET",
        )
        try:
            response = self._opener(req, timeout_seconds)
            with response:
                final_url = str(getattr(response, "url", None) or response.geturl())
                _stop(final_url == url, "REDIRECT_OR_URL_DRIFT", request_count=1)
                status = int(getattr(response, "status", None) or response.getcode())
                content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower() or None
                content_length = _header_int(response.headers.get("Content-Length"))
                total = _content_range_total(response.headers.get("Content-Range"))
                _stop(status in {200, 206}, "HTTP_STATUS", request_count=1)
                _stop(content_type in _ALLOWED_CONTENT_TYPES, "CONTENT_TYPE", request_count=1)
                if status == 200 and content_length is not None:
                    _stop(content_length <= max_response_bytes, "RANGE_IGNORED_LARGE_200", request_count=1)
                body = response.read(max_response_bytes + 1)
                _stop(len(body) <= max_response_bytes, "RESPONSE_TOO_LARGE", request_count=1)
                return ResolvedPathObservation(
                    result_kind="DIRECT_BOUNDED_RESPONSE",
                    request_count=1,
                    http_status=status,
                    content_type=content_type,
                    response_byte_count=len(body),
                    content_length_header=content_length,
                    content_range_total=total,
                    zip_magic_present=body.startswith(b"PK\x03\x04"),
                    sample_sha256=hashlib.sha256(body).hexdigest() if body else hashlib.sha256(b"").hexdigest(),
                )
        except HTTPError as exc:
            if exc.code in {301, 302, 303, 307, 308}:
                scheme, host, path = _sanitize_location(exc.headers.get("Location"))
                return ResolvedPathObservation(
                    result_kind="REDIRECT_STOP_REQUIRES_NEW_AUTHORIZATION",
                    request_count=1,
                    http_status=int(exc.code),
                    content_type=None,
                    response_byte_count=0,
                    content_length_header=_header_int(exc.headers.get("Content-Length")),
                    content_range_total=None,
                    zip_magic_present=False,
                    sample_sha256=None,
                    redirect_scheme=scheme,
                    redirect_host=host,
                    redirect_path=path,
                )
            raise MetadataResolvedPathProbeError(f"{ERROR}_HTTP_{exc.code}", request_count=1) from None
        except (URLError, TimeoutError) as exc:
            raise MetadataResolvedPathProbeError(f"{ERROR}_TRANSPORT_{type(exc).__name__}", request_count=1) from None
