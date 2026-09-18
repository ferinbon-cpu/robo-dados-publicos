from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping, Protocol

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/task256_task255_timeout_curl_diagnostic.v1.json"
DEFAULT_EVIDENCE = ROOT / "docs/evidence/TASK_256_TASK255_TIMEOUT_CANONICAL_0.8.0.json"
EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


class Task256Stop(RuntimeError):
    pass


class DiagnosticTransport(Protocol):
    def get(self, url: str, *, connect_timeout: int, max_time: int) -> dict[str, Any]:
        ...


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task256Stop(code)


def load_config(path: Path | str = DEFAULT_CONFIG) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(cfg.get("schema") == "TASK256_TASK255_TIMEOUT_CURL_DIAGNOSTIC_V1", "TASK256_CONFIG_SCHEMA")
    _stop(cfg.get("task") == "TASK_256", "TASK256_CONFIG_TASK")
    _stop(cfg.get("issue") == 845, "TASK256_CONFIG_ISSUE")
    _stop(cfg.get("base_main_sha") == "72c22246edcde103c8b51dd8a959f700606315c1", "TASK256_BASE_MAIN")
    _stop(cfg.get("mode") == "T1_READONLY_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION", "TASK256_MODE")

    t255 = cfg.get("source_task255") or {}
    _stop(t255.get("run_id") == 35297299432, "TASK256_TASK255_RUN")
    _stop(t255.get("job_id") == 105452378888, "TASK256_TASK255_JOB")
    _stop(t255.get("artifact_id") == 10527918489, "TASK256_TASK255_ARTIFACT")
    _stop(t255.get("artifact_zip_sha256") == "bc1a12214ce35464b4e1d70674a4f0b93d4846beeac04050d5ae58c953d0440f", "TASK256_TASK255_ARTIFACT_SHA")
    _stop(t255.get("result_sha256") == "52fbcbd4a06ba2a8c094bf8898a23ead52ce6aa18c214473cebe60bcf97af8d7", "TASK256_TASK255_RESULT_SHA")
    _stop(t255.get("status") == "PASS_TASK255_SINGLE_NOFOLLOW_PROBE_OBSERVED", "TASK256_TASK255_STATUS")
    _stop(t255.get("outcome") == "TRANSPORT_UNRESOLVED", "TASK256_TASK255_OUTCOME")
    _stop(t255.get("transport_error") == "URL_ERROR:TimeoutError", "TASK256_TASK255_ERROR")
    _stop(t255.get("source_get_count") == 1, "TASK256_TASK255_GETS")
    _stop(t255.get("remaining_seven_targets_queried") is False, "TASK256_TASK255_REMAINING")
    _stop(t255.get("authorization_consumed") is True, "TASK256_TASK255_AUTH")

    diag = cfg.get("diagnostic") or {}
    _stop(diag.get("control") == "45132495000140-1-000646/2026", "TASK256_CONTROL")
    _stop(diag.get("requested_url") == "https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/646", "TASK256_URL")
    _stop(diag.get("method") == "GET", "TASK256_METHOD")
    _stop(diag.get("tool") == "curl", "TASK256_TOOL")
    _stop(diag.get("max_remote_get_count") == 1, "TASK256_GET_BUDGET")
    _stop(diag.get("retry") is False, "TASK256_RETRY")
    _stop(diag.get("follow_redirects") is False, "TASK256_REDIRECT_FOLLOW")
    _stop(diag.get("alternate_url_discovery") is False, "TASK256_ALT_DISCOVERY")
    _stop(diag.get("response_body_persistence") is False, "TASK256_BODY")
    _stop(diag.get("require_effective_url_exact") is True, "TASK256_EFFECTIVE_URL")
    _stop(diag.get("infer_remaining_target_urls") is False, "TASK256_REMAINING_INFERENCE")

    auth = cfg.get("authorization") or {}
    _stop(auth.get("required_task") == "TASK_256_LIVE_AUTHORIZATION", "TASK256_AUTH_TASK")
    _stop(auth.get("required_operation") == "EXACT_1_TASK255_FIRST_TARGET_CURL_NOFOLLOW_TRANSPORT_DIAGNOSTIC", "TASK256_AUTH_OPERATION")
    _stop(auth.get("attempt_count") == 1, "TASK256_AUTH_ATTEMPT")
    for key, value in auth.items():
        if key.endswith("_authorized_by_default") or key.endswith("_reuse_allowed"):
            _stop(value is False, "TASK256_AUTH_DEFAULT_" + key.upper())

    _stop(all(v is False for v in (cfg.get("effects") or {}).values()), "TASK256_EFFECTS")
    _stop(cfg.get("next_gate") == "OWNER_AUTHORIZED_SINGLE_PNCP_CURL_NOFOLLOW_TRANSPORT_DIAGNOSTIC_ON_MERGED_TASK256_SHA", "TASK256_NEXT_GATE")
    return cfg


def load_evidence(path: Path | str = DEFAULT_EVIDENCE) -> dict[str, Any]:
    ev = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(ev.get("schema") == "TASK256_TASK255_TIMEOUT_CANONICAL_V1", "TASK256_EVIDENCE_SCHEMA")
    _stop(ev.get("status") == "CANONICAL_TASK255_TIMEOUT_AFTER_SINGLE_GET_WITH_PRIOR_TASK254_3XX_PRESERVED_SEPARATELY", "TASK256_EVIDENCE_STATUS")
    t255 = ev.get("task255") or {}
    _stop(t255.get("run_id") == 35297299432, "TASK256_EVIDENCE_RUN")
    _stop(t255.get("transport_error") == "URL_ERROR:TimeoutError", "TASK256_EVIDENCE_TIMEOUT")
    _stop(t255.get("source_get_count") == 1, "TASK256_EVIDENCE_GETS")
    _stop(t255.get("authorization_consumed") is True, "TASK256_EVIDENCE_AUTH")
    _stop(len(ev.get("untouched_targets") or []) == 7, "TASK256_EVIDENCE_UNTOUCHED")
    adj = ev.get("epistemic_adjudication") or {}
    _stop(adj.get("task254_3xx_condition_proven_for_its_run") is True, "TASK256_EVIDENCE_TASK254")
    _stop(adj.get("task255_timeout_proven_for_its_run") is True, "TASK256_EVIDENCE_TASK255")
    _stop(adj.get("redirect_destination_proven") is False, "TASK256_EVIDENCE_DESTINATION")
    _stop(adj.get("pncp_records_absent") is False, "TASK256_EVIDENCE_ABSENCE")
    return ev


def build_curl_command(url: str, *, connect_timeout: int, max_time: int) -> list[str]:
    return [
        "curl",
        "--silent",
        "--show-error",
        "--request", "GET",
        "--retry", "0",
        "--max-redirs", "0",
        "--connect-timeout", str(connect_timeout),
        "--max-time", str(max_time),
        "--output", "/dev/null",
        "--header", "Accept: application/json",
        "--user-agent", "robo-dados-publicos-task256/0.8.0",
        "--write-out", "%{json}",
        url,
    ]


class CurlNoFollowTransport:
    def get(self, url: str, *, connect_timeout: int, max_time: int) -> dict[str, Any]:
        cmd = build_curl_command(url, connect_timeout=connect_timeout, max_time=max_time)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max_time + 15,
            check=False,
        )
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        meta: dict[str, Any] = {}
        if stdout:
            try:
                parsed = json.loads(stdout)
                if isinstance(parsed, dict):
                    meta = parsed
            except json.JSONDecodeError:
                meta = {}

        return {
            "requested_url": url,
            "curl_exit_code": int(proc.returncode),
            "curl_error": stderr[:240] or None,
            "http_code": int(meta.get("http_code") or 0),
            "redirect_url": meta.get("redirect_url") or None,
            "url_effective": meta.get("url_effective") or None,
            "remote_ip": meta.get("remote_ip") or None,
            "remote_port": meta.get("remote_port"),
            "local_ip": meta.get("local_ip") or None,
            "local_port": meta.get("local_port"),
            "time_namelookup": meta.get("time_namelookup"),
            "time_connect": meta.get("time_connect"),
            "time_appconnect": meta.get("time_appconnect"),
            "time_starttransfer": meta.get("time_starttransfer"),
            "time_total": meta.get("time_total"),
            "content_type": meta.get("content_type") or None,
            "size_download": meta.get("size_download"),
            "remote_get_count": 1,
            "response_body_persisted": False,
        }


def validate_live_authorization(
    authorization: Mapping[str, Any] | None,
    *,
    expected_implementation_sha: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if not authorization:
        return {"status": "STOP_TASK256_LIVE_NOT_AUTHORIZED"}
    if authorization.get("prior_authorization_reused") is True:
        return {"status": "STOP_TASK256_PRIOR_AUTHORIZATION_REUSE"}
    if not HEX40_RE.fullmatch(expected_implementation_sha or ""):
        return {"status": "STOP_TASK256_IMPLEMENTATION_SHA_FORMAT"}

    diag = config["diagnostic"]
    required = {
        "task": "TASK_256_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "implementation_branch": "main",
        "runtime_branch": config["runtime"]["branch"],
        "implementation_sha": expected_implementation_sha,
        "operation": "EXACT_1_TASK255_FIRST_TARGET_CURL_NOFOLLOW_TRANSPORT_DIAGNOSTIC",
        "control": diag["control"],
        "requested_url": diag["requested_url"],
        "max_remote_get_count": 1,
        "attempt_count": 1,
        "owner_authorized": True,
        "source_network_authorized": True,
        "follow_redirects": False,
        "automatic_retry": False,
        "alternate_url_discovery": False,
        "response_body_persistence": False,
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
        return {"status": "STOP_TASK256_AUTHORIZATION_CONTRACT_MISMATCH"}
    return {"status": "PASS_TASK256_LIVE_AUTHORIZATION"}


def execute_diagnostic(
    config: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    transport: DiagnosticTransport,
    authorization: Mapping[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    _stop(evidence.get("schema") == "TASK256_TASK255_TIMEOUT_CANONICAL_V1", "TASK256_EXEC_EVIDENCE")
    if not offline_test_mode:
        auth = validate_live_authorization(
            authorization,
            expected_implementation_sha=expected_implementation_sha,
            config=config,
        )
        if auth["status"] != "PASS_TASK256_LIVE_AUTHORIZATION":
            return {
                "schema": "TASK256_PNCP_CURL_TRANSPORT_DIAGNOSTIC_RESULT_V1",
                "status": auth["status"],
                "source_get_count": 0,
                "response_body_persisted": False,
                "absence_inference_allowed": False,
            }

    diag = config["diagnostic"]
    meta = transport.get(
        diag["requested_url"],
        connect_timeout=int(diag["connect_timeout_seconds"]),
        max_time=int(diag["max_time_seconds"]),
    )
    _stop(meta.get("remote_get_count") == 1, "TASK256_REMOTE_GET_COUNT")
    _stop(meta.get("requested_url") == diag["requested_url"], "TASK256_REQUEST_URL_DRIFT")
    _stop(meta.get("response_body_persisted") is False, "TASK256_BODY_PERSISTED")

    effective = meta.get("url_effective")
    if effective:
        _stop(effective == diag["requested_url"], "TASK256_EFFECTIVE_URL_DRIFT")

    exit_code = int(meta.get("curl_exit_code") or 0)
    http_code = int(meta.get("http_code") or 0)
    redirect_url = meta.get("redirect_url")
    if exit_code == 28:
        outcome = "CURL_TIMEOUT_WITH_TRANSPORT_TIMINGS"
    elif 300 <= http_code < 400 and redirect_url:
        outcome = "REDIRECT_LOCATION_CAPTURED"
    elif 300 <= http_code < 400:
        outcome = "REDIRECT_STATUS_WITHOUT_LOCATION"
    elif http_code == 200:
        outcome = "HTTP_200_OBSERVED"
    elif http_code == 0:
        outcome = "NO_HTTP_RESPONSE_WITH_TRANSPORT_DIAGNOSTICS"
    else:
        outcome = "NON_REDIRECT_HTTP_STATUS_OBSERVED"

    return {
        "schema": "TASK256_PNCP_CURL_TRANSPORT_DIAGNOSTIC_RESULT_V1",
        "status": "PASS_TASK256_SINGLE_CURL_NOFOLLOW_DIAGNOSTIC_OBSERVED",
        "outcome": outcome,
        "control": diag["control"],
        "requested_url": diag["requested_url"],
        "curl_exit_code": exit_code,
        "curl_error": meta.get("curl_error"),
        "http_code": http_code,
        "redirect_url": redirect_url,
        "url_effective": effective,
        "remote_ip": meta.get("remote_ip"),
        "remote_port": meta.get("remote_port"),
        "local_ip": meta.get("local_ip"),
        "local_port": meta.get("local_port"),
        "time_namelookup": meta.get("time_namelookup"),
        "time_connect": meta.get("time_connect"),
        "time_appconnect": meta.get("time_appconnect"),
        "time_starttransfer": meta.get("time_starttransfer"),
        "time_total": meta.get("time_total"),
        "content_type": meta.get("content_type"),
        "size_download": meta.get("size_download"),
        "source_get_count": 1,
        "redirect_followed": False,
        "retry_performed": False,
        "alternate_url_discovery_performed": False,
        "remaining_seven_targets_queried": False,
        "remaining_target_url_inference_allowed": False,
        "response_body_persisted": False,
        "raw_payload_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "tce_network_used": False,
        "absence_inference_allowed": False,
        "global_pncp_absence_conclusion": False,
    }
