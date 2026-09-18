from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task255_task254_redirect_location_probe.v1.json"
DEFAULT_EVIDENCE = ROOT / "docs/evidence/TASK_255_TASK254_REDIRECT_INCIDENT_CANONICAL_0.8.0.json"
EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class Task255Stop(RuntimeError):
    pass


class ProbeTransport(Protocol):
    def get(self, url: str, *, timeout: int, max_body_bytes: int) -> dict[str, Any]:
        ...


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task255Stop(code)


def load_config(path: Path | str = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg.get("schema") == "TASK255_TASK254_REDIRECT_LOCATION_PROBE_V1", "TASK255_CONFIG_SCHEMA")
    _stop(cfg.get("task") == "TASK_255", "TASK255_CONFIG_TASK")
    _stop(cfg.get("issue") == 843, "TASK255_CONFIG_ISSUE")
    _stop(cfg.get("base_main_sha") == "5dbb0a3a8dc68cc286a1b6933dfbea94e7cab9d2", "TASK255_BASE_MAIN")
    _stop(cfg.get("mode") == "T1_READONLY_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION", "TASK255_MODE")

    t254 = cfg.get("source_task254") or {}
    _stop(t254.get("run_id") == 35296079277, "TASK255_RUN")
    _stop(t254.get("job_id") == 105448761103, "TASK255_JOB")
    _stop(t254.get("artifact_id") == 10527683320, "TASK255_ARTIFACT")
    _stop(t254.get("artifact_zip_sha256") == "3238e7eb162833d821f8116c36460278584f18f2fb3afa31c5c92b78393344fc", "TASK255_ARTIFACT_SHA")
    _stop(t254.get("result_sha256") == "d408b5c4d98b40d3c7e6b9d90c94c2180b6f31bea56c7502190189beda645e0c", "TASK255_RESULT_SHA")
    _stop(t254.get("status") == "STOP_TASK254_FAIL_CLOSED", "TASK255_TASK254_STATUS")
    _stop(t254.get("stop_code") == "TASK254_REDIRECT_STATUS_OBSERVED", "TASK255_TASK254_STOP")
    _stop(t254.get("source_get_count") == 1, "TASK255_TASK254_GETS")
    _stop(t254.get("remaining_targets_not_requested") == 7, "TASK255_TASK254_REMAINING")
    _stop(t254.get("raw_payload_persisted") is False, "TASK255_TASK254_RAW")
    _stop(t254.get("drive_write_count") == 0, "TASK255_TASK254_DRIVE")
    _stop(t254.get("absence_inference_allowed") is False, "TASK255_TASK254_ABSENCE")

    probe = cfg.get("probe") or {}
    _stop(probe.get("control") == "45132495000140-1-000646/2026", "TASK255_CONTROL")
    _stop(probe.get("requested_url") == "https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/646", "TASK255_URL")
    _stop(probe.get("method") == "GET", "TASK255_METHOD")
    _stop(probe.get("max_remote_get_count") == 1, "TASK255_GET_BUDGET")
    _stop(probe.get("retry") is False, "TASK255_RETRY")
    _stop(probe.get("follow_redirects") is False, "TASK255_REDIRECT_FOLLOW")
    _stop(probe.get("alternate_url_discovery") is False, "TASK255_ALT_DISCOVERY")
    _stop(probe.get("require_absolute_https_location_on_3xx") is True, "TASK255_LOCATION_REQUIREMENT")
    _stop(probe.get("infer_remaining_target_urls") is False, "TASK255_REMAINING_INFERENCE")

    auth = cfg.get("authorization") or {}
    _stop(auth.get("required_task") == "TASK_255_LIVE_AUTHORIZATION", "TASK255_AUTH_TASK")
    _stop(auth.get("required_operation") == "EXACT_1_TASK254_FIRST_TARGET_NOFOLLOW_REDIRECT_LOCATION_PROBE", "TASK255_AUTH_OPERATION")
    _stop(auth.get("attempt_count") == 1, "TASK255_AUTH_ATTEMPT")
    for key, value in auth.items():
        if key.endswith("_authorized_by_default") or key.endswith("_reuse_allowed"):
            _stop(value is False, "TASK255_AUTH_DEFAULT_" + key.upper())

    _stop(all(v is False for v in (cfg.get("effects") or {}).values()), "TASK255_EFFECTS")
    _stop(cfg.get("next_gate") == "OWNER_AUTHORIZED_SINGLE_NOFOLLOW_PNCP_REDIRECT_LOCATION_PROBE_ON_MERGED_TASK255_SHA", "TASK255_NEXT_GATE")
    return cfg


def load_evidence(path: Path | str = DEFAULT_EVIDENCE) -> dict[str, Any]:
    ev = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(ev.get("schema") == "TASK255_TASK254_REDIRECT_INCIDENT_CANONICAL_V1", "TASK255_EVIDENCE_SCHEMA")
    _stop(ev.get("status") == "CANONICAL_TASK254_REDIRECT_STOP_WITH_SINGLE_GET_AND_NO_ABSENCE_INFERENCE", "TASK255_EVIDENCE_STATUS")
    t254 = ev.get("task254") or {}
    _stop(t254.get("run_id") == 35296079277, "TASK255_EVIDENCE_RUN")
    _stop(t254.get("source_get_count") == 1, "TASK255_EVIDENCE_GETS")
    _stop(t254.get("stop_code") == "TASK254_REDIRECT_STATUS_OBSERVED", "TASK255_EVIDENCE_STOP")
    _stop(t254.get("authorization_consumed") is True, "TASK255_EVIDENCE_AUTH_CONSUMED")
    _stop(len(ev.get("untouched_targets") or []) == 7, "TASK255_EVIDENCE_UNTOUCHED")
    adjudication = ev.get("epistemic_adjudication") or {}
    _stop(adjudication.get("redirect_condition_proven") is True, "TASK255_EVIDENCE_REDIRECT")
    _stop(adjudication.get("redirect_destination_proven") is False, "TASK255_EVIDENCE_DESTINATION")
    _stop(adjudication.get("remaining_seven_redirect_behavior_proven") is False, "TASK255_EVIDENCE_REMAINING")
    _stop(adjudication.get("pncp_records_absent") is False, "TASK255_EVIDENCE_ABSENCE")
    return ev


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LiveNoFollowTransport:
    def get(self, url: str, *, timeout: int, max_body_bytes: int) -> dict[str, Any]:
        opener = urllib.request.build_opener(NoRedirect)
        req = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": "robo-dados-publicos-task255/0.8.0",
            },
        )
        raw = b""
        status = None
        content_type = None
        location = None
        transport_error = None
        try:
            with opener.open(req, timeout=timeout) as response:
                status = int(response.status)
                content_type = response.headers.get("Content-Type")
                location = response.headers.get("Location")
                raw = response.read(max_body_bytes + 1)
                if len(raw) > max_body_bytes:
                    raise Task255Stop("TASK255_BODY_TOO_LARGE")
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            content_type = exc.headers.get("Content-Type") if exc.headers else None
            location = exc.headers.get("Location") if exc.headers else None
            try:
                raw = exc.read(max_body_bytes + 1)
            except Exception:
                raw = b""
            if len(raw) > max_body_bytes:
                raise Task255Stop("TASK255_BODY_TOO_LARGE")
            transport_error = f"HTTP_ERROR_{exc.code}"
        except urllib.error.URLError as exc:
            transport_error = f"URL_ERROR:{type(exc.reason).__name__}"
        except Task255Stop:
            raise
        except Exception as exc:
            transport_error = f"TRANSPORT_ERROR:{type(exc).__name__}:{str(exc)[:160]}"

        return {
            "requested_url": url,
            "http_status": status,
            "location": location,
            "content_type": content_type,
            "bytes_received": len(raw),
            "body_sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "transport_error": transport_error,
            "remote_get_count": 1,
        }


def _valid_absolute_https_location(location: str) -> bool:
    parsed = urlparse(location)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if not authorization:
        return {"status": "STOP_TASK255_LIVE_NOT_AUTHORIZED"}
    if authorization.get("prior_authorization_reused") is True:
        return {"status": "STOP_TASK255_PRIOR_AUTHORIZATION_REUSE"}
    if not HEX40_RE.fullmatch(expected_implementation_sha or ""):
        return {"status": "STOP_TASK255_IMPLEMENTATION_SHA_FORMAT"}

    probe = config["probe"]
    required = {
        "task": "TASK_255_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "implementation_branch": "main",
        "runtime_branch": config["runtime"]["branch"],
        "implementation_sha": expected_implementation_sha,
        "operation": "EXACT_1_TASK254_FIRST_TARGET_NOFOLLOW_REDIRECT_LOCATION_PROBE",
        "control": probe["control"],
        "requested_url": probe["requested_url"],
        "max_remote_get_count": 1,
        "attempt_count": 1,
        "owner_authorized": True,
        "source_network_authorized": True,
        "follow_redirects": False,
        "automatic_retry": False,
        "alternate_url_discovery": False,
        "prior_authorization_reused": False,
        "drive_write_authorized": False,
        "publication_authorized": False,
        "serving_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
        "consumed": False,
    }
    if any(authorization.get(k) != v for k, v in required.items()):
        return {"status": "STOP_TASK255_AUTHORIZATION_CONTRACT_MISMATCH"}
    return {"status": "PASS_TASK255_LIVE_AUTHORIZATION"}


def execute_probe(
    config: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    transport: ProbeTransport,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    _stop(evidence.get("schema") == "TASK255_TASK254_REDIRECT_INCIDENT_CANONICAL_V1", "TASK255_EXEC_EVIDENCE")
    if not offline_test_mode:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
            config=config,
        )
        if auth["status"] != "PASS_TASK255_LIVE_AUTHORIZATION":
            return {
                "schema": "TASK255_PNCP_REDIRECT_LOCATION_PROBE_RESULT_V1",
                "status": auth["status"],
                "source_get_count": 0,
                "raw_payload_persisted": False,
                "absence_inference_allowed": False,
            }

    probe = config["probe"]
    meta = transport.get(
        probe["requested_url"],
        timeout=int(probe["timeout_seconds"]),
        max_body_bytes=int(probe["max_body_bytes"]),
    )
    _stop(meta.get("remote_get_count") == 1, "TASK255_REMOTE_GET_COUNT")
    _stop(meta.get("requested_url") == probe["requested_url"], "TASK255_REQUEST_URL_DRIFT")
    status = meta.get("http_status")
    location = meta.get("location")
    outcome = "NON_REDIRECT_STATUS_OBSERVED"

    if isinstance(status, int) and 300 <= status < 400:
        _stop(isinstance(location, str) and bool(location.strip()), "TASK255_REDIRECT_LOCATION_MISSING")
        _stop(_valid_absolute_https_location(location.strip()), "TASK255_REDIRECT_LOCATION_NOT_ABSOLUTE_HTTPS")
        outcome = "REDIRECT_LOCATION_CAPTURED"
    elif status == 200:
        outcome = "HTTP_200_NO_REDIRECT_CURRENTLY_OBSERVED"
    elif status is None:
        outcome = "TRANSPORT_UNRESOLVED"
    else:
        outcome = "NON_REDIRECT_HTTP_STATUS_OBSERVED"

    return {
        "schema": "TASK255_PNCP_REDIRECT_LOCATION_PROBE_RESULT_V1",
        "status": "PASS_TASK255_SINGLE_NOFOLLOW_PROBE_OBSERVED",
        "outcome": outcome,
        "control": probe["control"],
        "requested_url": probe["requested_url"],
        "http_status": status,
        "location": location,
        "content_type": meta.get("content_type"),
        "bytes_received": int(meta.get("bytes_received") or 0),
        "body_sha256": meta.get("body_sha256"),
        "transport_error": meta.get("transport_error"),
        "source_get_count": 1,
        "redirect_followed": False,
        "retry_performed": False,
        "alternate_url_discovery_performed": False,
        "remaining_seven_targets_queried": False,
        "remaining_target_url_inference_allowed": False,
        "raw_payload_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "tce_network_used": False,
        "absence_inference_allowed": False,
        "global_pncp_absence_conclusion": False,
    }
