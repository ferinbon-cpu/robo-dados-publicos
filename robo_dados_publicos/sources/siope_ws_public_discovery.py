from __future__ import annotations

from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urljoin, urlparse, urlunparse

from .siope_download_route_discovery import (
    ReadOnlyDeclaredResourceClient,
    SiopeDownloadRouteDiscoveryError,
)


ERROR = "STOP_SIOPE_WS_PUBLIC_DISCOVERY"
_SIGNAL_TERMS = ("ws-siope", "webservice", "web service", "wsdl", "soap", "api")
_DOC_TERMS = ("documentação", "documentacao", "manual", "orientação", "orientacao", "especificação", "especificacao")
_DOC_EXTENSIONS = (".pdf", ".doc", ".docx", ".html", ".htm", ".txt")
_BINARY_EXTENSIONS = (".pdf", ".doc", ".docx", ".zip", ".gz", ".rar", ".xlsx", ".xls")


class SiopeWsPublicDiscoveryError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_WS_PUBLIC_DISCOVERY_DESIGN_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "mode": "PUBLIC_READ_ONLY_DISCOVERY",
        "success_condition": "EXPLICIT_PUBLIC_WS_SIOPE_ENDPOINT_OR_OFFICIAL_DOCUMENTATION_OBSERVED",
        "failure_condition": "NO_EXPLICIT_PUBLIC_WS_SIOPE_ENDPOINT_OR_DOCUMENTATION",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate_if_success": "M7_SIOPE_WS_PUBLIC_ENDPOINT_CONTRACT_VERIFICATION_0_8_0",
        "next_gate_if_failure": "M7_SIOPE_AUTHENTICATED_FLOW_DECISION_0_8_0",
    }
    for key, value in exact.items():
        if config.get(key) != value:
            raise SiopeWsPublicDiscoveryError(f"{ERROR}_CONFIG_{key.upper()}")
    if config.get("allowed_hosts") != ["www.fnde.gov.br", "webservice.fnde.gov.br"]:
        raise SiopeWsPublicDiscoveryError(f"{ERROR}_CONFIG_ALLOWED_HOSTS")
    if config.get("initial_urls") != [
        "https://www.fnde.gov.br/siope/download.do",
        "https://www.fnde.gov.br/siope/dadosInformadosMunicipio.do",
    ]:
        raise SiopeWsPublicDiscoveryError(f"{ERROR}_CONFIG_INITIAL_URLS")
    limits = config.get("limits") or {}
    if limits != {
        "max_initial_pages": 2,
        "max_followed_links": 12,
        "max_page_bytes": 1048576,
        "max_total_bytes": 4194304,
    }:
        raise SiopeWsPublicDiscoveryError(f"{ERROR}_CONFIG_LIMITS")
    rules = config.get("discovery_rules") or {}
    expected_rules = {
        "methods": ["GET"],
        "follow_only_explicit_declared_links": True,
        "guess_endpoint_paths": False,
        "submit_forms": False,
        "bypass_captcha": False,
        "authenticate": False,
        "capture_credentials": False,
        "capture_cookies": False,
        "download_artifacts": False,
    }
    if rules != expected_rules:
        raise SiopeWsPublicDiscoveryError(f"{ERROR}_CONFIG_RULES")


def load_ws_public_discovery_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _text(value: str, limit: int = 180) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", value)
    cleaned = unescape(re.sub(r"\s+", " ", cleaned)).strip()
    return cleaned[:limit]


def _signals(value: str) -> list[str]:
    lower = value.lower()
    found = []
    for term in _SIGNAL_TERMS:
        if term in lower:
            normalized = "webservice" if term == "web service" else term
            if normalized not in found:
                found.append(normalized)
    return found


def _sanitize_url(url: str) -> dict:
    parsed = urlparse(url)
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", "", ""))
    keys = sorted({key[:128] for key, _ in parse_qsl(parsed.query, keep_blank_values=True) if key})[:32]
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "path": parsed.path or "/",
        "url_without_query": clean,
        "query_present": bool(parsed.query),
        "query_keys": keys,
    }


def extract_declared_ws_links(html: str, *, page_url: str, allowed_hosts: tuple[str, ...]) -> tuple[dict, ...]:
    found: list[dict] = []
    seen: set[tuple[str, tuple[str, ...], str]] = set()
    pattern = re.compile(r"<a\b[^>]*\bhref\s*=\s*['\"]([^'\"]+)['\"][^>]*>(.*?)</a\s*>", re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(html):
        raw_href = unescape(match.group(1)).strip()
        if not raw_href or raw_href.lower().startswith(("javascript:", "mailto:", "tel:")):
            continue
        absolute = urljoin(page_url, raw_href)
        parsed = urlparse(absolute)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            continue
        anchor = _text(match.group(2))
        context = _text(html[max(0, match.start() - 260): min(len(html), match.end() + 260)], 520)
        signal_source = " ".join((raw_href, anchor, context))
        signals = _signals(signal_source)
        if not signals:
            continue

        path_lower = parsed.path.lower()
        href_lower = raw_href.lower()
        anchor_lower = anchor.lower()
        endpoint_explicit = any(term in href_lower for term in ("ws-siope", "webservice", "wsdl", "soap"))
        endpoint_explicit = endpoint_explicit or any(term in anchor_lower for term in ("ws-siope", "webservice", "web service", "wsdl", "soap"))
        documentation_explicit = path_lower.endswith(_DOC_EXTENSIONS) and (
            "ws-siope" in signal_source.lower()
            or "webservice" in signal_source.lower()
            or any(term in anchor_lower for term in _DOC_TERMS)
        )
        classification = "SIGNAL_LINK"
        if endpoint_explicit:
            classification = "EXPLICIT_WS_ENDPOINT_LINK"
        elif documentation_explicit:
            classification = "EXPLICIT_WS_DOCUMENTATION_LINK"

        sanitized = _sanitize_url(absolute)
        key = (sanitized["url_without_query"], tuple(sanitized["query_keys"]), classification)
        if key in seen:
            continue
        seen.add(key)
        found.append({
            "classification": classification,
            "anchor_text": anchor,
            "signals": signals,
            **sanitized,
            "network_sent": False,
        })
    return tuple(found)


def _page_markers(body: str) -> dict:
    lower = body.lower()
    return {
        "ws_siope_text_present": "ws-siope" in lower,
        "webservice_text_present": "webservice" in lower or "web service" in lower,
        "captcha_text_present": "captcha" in lower or "recaptcha" in lower,
    }


def _followable_documentation(link: dict) -> bool:
    if link.get("classification") != "EXPLICIT_WS_DOCUMENTATION_LINK":
        return False
    path = str(link.get("path", "")).lower()
    return not path.endswith(_BINARY_EXTENSIONS)


def discover_ws_public_surface(config: dict, *, client: ReadOnlyDeclaredResourceClient | None = None) -> dict:
    _validate_config(config)
    allowed_hosts = tuple(config["allowed_hosts"])
    client = client or ReadOnlyDeclaredResourceClient(allowed_hosts=allowed_hosts)
    max_page = int(config["limits"]["max_page_bytes"])
    max_total = int(config["limits"]["max_total_bytes"])
    max_follow = int(config["limits"]["max_followed_links"])

    pages: list[dict] = []
    observed_links: list[dict] = []
    fetch_failures: list[dict] = []
    total_bytes = 0
    queue = [(url, "INITIAL") for url in config["initial_urls"][: int(config["limits"]["max_initial_pages"])]]
    queued = {url for url, _ in queue}
    fetched: set[str] = set()
    followed_count = 0

    while queue:
        url, origin = queue.pop(0)
        if url in fetched:
            continue
        if total_bytes >= max_total:
            break
        limit = min(max_page, max_total - total_bytes)
        try:
            response = client.get_text(
                url,
                max_bytes=limit,
                allowed_content_types=("text/html", "application/xhtml+xml", "text/plain"),
            )
        except SiopeDownloadRouteDiscoveryError as exc:
            fetch_failures.append({
                "page": _sanitize_url(url),
                "origin": origin,
                "reason": str(exc),
            })
            fetched.add(url)
            continue

        fetched.add(url)
        total_bytes += response.byte_count
        links = extract_declared_ws_links(response.body, page_url=response.url, allowed_hosts=allowed_hosts)
        markers = _page_markers(response.body)
        pages.append({
            "page": _sanitize_url(response.url),
            "origin": origin,
            "status": response.status,
            "content_type": response.content_type,
            "byte_count": response.byte_count,
            "markers": markers,
            "declared_signal_link_count": len(links),
        })
        for link in links:
            if not any(
                existing["url_without_query"] == link["url_without_query"]
                and existing["query_keys"] == link["query_keys"]
                and existing["classification"] == link["classification"]
                for existing in observed_links
            ):
                observed_links.append(link)
            if _followable_documentation(link) and followed_count < max_follow:
                follow_url = link["url_without_query"]
                if follow_url not in queued and follow_url not in fetched:
                    queue.append((follow_url, "DECLARED_DOCUMENTATION_LINK"))
                    queued.add(follow_url)
                    followed_count += 1

    candidates = [
        item for item in observed_links
        if item["classification"] in {"EXPLICIT_WS_ENDPOINT_LINK", "EXPLICIT_WS_DOCUMENTATION_LINK"}
    ]
    diagnostics = {
        "initial_page_count": min(len(config["initial_urls"]), int(config["limits"]["max_initial_pages"])),
        "fetched_page_count": len(pages),
        "followed_documentation_count": followed_count,
        "fetch_failure_count": len(fetch_failures),
        "fetch_failures": fetch_failures[:12],
        "total_fetched_bytes": total_bytes,
        "page_summaries": pages[:16],
        "declared_signal_link_count": len(observed_links),
        "explicit_candidate_count": len(candidates),
    }

    common = {
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "endpoint_candidate_network_sent": False,
        "form_submission": False,
        "captcha_bypass": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "artifact_downloaded": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }

    if not candidates:
        raise SiopeWsPublicDiscoveryError(
            f"{ERROR}_NO_EXPLICIT_ENDPOINT_OR_DOCUMENTATION",
            diagnostics={**diagnostics, **common, "next_gate": config["next_gate_if_failure"]},
        )

    return {
        "status": "PASS_M7_SIOPE_WS_PUBLIC_DISCOVERY_GATE",
        "discovery_status": "EXPLICIT_PUBLIC_WS_SIOPE_ENDPOINT_OR_DOCUMENTATION_OBSERVED",
        **common,
        **diagnostics,
        "candidates": candidates[:12],
        "next_gate": config["next_gate_if_success"],
    }
