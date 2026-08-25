from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import json
import re
import socket
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


class SiopeDownloadRouteDiscoveryError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


@dataclass(frozen=True)
class TextResponse:
    url: str
    status: int
    content_type: str
    body: str
    byte_count: int


class ReadOnlyDeclaredResourceClient:
    def __init__(self, *, allowed_hosts: tuple[str, ...], opener=urlopen):
        self.allowed_hosts = allowed_hosts
        self.opener = opener

    def get_text(self, url: str, *, max_bytes: int, allowed_content_types: tuple[str, ...]) -> TextResponse:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_HOST_NOT_ALLOWED")
        req = Request(
            url,
            headers={
                "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 (+public-transparency-research)",
                "Accept": "text/html,application/xhtml+xml,text/javascript,application/javascript,*/*;q=0.1",
            },
            method="GET",
        )
        try:
            response = self.opener(req, timeout=15)
            with response:
                final_url = str(getattr(response, "url", response.geturl()))
                final = urlparse(final_url)
                if final.scheme != "https" or final.hostname not in self.allowed_hosts:
                    raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_REDIRECT_HOST_NOT_ALLOWED")
                status = int(getattr(response, "status", response.getcode()))
                content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
                raw = response.read(max_bytes + 1)
        except SiopeDownloadRouteDiscoveryError:
            raise
        except HTTPError as exc:
            raise SiopeDownloadRouteDiscoveryError(f"STOP_SIOPE_DOWNLOAD_ROUTE_HTTP_{exc.code}") from None
        except (TimeoutError, socket.timeout):
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_TIMEOUT") from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
                raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_TIMEOUT") from None
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_NETWORK") from None
        except OSError:
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_NETWORK") from None

        if len(raw) > max_bytes:
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_RESPONSE_TOO_LARGE")
        if status != 200:
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_HTTP_STATUS")
        if content_type not in set(allowed_content_types):
            raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONTENT_TYPE")
        return TextResponse(final_url, status, content_type, raw.decode("utf-8", errors="replace"), len(raw))


def _validate_config(config: dict) -> None:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_ANTONIETA_DOWNLOAD_ROUTE_DISCOVERY_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "PASSIVE_DOWNLOAD_ROUTE_DISCOVERY_ONLY",
        "network": "READ_ONLY_GET_PAGE_AND_DECLARED_SCRIPTS",
        "remote_writes": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "head_request": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "next_gate": "M7_SIOPE_ANTONIETA_ARTIFACT_VERIFICATION_GATE_0_8_0",
    }
    for key, value in exact.items():
        if config.get(key) != value:
            raise SiopeDownloadRouteDiscoveryError(f"STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_{key.upper()}")
    if config.get("allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_ALLOWED_HOSTS")
    if config.get("max_page_bytes") != 2097152:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_MAX_PAGE_BYTES")
    if config.get("max_script_bytes") != 1048576:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_MAX_SCRIPT_BYTES")
    if config.get("max_scripts") != 8:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_MAX_SCRIPTS")
    if config.get("max_total_script_bytes") != 6291456:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_MAX_TOTAL_SCRIPT_BYTES")
    page = urlparse(str(config.get("page_url", "")))
    if page.scheme != "https" or page.hostname != "www.fnde.gov.br":
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_PAGE_URL")
    if config.get("required_product_name") != "Dados Gerais - SIOPE":
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_PRODUCT")
    if config.get("required_artifact_path") != "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz":
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_ARTIFACT")
    if config.get("candidate_keywords") != ["download", "export", "artefato", "artifact"]:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_CONFIG_KEYWORDS")


def load_download_route_discovery_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def extract_declared_script_urls(html: str, *, page_url: str, allowed_hosts: tuple[str, ...], max_scripts: int) -> tuple[str, ...]:
    found: list[str] = []
    for value in re.findall(r"<script\b[^>]*\bsrc\s*=\s*['\"]([^'\"]+)['\"]", html, flags=re.IGNORECASE):
        absolute = urljoin(page_url, unescape(value))
        parsed = urlparse(absolute)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            continue
        if not parsed.path.lower().endswith(".js"):
            continue
        if absolute not in found:
            found.append(absolute)
        if len(found) >= max_scripts:
            break
    return tuple(found)


def summarize_public_page_markers(html: str) -> dict:
    lower = html.lower()
    inline_scripts = re.findall(
        r"<script\b(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script\s*>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    event_attrs = re.findall(
        r"\bon[a-z]+\s*=\s*['\"]([^'\"]*)['\"]",
        html,
        flags=re.IGNORECASE,
    )
    data_attrs = re.findall(
        r"\bdata-[a-z0-9_-]+\s*=\s*['\"]([^'\"]*)['\"]",
        html,
        flags=re.IGNORECASE,
    )
    href_action_attrs = re.findall(
        r"\b(?:href|action)\s*=\s*['\"]([^'\"]*)['\"]",
        html,
        flags=re.IGNORECASE,
    )
    export_terms = ("download", "export", "artefato", "artifact")
    return {
        "export_label_present": "exportar artefato" in lower,
        "inline_script_count": len(inline_scripts),
        "inline_script_export_marker_count": sum(
            1 for value in inline_scripts if any(term in value.lower() for term in export_terms)
        ),
        "inline_event_attribute_count": len(event_attrs),
        "inline_event_export_marker_count": sum(
            1 for value in event_attrs if any(term in value.lower() for term in export_terms)
        ),
        "data_attribute_count": len(data_attrs),
        "data_attribute_export_marker_count": sum(
            1 for value in data_attrs if any(term in value.lower() for term in export_terms)
        ),
        "href_action_count": len(href_action_attrs),
        "href_action_export_marker_count": sum(
            1 for value in href_action_attrs if any(term in value.lower() for term in export_terms)
        ),
    }


def _sanitize_public_candidate(url: str) -> dict:
    parsed = urlparse(url)
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return {
        "url_without_query": clean,
        "query_present": bool(parsed.query),
        "fragment_present": bool(parsed.fragment),
    }


def _quoted_strings(text: str) -> tuple[str, ...]:
    values: list[str] = []
    for value in re.findall(r"['\"]([^'\"\n\r]{1,600})['\"]", text):
        decoded = unescape(value.replace("\\/", "/"))
        if decoded not in values:
            values.append(decoded)
    return tuple(values)


def extract_explicit_download_route_candidates(
    text: str,
    *,
    base_url: str,
    allowed_hosts: tuple[str, ...],
    artifact_basename: str,
    keywords: tuple[str, ...],
) -> tuple[dict, ...]:
    candidates: list[dict] = []
    seen: set[str] = set()
    for literal in _quoted_strings(text):
        lower = literal.lower()
        has_artifact = artifact_basename.lower() in lower
        has_keyword = any(word in lower for word in keywords)
        if not (has_artifact or has_keyword):
            continue
        if not (literal.startswith("https://") or literal.startswith("/") or literal.startswith("./") or literal.startswith("../")):
            continue
        absolute = urljoin(base_url, literal)
        parsed = urlparse(absolute)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            continue
        if parsed.path.lower().endswith(".js"):
            continue
        sanitized = _sanitize_public_candidate(absolute)
        key = sanitized["url_without_query"] + ("?" if sanitized["query_present"] else "")
        if key in seen:
            continue
        seen.add(key)
        strength = "ARTIFACT_LITERAL" if has_artifact else "DOWNLOAD_KEYWORD_LITERAL"
        candidates.append({**sanitized, "evidence_strength": strength})
    return tuple(candidates)


def discover_download_route(config: dict, *, client: ReadOnlyDeclaredResourceClient | None = None) -> dict:
    _validate_config(config)
    allowed_hosts = tuple(config["allowed_hosts"])
    client = client or ReadOnlyDeclaredResourceClient(allowed_hosts=allowed_hosts)
    page = client.get_text(
        config["page_url"],
        max_bytes=int(config["max_page_bytes"]),
        allowed_content_types=("text/html", "application/xhtml+xml"),
    )
    if config["required_product_name"] not in page.body:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_PRODUCT_NOT_VERIFIED")
    if config["required_artifact_path"] not in page.body:
        raise SiopeDownloadRouteDiscoveryError("STOP_SIOPE_DOWNLOAD_ROUTE_ARTIFACT_NOT_DECLARED")

    page_markers = summarize_public_page_markers(page.body)
    script_urls = extract_declared_script_urls(
        page.body,
        page_url=page.url,
        allowed_hosts=allowed_hosts,
        max_scripts=int(config["max_scripts"]),
    )
    artifact_basename = config["required_artifact_path"].rsplit("/", 1)[-1]
    keywords = tuple(config["candidate_keywords"])
    all_candidates = list(
        extract_explicit_download_route_candidates(
            page.body,
            base_url=page.url,
            allowed_hosts=allowed_hosts,
            artifact_basename=artifact_basename,
            keywords=keywords,
        )
    )

    script_failures: list[dict] = []
    fetched_scripts = 0
    total_script_bytes = 0
    for script_index, script_url in enumerate(script_urls, start=1):
        if total_script_bytes >= int(config["max_total_script_bytes"]):
            break
        remaining = int(config["max_total_script_bytes"]) - total_script_bytes
        limit = min(int(config["max_script_bytes"]), remaining)
        try:
            script = client.get_text(
                script_url,
                max_bytes=limit,
                allowed_content_types=("text/javascript", "application/javascript", "application/x-javascript", "text/plain"),
            )
        except SiopeDownloadRouteDiscoveryError as exc:
            script_failures.append({"script_index": script_index, "reason": str(exc)})
            continue
        fetched_scripts += 1
        total_script_bytes += script.byte_count
        all_candidates.extend(
            extract_explicit_download_route_candidates(
                script.body,
                base_url=script.url,
                allowed_hosts=allowed_hosts,
                artifact_basename=artifact_basename,
                keywords=keywords,
            )
        )

    unique: list[dict] = []
    keys: set[str] = set()
    for item in all_candidates:
        key = item["url_without_query"] + ("?" if item["query_present"] else "")
        if key not in keys:
            keys.add(key)
            unique.append(item)

    diagnostics = {
        "page_verified": True,
        "artifact_declared": True,
        "page_bytes": page.byte_count,
        "declared_script_count": len(script_urls),
        "fetched_script_count": fetched_scripts,
        "script_failure_count": len(script_failures),
        "script_failures": script_failures,
        "total_fetched_script_bytes": total_script_bytes,
        "page_markers": page_markers,
        "route_candidate_count": len(unique),
    }

    if not unique:
        raise SiopeDownloadRouteDiscoveryError(
            "STOP_SIOPE_DOWNLOAD_ROUTE_NOT_EXPLICITLY_DISCOVERED",
            diagnostics=diagnostics,
        )

    return {
        "status": "PASS_M7_SIOPE_DOWNLOAD_ROUTE_DISCOVERY_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "network_called": True,
        "network_method": "GET_ONLY",
        **diagnostics,
        "route_candidates": unique[:12],
        "artifact_downloaded": False,
        "head_request_performed": False,
        "form_submission": False,
        "captcha_bypass": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "acquisition_route_status": "EXPLICIT_ROUTE_CANDIDATE_NOT_FETCHED",
        "next_gate": config["next_gate"],
    }
