from __future__ import annotations

from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse, urlunparse

from .siope_download_route_discovery import (
    ReadOnlyDeclaredResourceClient,
    SiopeDownloadRouteDiscoveryError,
)

ERROR = "STOP_SIOPE_PUBLIC_REPORT_SURFACE"


class SiopePublicReportSurfaceError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_REPORT_SURFACE_GATE_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "mode": "PUBLIC_REPORT_SURFACE_DISCOVERY",
        "index_url": "https://webservice.fnde.gov.br/siope/relatoriosMunicipais.jsp",
        "data_page_url": "https://webservice.fnde.gov.br/siope/dadosInformadosMunicipio.do",
        "required_index_anchor_text": "Dados Informados pelos Municípios",
        "success_condition": "EXACT_PUBLIC_REPORT_SURFACE_AND_FORM_CONTRACT_OBSERVED",
        "failure_condition": "PUBLIC_REPORT_SURFACE_OR_FORM_CONTRACT_UNPROVEN",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate_if_success": "M7_SIOPE_PUBLIC_REPORT_FORM_CONTRACT_VERIFICATION_0_8_0",
        "next_gate_if_human_challenge": "M7_SIOPE_PUBLIC_REPORT_HUMAN_CHALLENGE_DECISION_0_8_0",
        "next_gate_if_failure": "M7_SIOPE_AUTHENTICATED_FLOW_DECISION_0_8_0",
    }
    for key, value in exact.items():
        if config.get(key) != value:
            raise SiopePublicReportSurfaceError(f"{ERROR}_CONFIG_{key.upper()}")
    if config.get("allowed_hosts") != ["webservice.fnde.gov.br"]:
        raise SiopePublicReportSurfaceError(f"{ERROR}_CONFIG_ALLOWED_HOSTS")
    if config.get("limits") != {
        "max_page_bytes": 1048576,
        "max_total_bytes": 2097152,
        "max_forms": 8,
        "max_fields_per_form": 48,
    }:
        raise SiopePublicReportSurfaceError(f"{ERROR}_CONFIG_LIMITS")
    if config.get("discovery_rules") != {
        "methods": ["GET"],
        "follow_exact_declared_data_link": True,
        "parse_form_contract": True,
        "submit_forms": False,
        "guess_parameters": False,
        "bypass_captcha": False,
        "authenticate": False,
        "capture_credentials": False,
        "capture_cookies": False,
        "capture_field_values": False,
        "download_artifacts": False,
    }:
        raise SiopePublicReportSurfaceError(f"{ERROR}_CONFIG_RULES")


def load_public_report_surface_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(re.sub(r"\s+", " ", value)).strip()
    return value


def _without_query(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", "", ""))


def find_exact_declared_data_link(html: str, *, page_url: str, required_anchor: str, data_page_url: str) -> dict | None:
    target_text = _clean_text(required_anchor).casefold()
    target_url = _without_query(data_page_url)
    pattern = re.compile(r"<a\b[^>]*\bhref\s*=\s*['\"]([^'\"]+)['\"][^>]*>(.*?)</a\s*>", re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(html):
        href = unescape(match.group(1)).strip()
        anchor = _clean_text(match.group(2))
        absolute = urljoin(page_url, href)
        if anchor.casefold() != target_text:
            continue
        if _without_query(absolute) != target_url:
            continue
        parsed = urlparse(absolute)
        return {
            "anchor_text": anchor,
            "scheme": parsed.scheme,
            "host": parsed.hostname or "",
            "path": parsed.path or "/",
            "query_present": bool(parsed.query),
            "network_sent": False,
        }
    return None


def _attr(tag: str, name: str) -> str | None:
    match = re.search(rf"\b{name}\s*=\s*(['\"])(.*?)\1", tag, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return unescape(match.group(2)).strip()
    match = re.search(rf"\b{name}\s*=\s*([^\s>]+)", tag, flags=re.IGNORECASE)
    return unescape(match.group(1)).strip() if match else None


def extract_form_contracts(html: str, *, page_url: str, allowed_hosts: tuple[str, ...], max_forms: int, max_fields: int) -> tuple[dict, ...]:
    forms: list[dict] = []
    pattern = re.compile(r"(<form\b[^>]*>)(.*?)</form\s*>", re.IGNORECASE | re.DOTALL)
    for opening, body in pattern.findall(html)[:max_forms]:
        method = (_attr(opening, "method") or "GET").upper()
        action_raw = _attr(opening, "action") or page_url
        action_abs = urljoin(page_url, action_raw)
        parsed = urlparse(action_abs)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            action_status = "NOT_ALLOWED"
        else:
            action_status = "OFFICIAL_ALLOWLIST"

        fields: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for tag in re.findall(r"<(?:input|select|textarea)\b[^>]*>", body, flags=re.IGNORECASE):
            name = _attr(tag, "name")
            if not name:
                continue
            tag_name_match = re.match(r"<\s*([a-zA-Z0-9]+)", tag)
            tag_name = tag_name_match.group(1).lower() if tag_name_match else "unknown"
            field_type = (_attr(tag, "type") or tag_name).lower()
            key = (name, field_type)
            if key in seen:
                continue
            seen.add(key)
            fields.append({"name": name[:128], "type": field_type[:64]})
            if len(fields) >= max_fields:
                break

        forms.append({
            "method": method,
            "action": {
                "scheme": parsed.scheme,
                "host": parsed.hostname or "",
                "path": parsed.path or "/",
                "query_present": bool(parsed.query),
                "status": action_status,
                "network_sent": False,
            },
            "field_count": len(fields),
            "fields": fields,
        })
    return tuple(forms)


def _captcha_present(html: str) -> bool:
    lower = html.lower()
    return any(marker in lower for marker in ("captcha", "recaptcha", "g-recaptcha", "hcaptcha"))


def discover_public_report_surface(config: dict, *, client: ReadOnlyDeclaredResourceClient | None = None) -> dict:
    _validate_config(config)
    allowed_hosts = tuple(config["allowed_hosts"])
    client = client or ReadOnlyDeclaredResourceClient(allowed_hosts=allowed_hosts)
    max_page = int(config["limits"]["max_page_bytes"])
    max_total = int(config["limits"]["max_total_bytes"])

    try:
        index = client.get_text(
            config["index_url"],
            max_bytes=max_page,
            allowed_content_types=("text/html", "application/xhtml+xml"),
        )
    except SiopeDownloadRouteDiscoveryError as exc:
        raise SiopePublicReportSurfaceError(f"{ERROR}_INDEX_{exc}") from None

    declared = find_exact_declared_data_link(
        index.body,
        page_url=index.url,
        required_anchor=config["required_index_anchor_text"],
        data_page_url=config["data_page_url"],
    )
    if not declared:
        raise SiopePublicReportSurfaceError(
            f"{ERROR}_DECLARED_DATA_LINK_UNPROVEN",
            diagnostics={"index_status": index.status, "index_bytes": index.byte_count},
        )

    remaining = max_total - index.byte_count
    if remaining <= 0:
        raise SiopePublicReportSurfaceError(f"{ERROR}_TOTAL_BYTE_LIMIT")
    try:
        data_page = client.get_text(
            config["data_page_url"],
            max_bytes=min(max_page, remaining),
            allowed_content_types=("text/html", "application/xhtml+xml"),
        )
    except SiopeDownloadRouteDiscoveryError as exc:
        raise SiopePublicReportSurfaceError(f"{ERROR}_DATA_PAGE_{exc}") from None

    contracts = extract_form_contracts(
        data_page.body,
        page_url=data_page.url,
        allowed_hosts=allowed_hosts,
        max_forms=int(config["limits"]["max_forms"]),
        max_fields=int(config["limits"]["max_fields_per_form"]),
    )
    usable = [item for item in contracts if item["field_count"] > 0 and item["action"]["status"] == "OFFICIAL_ALLOWLIST"]
    if not usable:
        raise SiopePublicReportSurfaceError(
            f"{ERROR}_FORM_CONTRACT_UNPROVEN",
            diagnostics={
                "index_status": index.status,
                "data_page_status": data_page.status,
                "form_count": len(contracts),
                "captcha_present": _captcha_present(data_page.body),
            },
        )

    human_challenge = _captcha_present(data_page.body)
    next_gate = config["next_gate_if_human_challenge"] if human_challenge else config["next_gate_if_success"]
    return {
        "status": "PASS_M7_SIOPE_PUBLIC_REPORT_SURFACE_GATE",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "fetched_page_count": 2,
        "total_fetched_bytes": index.byte_count + data_page.byte_count,
        "index_status": index.status,
        "data_page_status": data_page.status,
        "declared_data_link": declared,
        "form_count": len(contracts),
        "usable_form_contract_count": len(usable),
        "form_contracts": list(usable[:4]),
        "captcha_present": human_challenge,
        "form_submission": False,
        "form_action_network_sent": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "field_values_captured": False,
        "artifact_downloaded": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "surface_status": "PUBLIC_REPORT_FORM_CONTRACT_OBSERVED",
        "next_gate": next_gate,
    }
