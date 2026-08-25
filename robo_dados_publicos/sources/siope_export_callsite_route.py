from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from robo_dados_publicos.sources.siope_download_route_discovery import (
    ReadOnlyDeclaredResourceClient,
    SiopeDownloadRouteDiscoveryError,
    extract_declared_script_urls,
)


class SiopeExportCallsiteRouteError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_config(config: dict) -> None:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_ANTONIETA_EXPORT_CALLSITE_ROUTE_DISCOVERY_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "PASSIVE_EXPORT_CALLSITE_ROUTE_DISCOVERY_ONLY",
        "network": "READ_ONLY_GET_PAGE_AND_DECLARED_SCRIPTS",
        "remote_writes": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "candidate_route_request": "PROHIBITED",
        "head_request": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "browser_automation": "PROHIBITED",
        "click_execution": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "callsite_window_chars": 2400,
        "max_callsites_per_identifier": 8,
        "max_total_callsites": 24,
        "max_page_bytes": 2097152,
        "max_script_bytes": 1048576,
        "max_scripts": 8,
        "max_total_script_bytes": 6291456,
        "next_gate_if_route_candidate": "M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0",
        "next_gate_if_route_unproven": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopeExportCallsiteRouteError(f"STOP_SIOPE_EXPORT_CALLSITE_CONFIG_{key.upper()}")
    if config.get("allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_CONFIG_ALLOWED_HOSTS")
    if config.get("target_identifiers") != [
        "getArtifactByDataProductId",
        "getArtifactMetadataByDataProductId",
        "downloadFile",
        "exportKey",
    ]:
        raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_CONFIG_IDENTIFIERS")
    page = urlparse(str(config.get("page_url", "")))
    if page.scheme != "https" or page.hostname != "www.fnde.gov.br":
        raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_CONFIG_PAGE_URL")
    if config.get("required_product_name") != "Dados Gerais - SIOPE":
        raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_CONFIG_PRODUCT")
    if config.get("required_artifact_path") != "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz":
        raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_CONFIG_ARTIFACT")


def load_export_callsite_route_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _literal_strings(text: str) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    pattern = re.compile(r"(?P<q>['\"`])(?P<body>(?:\\.|(?!\1).){1,600}?)\1", flags=re.DOTALL)
    for match in pattern.finditer(text):
        quote = match.group("q")
        body = match.group("body").replace("\\/", "/")
        values.append(("TEMPLATE_LITERAL" if quote == "`" else "QUOTED_LITERAL", body))
    return tuple(values)


def _is_route_like(value: str) -> bool:
    value = value.strip()
    lower = value.lower()
    if value.startswith(("https://", "/", "./", "../")):
        return True
    return lower.startswith(("api/", "rest/", "download/", "downloads/", "export/", "exports/", "artifact/", "artifacts/", "artefato/", "artefatos/"))


def _sanitize_route(value: str, *, base_url: str, allowed_hosts: tuple[str, ...]) -> dict | None:
    value = value.strip()
    if not _is_route_like(value):
        return None
    if value.lower().startswith(("api/", "rest/", "download/", "downloads/", "export/", "exports/", "artifact/", "artifacts/", "artefato/", "artefatos/")):
        value = "./" + value
    normalized = re.sub(r"\$\{[^}]{1,200}\}", "{VAR}", value)
    absolute = urljoin(base_url, normalized)
    parsed = urlparse(absolute)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return None
    path = parsed.path
    if not path or len(path) > 360:
        return None
    if re.search(r"\.(?:js|css|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|map)$", path, flags=re.IGNORECASE):
        return None
    clean = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
    return {
        "route_without_query": clean,
        "dynamic": "{VAR}" in clean,
        "query_present": bool(parsed.query),
    }


def _http_mechanisms(window: str) -> dict:
    return {
        "fetch": len(re.findall(r"\bfetch\s*\(", window, flags=re.IGNORECASE)),
        "xmlhttprequest": len(re.findall(r"\bXMLHttpRequest\b", window)),
        "window_open": len(re.findall(r"\bwindow\s*\.\s*open\s*\(", window, flags=re.IGNORECASE)),
        "location_navigation": len(re.findall(r"(?:\bwindow\s*\.\s*)?\blocation\s*(?:\.\s*(?:href|assign|replace))?\s*(?:=|\()", window, flags=re.IGNORECASE)),
        "get_call": len(re.findall(r"\.\s*get\s*\(", window, flags=re.IGNORECASE)),
        "post_call": len(re.findall(r"\.\s*post\s*\(", window, flags=re.IGNORECASE)),
    }


def analyze_callsites(
    text: str,
    *,
    source_kind: str,
    source_index: int,
    base_url: str,
    allowed_hosts: tuple[str, ...],
    identifiers: tuple[str, ...],
    window_chars: int,
    max_per_identifier: int,
    max_total: int,
) -> tuple[dict, ...]:
    observations: list[dict] = []
    seen_routes: set[tuple[str, str]] = set()
    for identifier in identifiers:
        positions = [match.start() for match in re.finditer(re.escape(identifier), text)]
        for position in positions[:max_per_identifier]:
            start = max(0, position - window_chars)
            end = min(len(text), position + len(identifier) + window_chars)
            window = text[start:end]
            routes: list[dict] = []
            for literal_kind, literal in _literal_strings(window):
                candidate = _sanitize_route(literal, base_url=base_url, allowed_hosts=allowed_hosts)
                if candidate is None:
                    continue
                key = (identifier, candidate["route_without_query"])
                if key in seen_routes:
                    continue
                seen_routes.add(key)
                routes.append({**candidate, "literal_kind": literal_kind})
                if len(routes) >= 10:
                    break
            observations.append({
                "source_kind": source_kind,
                "source_index": source_index,
                "identifier": identifier,
                "route_candidates": routes,
                "mechanisms": _http_mechanisms(window),
            })
            if len(observations) >= max_total:
                return tuple(observations)
    return tuple(observations)


def _inline_scripts(html: str) -> tuple[str, ...]:
    return tuple(re.findall(r"<script\b(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script\s*>", html, flags=re.IGNORECASE | re.DOTALL))


def discover_export_callsite_routes(config: dict, *, client: ReadOnlyDeclaredResourceClient | None = None) -> dict:
    _validate_config(config)
    allowed_hosts = tuple(config["allowed_hosts"])
    client = client or ReadOnlyDeclaredResourceClient(allowed_hosts=allowed_hosts)
    try:
        page = client.get_text(
            config["page_url"],
            max_bytes=int(config["max_page_bytes"]),
            allowed_content_types=("text/html", "application/xhtml+xml"),
        )
    except SiopeDownloadRouteDiscoveryError as exc:
        raise SiopeExportCallsiteRouteError(str(exc)) from None

    if config["required_product_name"] not in page.body:
        raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_PRODUCT_NOT_VERIFIED")
    if config["required_artifact_path"] not in page.body:
        raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_ARTIFACT_NOT_DECLARED")

    identifiers = tuple(config["target_identifiers"])
    kwargs = dict(
        base_url=config["page_url"],
        allowed_hosts=allowed_hosts,
        identifiers=identifiers,
        window_chars=int(config["callsite_window_chars"]),
        max_per_identifier=int(config["max_callsites_per_identifier"]),
        max_total=int(config["max_total_callsites"]),
    )

    observations: list[dict] = []
    for index, body in enumerate(_inline_scripts(page.body), start=1):
        observations.extend(analyze_callsites(body, source_kind="INLINE_SCRIPT", source_index=index, **kwargs))
        if len(observations) >= int(config["max_total_callsites"]):
            break

    declared_scripts = extract_declared_script_urls(page.body, base_url=config["page_url"], allowed_hosts=allowed_hosts)
    if len(declared_scripts) > int(config["max_scripts"]):
        declared_scripts = declared_scripts[: int(config["max_scripts"])]

    fetched = 0
    total_script_bytes = 0
    script_failures: list[str] = []
    for index, script_url in enumerate(declared_scripts, start=1):
        try:
            response = client.get_text(
                script_url,
                max_bytes=int(config["max_script_bytes"]),
                allowed_content_types=("application/javascript", "text/javascript", "application/x-javascript", "text/plain"),
            )
        except SiopeDownloadRouteDiscoveryError as exc:
            script_failures.append(str(exc))
            continue
        fetched += 1
        total_script_bytes += response.byte_count
        if total_script_bytes > int(config["max_total_script_bytes"]):
            raise SiopeExportCallsiteRouteError("STOP_SIOPE_EXPORT_CALLSITE_TOTAL_SCRIPT_BYTES")
        remaining = int(config["max_total_callsites"]) - len(observations)
        if remaining <= 0:
            break
        local_kwargs = dict(kwargs)
        local_kwargs["max_total"] = remaining
        observations.extend(analyze_callsites(response.body, source_kind="DECLARED_EXTERNAL_SCRIPT", source_index=index, **local_kwargs))

    if not observations:
        raise SiopeExportCallsiteRouteError(
            "STOP_SIOPE_EXPORT_CALLSITE_TARGET_IDENTIFIERS_NOT_OBSERVED",
            diagnostics={
                "declared_script_count": len(declared_scripts),
                "fetched_script_count": fetched,
                "script_failure_count": len(script_failures),
            },
        )

    route_candidates: list[dict] = []
    seen: set[str] = set()
    identifiers_observed: set[str] = set()
    for item in observations:
        identifiers_observed.add(item["identifier"])
        for route in item["route_candidates"]:
            key = route["route_without_query"]
            if key in seen:
                continue
            seen.add(key)
            route_candidates.append({
                "route_without_query": key,
                "dynamic": route["dynamic"],
                "query_present": route["query_present"],
                "literal_kind": route["literal_kind"],
                "evidence_identifier": item["identifier"],
                "source_kind": item["source_kind"],
                "source_index": item["source_index"],
            })
            if len(route_candidates) >= 16:
                break

    route_proven = bool(route_candidates)
    return {
        "status": "PASS_M7_SIOPE_EXPORT_CALLSITE_ROUTE_DISCOVERY_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "page_verified": True,
        "artifact_declared": True,
        "page_bytes": page.byte_count,
        "declared_script_count": len(declared_scripts),
        "fetched_script_count": fetched,
        "script_failure_count": len(script_failures),
        "script_failures": script_failures,
        "total_fetched_script_bytes": total_script_bytes,
        "callsite_count": len(observations),
        "identifiers_observed": sorted(identifiers_observed),
        "route_candidate_count": len(route_candidates),
        "route_candidates": route_candidates,
        "callsite_route_status": "CALLSITE_ROUTE_CANDIDATE_OBSERVED_NOT_CALLED" if route_proven else "EXPORT_CALLSITE_OBSERVED_ROUTE_UNPROVEN",
        "next_gate": config["next_gate_if_route_candidate"] if route_proven else config["next_gate_if_route_unproven"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "candidate_route_requested": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "form_submission": False,
        "browser_automation_performed": False,
        "click_executed": False,
        "captcha_bypass": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
