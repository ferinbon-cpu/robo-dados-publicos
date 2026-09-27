"""Fail-closed preparation, authorization, and bounded route probe for the official SIOPE 2025 metadata package."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
import socket
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

PREP_SCHEMA = "SIOPE_2025_METADATA_PACKAGE_ROUTE_PROBE_PREPARATION_V1"
AUTH_SCHEMA = "SIOPE_2025_METADATA_PACKAGE_ROUTE_PROBE_AUTHORIZATION_V1"
AUTH_PATH = "config/siope_2025_metadata_package_route_probe_authorization.v1.json"
MAIN_REF = "refs/heads/main"
ERROR = "STOP_SIOPE_2025_METADATA_PACKAGE_ROUTE_PROBE"
PACKAGE_URL = "https://fnde.sharepoint.com/:u:/s/SIOPE/EeP0ArdsxWJLuWyg3LQHt2IBKEWEhLDvDk2_7k1vbAx0tQ?download=1&e=UiD081"
INITIAL_HOST = "fnde.sharepoint.com"
RANGE_HEADER = "bytes=0-4095"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_AUTH_ID = re.compile(r"^SIOPE2025-METADATA-PROBE-[A-Z0-9_-]{4,64}$")
_CONTENT_RANGE = re.compile(r"^bytes\s+(\d+)-(\d+)/(\d+|\*)$", re.IGNORECASE)
_ALLOWED_PACKAGE_CONTENT_TYPES = {
    "application/zip",
    "application/x-zip",
    "application/x-zip-compressed",
    "application/octet-stream",
}


class MetadataPackageProbeError(RuntimeError):
    def __init__(self, message: str, *, request_count: int = 0):
        super().__init__(message)
        self.request_count = request_count


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise MetadataPackageProbeError(f"{ERROR}_{code}")


def _parse_utc(value: object, code: str) -> datetime:
    _stop(isinstance(value, str) and value.endswith("Z"), code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except (TypeError, ValueError):
        raise MetadataPackageProbeError(f"{ERROR}_{code}") from None
    return parsed.astimezone(timezone.utc)


def _expected_source_identity() -> dict:
    return {
        "provider": "FNDE",
        "year": 2025,
        "scope": "MUNICIPAL_METADATA",
        "initial_host": INITIAL_HOST,
        "package_url": PACKAGE_URL,
    }


def _expected_request_contract() -> dict:
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
    _stop(preparation.get("task") == "TASK_009A", "PREPARATION_TASK")
    _stop(preparation.get("task_phase") == "OFFLINE_PREPARATION_ONLY", "PREPARATION_PHASE")
    _stop(preparation.get("current_task_execution_tier") == "T0_OFFLINE", "PREPARATION_TIER")
    _stop(preparation.get("tier_design_target") == "T1_REMOTE_READONLY", "TARGET_TIER")
    _stop(preparation.get("live_execution_authorized_by_task_009a") is False, "LIVE_AUTH")
    _stop(preparation.get("source_get_authorized_by_task_009a") is False, "SOURCE_AUTH")
    _stop(preparation.get("future_batch_execution_authorized") is False, "BATCH")

    source = preparation.get("source_identity", {})
    _stop(source.get("provider") == "FNDE", "SOURCE_PROVIDER")
    _stop(source.get("year") == 2025 and source.get("scope") == "MUNICIPAL_METADATA", "SOURCE_SCOPE")
    _stop(source.get("initial_host") == INITIAL_HOST and source.get("package_url") == PACKAGE_URL, "SOURCE_IDENTITY")
    _stop(source.get("official_index_url") == "https://www.gov.br/fnde/pt-br/assuntos/sistemas/siope/downloads", "SOURCE_INDEX")

    auth = preparation.get("authorization", {})
    _stop(auth.get("fixed_artifact_path") == AUTH_PATH, "AUTH_PATH")
    _stop(auth.get("artifact_must_be_absent_in_task_009a") is True, "AUTH_ABSENT")
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
    _stop(probe.get("purpose") == "ROUTE_REDIRECT_SIZE_AND_ZIP_MAGIC_DISCOVERY_ONLY", "PURPOSE")

    effects = preparation.get("effects_task_009a", {})
    _stop(effects == {
        "source_get_count": 0,
        "operational_receipt_status_query_count": 0,
        "siope_fiscal_odata_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "response_persistence": False,
        "archive_persistence": False,
        "bronze_silver_gold_creation": False,
        "publication": False,
    }, "PREPARATION_EFFECTS")

    guards = preparation.get("semantic_guards", {})
    _stop(guards.get("annual_closure_status") == "UNKNOWN", "CLOSURE")
    _stop(guards.get("semantic_comparability_status") == "UNKNOWN", "COMPARABILITY")
    _stop(guards.get("gold_metrics_status") == "UNKNOWN", "GOLD")
    _stop(guards.get("closed_annual_series_last_year") == 2024, "SERIES")
    _stop(guards.get("include_2026_authorized") is False, "YEAR_2026")
    _stop(guards.get("compliance_claims_authorized") is False, "COMPLIANCE")

    _stop(authorization_template.get("schema") == AUTH_SCHEMA, "AUTH_TEMPLATE_SCHEMA")
    _stop(authorization_template.get("authorized") is False, "AUTH_TEMPLATE_MUST_BLOCK")
    _stop(authorization_template.get("source_identity") == _expected_source_identity(), "AUTH_TEMPLATE_SOURCE")
    _stop(authorization_template.get("request_contract") == _expected_request_contract(), "AUTH_TEMPLATE_REQUEST")
    _stop(authorization_template.get("one_shot") is True and authorization_template.get("max_live_runs") == 1, "AUTH_TEMPLATE_ONE_SHOT")

    _stop(automation_policy.get("default_decision") == "BLOCK", "POLICY_DEFAULT")
    invariants = automation_policy.get("policy_invariants", {})
    _stop(invariants.get("agent_may_authorize_remote_execution") is False, "POLICY_AGENT_AUTH")
    _stop(invariants.get("future_batch_execution_authorized") is False, "POLICY_BATCH")
    t1 = automation_policy.get("tiers", {}).get("T1_REMOTE_READONLY", {})
    _stop(t1.get("human_confirmation_required") == "UNTIL_LIVE_PROOF_AND_TRUST_BOUNDARY_PASS", "POLICY_HUMAN_CONFIRMATION")


def validate_authorization_document(
    authorization: dict | None,
    preparation: dict,
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

    run_number = authorization.get("authorized_workflow_run_number")
    _stop(isinstance(run_number, int) and run_number >= 1, "RUN_NUMBER")
    _stop(current_workflow_run_number == run_number, "RUN_NUMBER_MISMATCH")
    _stop(authorization.get("authorized_workflow_run_attempt") == 1 and current_workflow_run_attempt == 1, "RERUN_BLOCKED")
    _stop(authorization.get("authorized_workflow_ref") == MAIN_REF and current_workflow_ref == MAIN_REF, "REF_MISMATCH")

    base = authorization.get("authorized_base_sha")
    _stop(isinstance(base, str) and _SHA40.fullmatch(base) is not None, "BASE_SHA")
    _stop(isinstance(current_head_sha, str) and _SHA40.fullmatch(current_head_sha) is not None, "HEAD_SHA")
    _stop(isinstance(current_parent_sha, str) and _SHA40.fullmatch(current_parent_sha) is not None, "PARENT_SHA")
    _stop(current_parent_sha == base, "PARENT_NOT_AUTHORIZED_BASE")
    _stop(current_head_sha != base, "AUTHORIZATION_COMMIT_REQUIRED")
    _stop(changed_paths_since_base == [AUTH_PATH], "AUTHORIZATION_ONLY_DIFF")

    _stop(authorization.get("source_identity") == _expected_source_identity(), "AUTH_SOURCE")
    _stop(authorization.get("request_contract") == _expected_request_contract(), "AUTH_REQUEST")
    _stop(authorization.get("effects") == {
        "operational_receipt_status_query_count": 0,
        "siope_fiscal_odata_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "response_persistence": False,
        "archive_persistence": False,
        "bronze_silver_gold_creation": False,
        "publication": False,
        "future_batch_execution_authorized": False,
    }, "AUTH_EFFECTS")
    _stop(authorization.get("semantic_guards") == {
        "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN",
        "gold_metrics_status": "UNKNOWN",
        "closed_annual_series_last_year": 2024,
        "include_2026_authorized": False,
    }, "AUTH_GUARDS")

    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    approved = _parse_utc(authorization.get("approved_at_utc"), "APPROVED_AT")
    expires = _parse_utc(authorization.get("expires_at_utc"), "EXPIRES_AT")
    _stop(approved <= now < expires, "AUTH_TIME_WINDOW")
    _stop(expires > approved, "AUTH_TIME_ORDER")
    _stop(preparation.get("probe_contract", {}).get("maximum_source_get_count") == 1, "PREPARATION_GET_COUNT")


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
class RouteProbeObservation:
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


class MetadataPackageRouteProbe:
    def __init__(self, opener: Callable[[Request, int], object] | None = None):
        self._opener = opener or _default_open

    def run(self, *, url: str = PACKAGE_URL, timeout_seconds: int = 60, max_response_bytes: int = 4096) -> RouteProbeObservation:
        parsed = urlparse(url)
        _stop(url == PACKAGE_URL, "URL_DRIFT")
        _stop(parsed.scheme == "https" and parsed.hostname == INITIAL_HOST, "HOST_DRIFT")
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
                _stop(final_url == url, "REDIRECT_OR_URL_DRIFT")
                status = int(getattr(response, "status", None) or response.getcode())
                content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower() or None
                content_length = _header_int(response.headers.get("Content-Length"))
                content_range_total = _content_range_total(response.headers.get("Content-Range"))
                _stop(status in {200, 206}, "HTTP_STATUS")
                _stop(content_type in _ALLOWED_PACKAGE_CONTENT_TYPES, "CONTENT_TYPE")
                if status == 200 and content_length is not None and content_length > max_response_bytes:
                    raise MetadataPackageProbeError(f"{ERROR}_RANGE_IGNORED_RESPONSE_TOO_LARGE", request_count=1)
                raw = response.read(max_response_bytes + 1)
        except MetadataPackageProbeError:
            raise
        except HTTPError as exc:
            code = int(getattr(exc, "code", 0) or 0)
            if 300 <= code < 400:
                location = exc.headers.get("Location") if exc.headers else None
                scheme, host, path = _sanitize_location(location)
                return RouteProbeObservation(
                    result_kind="REDIRECT_STOP_REQUIRES_NEW_AUTHORIZATION",
                    request_count=1,
                    http_status=code,
                    content_type=None,
                    response_byte_count=0,
                    content_length_header=_header_int(exc.headers.get("Content-Length") if exc.headers else None),
                    content_range_total=None,
                    zip_magic_present=False,
                    sample_sha256=None,
                    redirect_scheme=scheme,
                    redirect_host=host,
                    redirect_path=path,
                )
            raise MetadataPackageProbeError(f"{ERROR}_HTTP_{code}", request_count=1) from None
        except (TimeoutError, socket.timeout):
            raise MetadataPackageProbeError(f"{ERROR}_TIMEOUT", request_count=1) from None
        except URLError as exc:
            reason = getattr(exc, "reason", None)
            code = "TIMEOUT" if isinstance(reason, (TimeoutError, socket.timeout)) else "NETWORK"
            raise MetadataPackageProbeError(f"{ERROR}_{code}", request_count=1) from None
        except OSError:
            raise MetadataPackageProbeError(f"{ERROR}_NETWORK", request_count=1) from None

        if len(raw) > max_response_bytes:
            raise MetadataPackageProbeError(f"{ERROR}_RESPONSE_TOO_LARGE", request_count=1)
        zip_magic = raw.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))
        return RouteProbeObservation(
            result_kind="DIRECT_BOUNDED_RESPONSE",
            request_count=1,
            http_status=status,
            content_type=content_type,
            response_byte_count=len(raw),
            content_length_header=content_length,
            content_range_total=content_range_total,
            zip_magic_present=zip_magic,
            sample_sha256=hashlib.sha256(raw).hexdigest(),
        )
