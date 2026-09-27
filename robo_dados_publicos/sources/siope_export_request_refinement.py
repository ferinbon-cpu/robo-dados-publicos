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


class SiopeExportRequestRefinementError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_config(config: dict) -> None:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_ANTONIETA_EXPORT_REQUEST_EXPRESSION_REFINEMENT_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "PASSIVE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_ONLY",
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
        "context_window_chars": 1400,
        "max_contexts_per_identifier": 6,
        "max_total_contexts": 20,
        "max_page_bytes": 2097152,
        "max_script_bytes": 1048576,
        "max_scripts": 8,
        "max_total_script_bytes": 6291456,
        "next_gate_if_unique_request_route": "M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0",
        "next_gate_if_ambiguous_or_unproven": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopeExportRequestRefinementError(f"STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_CONFIG_{key.upper()}")
    if config.get("allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_CONFIG_ALLOWED_HOSTS")
    if config.get("target_identifiers") != [
        "getArtifactByDataProductId",
        "getArtifactMetadataByDataProductId",
        "downloadFile",
        "exportKey",
    ]:
        raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_CONFIG_IDENTIFIERS")
    page = urlparse(str(config.get("page_url", "")))
    if page.scheme != "https" or page.hostname != "www.fnde.gov.br":
        raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_CONFIG_PAGE_URL")
    if config.get("required_product_name") != "Dados Gerais - SIOPE":
        raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_CONFIG_PRODUCT")
    if config.get("required_artifact_path") != "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz":
        raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_CONFIG_ARTIFACT")


def load_export_request_refinement_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _inline_scripts(html: str) -> tuple[str, ...]:
    return tuple(re.findall(
        r"<script\b(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script\s*>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ))


def _context_windows(
    text: str,
    *,
    identifiers: tuple[str, ...],
    window_chars: int,
    max_per_identifier: int,
    max_total: int,
) -> tuple[tuple[str, str], ...]:
    results: list[tuple[str, str]] = []
    seen: set[tuple[int, int]] = set()
    for identifier in identifiers:
        positions = [match.start() for match in re.finditer(re.escape(identifier), text)]
        for position in positions[:max_per_identifier]:
            start = max(0, position - window_chars)
            end = min(len(text), position + len(identifier) + window_chars)
            key = (start, end)
            if key in seen:
                continue
            seen.add(key)
            results.append((identifier, text[start:end]))
            if len(results) >= max_total:
                return tuple(results)
    return tuple(results)


def _normalize_literal(
    literal_body: str,
    *,
    base_url: str,
    allowed_hosts: tuple[str, ...],
) -> dict | None:
    value = literal_body.replace("\\/", "/").strip()
    value = re.sub(r"\$\{[^}]{1,240}\}", "{VAR}", value)
    lower = value.lower()
    if lower.startswith("http://"):
        return None
    if not value.startswith(("https://", "/", "./", "../")):
        if lower.startswith(("api/", "rest/", "artifact/", "artifacts/", "artefato/", "artefatos/", "download/", "downloads/", "export/", "exports/")):
            value = "./" + value
        else:
            return None
    absolute = urljoin(base_url, value)
    parsed = urlparse(absolute)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return None
    if not parsed.path or len(parsed.path) > 420:
        return None
    if re.search(r"\.(?:js|css|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|map)$", parsed.path, flags=re.IGNORECASE):
        return None
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return {
        "route_without_query": clean,
        "path": parsed.path,
        "dynamic": "{VAR}" in clean,
        "query_present": bool(parsed.query),
    }


def _literal_call_matches(context: str) -> tuple[dict, ...]:
    matches: list[dict] = []
    patterns = (
        ("FETCH_ARGUMENT", "GET_OR_DECLARED_BY_FETCH", re.compile(r"\bfetch\s*\(\s*(?P<q>['\"`])(?P<body>(?:\\.|(?!\1).){1,500}?)\1", re.IGNORECASE | re.DOTALL)),
        ("HTTP_METHOD_ARGUMENT", "HTTP_METHOD", re.compile(r"(?:\baxios\s*\.\s*|\.\s*)(?P<method>get|post|put|patch|delete)\s*\(\s*(?P<q>['\"`])(?P<body>(?:\\.|(?!\2).){1,500}?)\2", re.IGNORECASE | re.DOTALL)),
    )
    for binding, default_method, pattern in patterns:
        for match in pattern.finditer(context):
            method = match.groupdict().get("method") or default_method
            matches.append({
                "binding": binding,
                "method": str(method).upper(),
                "literal_body": match.group("body"),
            })
    return tuple(matches)


def _field_literal_matches(context: str) -> tuple[dict, ...]:
    matches: list[dict] = []
    pattern = re.compile(
        r"\b(?P<field>baseURL|baseUrl|url)\s*[:=]\s*(?P<q>['\"`])(?P<body>(?:\\.|(?!\2).){1,500}?)\2",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(context):
        field = match.group("field").lower()
        matches.append({
            "binding": "BASE_URL_FIELD" if field == "baseurl" else "REQUEST_URL_FIELD",
            "method": "CONFIG",
            "literal_body": match.group("body"),
        })
    return tuple(matches)


def _resolved_variable_call_matches(context: str) -> tuple[dict, ...]:
    assignments: dict[str, tuple[str, str]] = {}
    assign_pattern = re.compile(
        r"\b(?:const|let|var)\s+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?P<q>['\"`])(?P<body>(?:\\.|(?!\2).){1,500}?)\2",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in assign_pattern.finditer(context):
        assignments[match.group("name")] = (match.group("q"), match.group("body"))

    results: list[dict] = []
    call_pattern = re.compile(
        r"(?:\bfetch|(?:\baxios\s*\.\s*|\.\s*)(?P<method>get|post|put|patch|delete))\s*\(\s*(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)",
        flags=re.IGNORECASE,
    )
    for match in call_pattern.finditer(context):
        name = match.group("name")
        if name not in assignments:
            continue
        _quote, body = assignments[name]
        results.append({
            "binding": "RESOLVED_VARIABLE_REQUEST_ARGUMENT",
            "method": str(match.groupdict().get("method") or "FETCH").upper(),
            "literal_body": body,
        })
    return tuple(results)


def analyze_request_context(
    context: str,
    *,
    evidence_identifier: str,
    source_kind: str,
    source_index: int,
    base_url: str,
    allowed_hosts: tuple[str, ...],
) -> dict:
    raw = [*_literal_call_matches(context), *_field_literal_matches(context), *_resolved_variable_call_matches(context)]
    candidates: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        normalized = _normalize_literal(item["literal_body"], base_url=base_url, allowed_hosts=allowed_hosts)
        if normalized is None:
            continue
        key = (item["binding"], normalized["route_without_query"])
        if key in seen:
            continue
        seen.add(key)
        candidates.append({
            "binding": item["binding"],
            "method": item["method"],
            **normalized,
        })

    bases = [item for item in candidates if item["binding"] == "BASE_URL_FIELD"]
    directs = [item for item in candidates if item["binding"] in {"FETCH_ARGUMENT", "HTTP_METHOD_ARGUMENT", "REQUEST_URL_FIELD", "RESOLVED_VARIABLE_REQUEST_ARGUMENT"}]
    composed: list[dict] = []
    composed_seen: set[str] = set()
    for base in bases:
        base_parsed = urlparse(base["route_without_query"])
        base_prefix = urlunparse((base_parsed.scheme, base_parsed.netloc, base_parsed.path.rstrip("/"), "", "", ""))
        for direct in directs:
            path = direct["path"]
            if path == base_parsed.path:
                continue
            route = base_prefix + "/" + path.lstrip("/")
            if route in composed_seen:
                continue
            composed_seen.add(route)
            composed.append({
                "route_without_query": route,
                "dynamic": direct["dynamic"],
                "query_present": direct["query_present"],
                "evidence": "BASE_URL_PLUS_DIRECT_REQUEST_EXPRESSION",
                "method": direct["method"],
            })

    return {
        "evidence_identifier": evidence_identifier,
        "source_kind": source_kind,
        "source_index": source_index,
        "request_candidate_count": len(candidates),
        "request_candidates": candidates[:12],
        "composed_candidate_count": len(composed),
        "composed_candidates": composed[:8],
    }


def refine_export_request_expressions(config: dict, *, client: ReadOnlyDeclaredResourceClient | None = None) -> dict:
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
        raise SiopeExportRequestRefinementError(str(exc)) from None

    if config["required_product_name"] not in page.body:
        raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_PRODUCT_NOT_VERIFIED")
    if config["required_artifact_path"] not in page.body:
        raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_ARTIFACT_NOT_DECLARED")

    identifiers = tuple(config["target_identifiers"])
    contexts: list[dict] = []

    def add_contexts(text: str, *, source_kind: str, source_index: int) -> None:
        remaining = int(config["max_total_contexts"]) - len(contexts)
        if remaining <= 0:
            return
        for identifier, window in _context_windows(
            text,
            identifiers=identifiers,
            window_chars=int(config["context_window_chars"]),
            max_per_identifier=int(config["max_contexts_per_identifier"]),
            max_total=remaining,
        ):
            contexts.append(analyze_request_context(
                window,
                evidence_identifier=identifier,
                source_kind=source_kind,
                source_index=source_index,
                base_url=config["page_url"],
                allowed_hosts=allowed_hosts,
            ))

    for index, body in enumerate(_inline_scripts(page.body), start=1):
        add_contexts(body, source_kind="INLINE_SCRIPT", source_index=index)
        if len(contexts) >= int(config["max_total_contexts"]):
            break

    declared_scripts = extract_declared_script_urls(
        page.body,
        page_url=page.url,
        allowed_hosts=allowed_hosts,
        max_scripts=int(config["max_scripts"]),
    )
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
            raise SiopeExportRequestRefinementError("STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_TOTAL_SCRIPT_BYTES")
        add_contexts(response.body, source_kind="DECLARED_EXTERNAL_SCRIPT", source_index=index)
        if len(contexts) >= int(config["max_total_contexts"]):
            break

    observed_identifiers = sorted({item["evidence_identifier"] for item in contexts})
    if not observed_identifiers:
        raise SiopeExportRequestRefinementError(
            "STOP_SIOPE_EXPORT_REQUEST_REFINEMENT_TARGET_IDENTIFIERS_NOT_OBSERVED",
            diagnostics={
                "declared_script_count": len(declared_scripts),
                "fetched_script_count": fetched,
                "script_failure_count": len(script_failures),
            },
        )

    direct_routes: dict[str, dict] = {}
    composed_routes: dict[str, dict] = {}
    for context in contexts:
        for candidate in context["request_candidates"]:
            if candidate["binding"] == "BASE_URL_FIELD":
                continue
            direct_routes.setdefault(candidate["route_without_query"], {
                "route_without_query": candidate["route_without_query"],
                "dynamic": candidate["dynamic"],
                "query_present": candidate["query_present"],
                "binding": candidate["binding"],
                "method": candidate["method"],
                "evidence_identifier": context["evidence_identifier"],
            })
        for candidate in context["composed_candidates"]:
            composed_routes.setdefault(candidate["route_without_query"], {
                **candidate,
                "evidence_identifier": context["evidence_identifier"],
            })

    preferred = list(composed_routes.values()) or list(direct_routes.values())
    if len(preferred) == 1:
        status = "UNIQUE_REQUEST_ROUTE_EXPRESSION_OBSERVED_NOT_CALLED"
        next_gate = config["next_gate_if_unique_request_route"]
    elif preferred:
        status = "REQUEST_ROUTE_EXPRESSIONS_OBSERVED_AMBIGUOUS_NOT_CALLED"
        next_gate = config["next_gate_if_ambiguous_or_unproven"]
    else:
        status = "EXPORT_REQUEST_CONTEXT_OBSERVED_ROUTE_UNPROVEN"
        next_gate = config["next_gate_if_ambiguous_or_unproven"]

    return {
        "status": "PASS_M7_SIOPE_EXPORT_REQUEST_EXPRESSION_REFINEMENT_GATE",
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
        "context_count": len(contexts),
        "identifiers_observed": observed_identifiers,
        "direct_request_route_count": len(direct_routes),
        "direct_request_routes": list(direct_routes.values())[:12],
        "composed_request_route_count": len(composed_routes),
        "composed_request_routes": list(composed_routes.values())[:8],
        "refinement_status": status,
        "next_gate": next_gate,
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
