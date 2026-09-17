"""Bounded diagnostic probe for TASK249 edition 7323 byte-count stop."""
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

EXPECTED_REPOSITORY = "ferinbon-cpu/robo-dados-publicos"
EXPECTED_BRANCH = "main"
EXPECTED_SOURCE = "LIMEIRA_JORNAL_OFICIAL"
EXPECTED_EDITION = 7323
ALLOWED_HOST = "ecrie.com.br"
PASS_STATUS = "PASS_TASK250_7323_BYTECOUNT_DIAGNOSTIC"


class Task250Stop(RuntimeError):
    pass


class ProbeSource(Protocol):
    network_capable: bool
    def fetch(self, *, url: str, destination: Path) -> dict[str, Any]: ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


@dataclass
class LiveProbeSource:
    user_agent: str = "ROBO_DADOS_PUBLICOS/0.8.0 TASK250"
    timeout: int = 120
    network_capable: bool = True

    def fetch(self, *, url: str, destination: Path) -> dict[str, Any]:
        opener = build_opener(_NoRedirect())
        request = Request(url, headers={"User-Agent": self.user_agent}, method="GET")
        digest = hashlib.sha256()
        total = 0
        destination.parent.mkdir(parents=True, exist_ok=True)
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
            raise Task250Stop(f"SOURCE_HTTP_{exc.code}") from exc
        return {
            "http_status": status,
            "requested_url": url,
            "final_url": final_url,
            "content_type": content_type,
            "transport_bytes": total,
            "transport_sha256": digest.hexdigest(),
            "path": str(destination),
        }


def load_config(path: str | Path = "config/task250_jom_7323_bytecount_probe.v1.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _stop(code: str, **details: object) -> dict[str, Any]:
    return {
        "status": code,
        "source_gets": int(details.pop("source_gets", 0)),
        "retry_performed": False,
        "redirect_followed": False,
        "alternate_url_discovery_performed": False,
        "raw_pdf_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        **details,
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("task") != "TASK_250" or config.get("schema") != "TASK250_JOM_7323_BYTECOUNT_PROBE_V1":
        raise Task250Stop("CONFIG_IDENTITY_MISMATCH")
    if config.get("mode") != "T1_READONLY_DIAGNOSTIC_IMPLEMENTED_LIVE_DISABLED_UNTIL_EXACT_OWNER_AUTHORIZATION":
        raise Task250Stop("CONFIG_MODE_MISMATCH")
    scope = config.get("scope") or {}
    if scope.get("edition") != EXPECTED_EDITION:
        raise Task250Stop("CONFIG_EDITION_MISMATCH")
    url = str(scope.get("document_url") or "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise Task250Stop("CONFIG_URL_INVALID")
    limits = config.get("limits") or {}
    if limits.get("max_source_gets") != 1 or limits.get("automatic_retry") is not False:
        raise Task250Stop("CONFIG_BUDGET_MISMATCH")
    if limits.get("redirects") is not False or limits.get("alternate_url_discovery") is not False:
        raise Task250Stop("CONFIG_DISCOVERY_MISMATCH")
    persistence = config.get("persistence") or {}
    if persistence.get("sanitized_result_artifact") is not True:
        raise Task250Stop("CONFIG_RESULT_PERSISTENCE_MISMATCH")
    for key in ("raw_pdf_artifact", "raw_pdf_repository", "drive_write", "serving_write", "publication"):
        if persistence.get(key) is not False:
            raise Task250Stop("CONFIG_PROHIBITED_PERSISTENCE_ENABLED")


def validate_live_authorization(auth: dict[str, Any] | None, *, expected_sha: str) -> bool:
    required = {
        "task": "TASK_250_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "branch": EXPECTED_BRANCH,
        "implementation_sha": expected_sha,
        "source": EXPECTED_SOURCE,
        "operation": "EXACT_1_JOM_7323_BYTECOUNT_DIAGNOSTIC_GET",
        "edition": EXPECTED_EDITION,
        "max_source_gets": 1,
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
    return bool(auth) and all(auth.get(k) == v for k, v in required.items())


def classify_byte_count(*, transport_bytes: int, stat_bytes: int, max_bytes: int) -> str:
    if stat_bytes <= 0:
        return "EMPTY_FILE"
    if stat_bytes > max_bytes:
        return "OVER_MAX_BYTES"
    if transport_bytes != stat_bytes:
        return "TRANSPORT_COUNTER_MISMATCH"
    return "BYTE_COUNT_VALID"


def execute(
    config: dict[str, Any],
    *,
    source: ProbeSource,
    authorization: dict[str, Any] | None,
    expected_implementation_sha: str,
    offline_test_mode: bool = False,
) -> dict[str, Any]:
    try:
        validate_config(config)
    except Task250Stop as exc:
        return _stop(f"STOP_TASK250_{exc}")
    if offline_test_mode:
        if getattr(source, "network_capable", True):
            return _stop("STOP_TASK250_OFFLINE_NETWORK_CAPABLE_SOURCE")
        if not authorization or authorization.get("synthetic_test_only") is not True:
            return _stop("STOP_TASK250_OFFLINE_SYNTHETIC_AUTH_REQUIRED")
    else:
        if not getattr(source, "network_capable", False):
            return _stop("STOP_TASK250_LIVE_SOURCE_NOT_NETWORK_CAPABLE")
        if not validate_live_authorization(authorization, expected_sha=expected_implementation_sha):
            return _stop("STOP_TASK250_LIVE_NOT_AUTHORIZED")

    scope = config["scope"]
    max_bytes = int(config["limits"]["max_pdf_bytes"])
    with tempfile.TemporaryDirectory(prefix="task250_") as temp_dir:
        destination = Path(temp_dir) / "jom_7323.pdf"
        try:
            observed = source.fetch(url=scope["document_url"], destination=destination)
        except Task250Stop as exc:
            return _stop(f"STOP_TASK250_{exc}", source_gets=1, edition=EXPECTED_EDITION)
        if observed.get("http_status") != 200:
            return _stop("STOP_TASK250_HTTP_NOT_200", source_gets=1, edition=EXPECTED_EDITION)
        if observed.get("requested_url") != scope["document_url"] or observed.get("final_url") != scope["document_url"]:
            return _stop("STOP_TASK250_URL_REDIRECT_OR_DRIFT", source_gets=1, edition=EXPECTED_EDITION)
        stat_bytes = destination.stat().st_size if destination.is_file() else 0
        transport_bytes = int(observed.get("transport_bytes") or 0)
        outcome = classify_byte_count(transport_bytes=transport_bytes, stat_bytes=stat_bytes, max_bytes=max_bytes)
        diagnostic = {
            "edition": EXPECTED_EDITION,
            "source_id": scope["source_id"],
            "logical_key": scope["logical_key"],
            "document_url": scope["document_url"],
            "http_status": observed.get("http_status"),
            "content_type": str(observed.get("content_type") or "").split(";", 1)[0].strip().lower(),
            "transport_bytes": transport_bytes,
            "temporary_stat_bytes": stat_bytes,
            "configured_max_bytes": max_bytes,
            "byte_count_outcome": outcome,
        }
    return {
        "status": PASS_STATUS,
        "source_gets": 1,
        "diagnostic": diagnostic,
        "retry_performed": False,
        "redirect_followed": False,
        "alternate_url_discovery_performed": False,
        "raw_pdf_persisted": False,
        "drive_write_count": 0,
        "serving_write_count": 0,
        "publication_count": 0,
        "next_gate": "ADJUDICATE_TASK249_FAILURE_BEFORE_ANY_CORRECTIVE_FULL_ATTEMPT",
    }
