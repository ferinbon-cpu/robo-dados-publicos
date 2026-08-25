from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import socket
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

from .siope_official_olinda_api_discovery_design import load_json as load_design_json, validate_discovery_design


ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY"


class SiopeOfficialOlindaApiServiceDiscoveryError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


@dataclass(frozen=True)
class ServiceResponse:
    status: int
    content_type: str
    body: bytes


class ServiceTransport(Protocol):
    request_count: int

    def get(self, url: str, *, max_bytes: int, timeout_seconds: int, accepted_content_types: tuple[str, ...]) -> ServiceResponse:
        ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


class UrllibServiceTransport:
    def __init__(self) -> None:
        self.request_count = 0
        self._opener = build_opener(_NoRedirect())

    def get(self, url: str, *, max_bytes: int, timeout_seconds: int, accepted_content_types: tuple[str, ...]) -> ServiceResponse:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "www.fnde.gov.br" or parsed.query or parsed.fragment:
            raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_EXACT_ROOT_REQUIRED")
        if self.request_count != 0:
            raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_MORE_THAN_ONE_REQUEST")
        request = Request(
            url,
            headers={
                "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 (+public-transparency-research)",
                "Accept": "application/xml,application/atomsvc+xml,application/json;q=0.9,text/xml;q=0.8",
            },
            method="GET",
        )
        self.request_count += 1
        try:
            with self._opener.open(request, timeout=timeout_seconds) as response:
                status = int(getattr(response, "status", response.getcode()))
                content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
                raw = response.read(max_bytes + 1)
        except HTTPError as exc:
            raise SiopeOfficialOlindaApiServiceDiscoveryError(
                f"{ERROR}_HTTP_{int(exc.code)}",
                diagnostics={"http_status": int(exc.code)},
            ) from None
        except (TimeoutError, socket.timeout):
            raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_TIMEOUT") from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
                raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_TIMEOUT") from None
            raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_NETWORK") from None
        except OSError:
            raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_NETWORK") from None

        if status != 200:
            raise SiopeOfficialOlindaApiServiceDiscoveryError(
                f"{ERROR}_HTTP_STATUS", diagnostics={"http_status": status}
            )
        if content_type not in set(accepted_content_types):
            raise SiopeOfficialOlindaApiServiceDiscoveryError(
                f"{ERROR}_CONTENT_TYPE", diagnostics={"http_status": status, "content_type": content_type}
            )
        if len(raw) > max_bytes:
            raise SiopeOfficialOlindaApiServiceDiscoveryError(
                f"{ERROR}_RESPONSE_TOO_LARGE", diagnostics={"http_status": status, "content_type": content_type}
            )
        return ServiceResponse(status=status, content_type=content_type, body=raw)


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_{code}")


def validate_config(config: dict, design: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "EXACT_ONE_GET_OFFICIAL_OLINDA_SERVICE_DOCUMENT_DISCOVERY",
        "design_config_path": "config/source_expansion.siope_official_olinda_api_discovery_design.json",
        "exact_service_root": "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/",
        "method": "GET",
        "query_keys": [],
        "request_body": False,
        "follow_redirects": False,
        "follow_service_links": False,
        "max_requests": 1,
        "max_response_bytes": 1048576,
        "timeout_seconds": 15,
        "accepted_content_types": ["application/json", "application/xml", "application/atomsvc+xml", "text/xml"],
        "candidate_resource_name": "Dados_Gerais_Siope",
        "collection_name_pattern": "^[A-Za-z0-9_]+$",
        "max_collection_names": 64,
        "raw_response_persistence": "PROHIBITED",
        "response_header_persistence": "CONTENT_TYPE_ONLY",
        "query_value_persistence": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "browser_execution": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "authentication": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "head_request": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate_if_candidate_present": "M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_REVIEW_0_8_0",
        "stop_if_candidate_absent": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_CANDIDATE_ABSENT",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    parsed = urlparse(config["exact_service_root"])
    _require(parsed.scheme, "https", "ROOT_SCHEME")
    _require(parsed.hostname, "www.fnde.gov.br", "ROOT_HOST")
    _require(parsed.path, "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/", "ROOT_PATH")
    _require(parsed.query, "", "ROOT_QUERY")
    _require(parsed.fragment, "", "ROOT_FRAGMENT")
    if "352690" in config["exact_service_root"] or "Limeira" in config["exact_service_root"]:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_PILOT_VALUE_IN_ROOT")

    _require(design.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_DISCOVERY_DESIGN_0_8_0", "DESIGN_GATE")
    _require(design.get("next_gate"), config["gate_id"], "DESIGN_NEXT_GATE")
    probe = design.get("initial_live_probe") or {}
    _require(probe.get("exact_url"), config["exact_service_root"], "DESIGN_ROOT")
    _require(probe.get("query_keys"), [], "DESIGN_QUERY_KEYS")
    _require(probe.get("max_requests"), 1, "DESIGN_REQUEST_LIMIT")
    _require(probe.get("request_body"), False, "DESIGN_BODY")
    _require(probe.get("follow_links"), False, "DESIGN_FOLLOW_LINKS")


def _safe_name(value: str, *, pattern: re.Pattern[str]) -> str | None:
    value = value.strip()
    if pattern.fullmatch(value):
        return value
    parsed = urlparse(value)
    if parsed.query or parsed.fragment:
        return None
    last = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    return last if pattern.fullmatch(last) else None


def _parse_json_service_document(raw: bytes, *, pattern: re.Pattern[str]) -> list[str]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_SERVICE_DOCUMENT_PARSE") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_SERVICE_DOCUMENT_SHAPE")
    names: list[str] = []
    for item in payload["value"]:
        if not isinstance(item, dict):
            continue
        for key in ("name", "url"):
            candidate = item.get(key)
            if isinstance(candidate, str):
                safe = _safe_name(candidate, pattern=pattern)
                if safe and safe not in names:
                    names.append(safe)
                    break
    return names


def _parse_xml_service_document(raw: bytes, *, pattern: re.Pattern[str]) -> list[str]:
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_SERVICE_DOCUMENT_PARSE") from exc
    names: list[str] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "collection":
            continue
        href = element.attrib.get("href", "")
        safe = _safe_name(href, pattern=pattern) if href else None
        if not safe:
            for child in element:
                if child.tag.rsplit("}", 1)[-1] == "title" and child.text:
                    safe = _safe_name(child.text, pattern=pattern)
                    if safe:
                        break
        if safe and safe not in names:
            names.append(safe)
    return names


def parse_service_document(raw: bytes, content_type: str, *, name_pattern: str, max_names: int) -> tuple[str, ...]:
    pattern = re.compile(name_pattern)
    if content_type == "application/json":
        names = _parse_json_service_document(raw, pattern=pattern)
    else:
        names = _parse_xml_service_document(raw, pattern=pattern)
    if not names:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_NO_COLLECTION_NAMES")
    if len(names) > max_names:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_COLLECTION_LIMIT")
    return tuple(names)


def discover_service(config: dict, design: dict, *, transport: ServiceTransport | None = None) -> dict:
    validate_config(config, design)
    transport = transport or UrllibServiceTransport()
    response = transport.get(
        config["exact_service_root"],
        max_bytes=int(config["max_response_bytes"]),
        timeout_seconds=int(config["timeout_seconds"]),
        accepted_content_types=tuple(config["accepted_content_types"]),
    )
    if int(getattr(transport, "request_count", 0)) != 1:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(f"{ERROR}_REQUEST_COUNT")
    names = parse_service_document(
        response.body,
        response.content_type,
        name_pattern=config["collection_name_pattern"],
        max_names=int(config["max_collection_names"]),
    )
    candidate_present = config["candidate_resource_name"] in names
    diagnostics = {
        "http_status": response.status,
        "content_type": response.content_type,
        "service_document_parseable": True,
        "collection_name_count": len(names),
        "collection_names": list(names),
        "candidate_resource_present": candidate_present,
    }
    if not candidate_present:
        raise SiopeOfficialOlindaApiServiceDiscoveryError(config["stop_if_candidate_absent"], diagnostics=diagnostics)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "OFFICIAL_OLINDA_SERVICE_DOCUMENT_OBSERVED",
        "network_called": True,
        "network_method": "GET_ONLY",
        "request_count": 1,
        **diagnostics,
        "raw_response_persisted": False,
        "response_headers_persisted": ["content_type"],
        "query_values_persisted": False,
        "request_body_sent": False,
        "redirect_followed": False,
        "service_link_followed": False,
        "browser_execution": False,
        "dom_interaction_performed": False,
        "form_submission": False,
        "post_request_performed": False,
        "pilot_limeira_values_sent": False,
        "authentication_performed": False,
        "captcha_bypass": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "head_request_performed": False,
        "artifact_downloaded": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate_if_candidate_present"],
    }


def dry_run(config: dict, design: dict) -> dict:
    validate_config(config, design)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_SERVICE_DISCOVERY_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "request_count": 0,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def load_and_validate_design(root: Path, config: dict) -> dict:
    design = load_design_json(root / config["design_config_path"])
    base_source = load_design_json(root / design["base_source_config_path"])
    blocked_html = load_design_json(root / design["blocked_html_track_config_path"])
    research = load_design_json(root / design["public_research_evidence_path"])
    validate_discovery_design(design, base_source, blocked_html, research)
    return design
