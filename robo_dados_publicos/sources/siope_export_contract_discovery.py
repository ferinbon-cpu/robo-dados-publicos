from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

from robo_dados_publicos.sources.siope_download_route_discovery import (
    ReadOnlyDeclaredResourceClient,
    SiopeDownloadRouteDiscoveryError,
    extract_declared_script_urls,
)


class SiopeExportContractDiscoveryError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


@dataclass(frozen=True)
class ScriptSignals:
    source_kind: str
    source_index: int
    byte_count: int
    keyword_present: bool
    artifact_reference_present: bool
    mechanisms: dict
    dataset_keys: tuple[str, ...]
    data_attribute_names: tuple[str, ...]
    export_identifiers: tuple[str, ...]
    route_templates: tuple[dict, ...]


def _validate_config(config: dict) -> None:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_ANTONIETA_EXPORT_CONTRACT_DISCOVERY_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "PASSIVE_EXPORT_CONTRACT_DISCOVERY_ONLY",
        "network": "READ_ONLY_GET_PAGE_AND_DECLARED_SCRIPTS",
        "remote_writes": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "head_request": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "browser_automation": "PROHIBITED",
        "click_execution": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "next_gate": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_0_8_0",
    }
    for key, value in exact.items():
        if config.get(key) != value:
            raise SiopeExportContractDiscoveryError(f"STOP_SIOPE_EXPORT_CONTRACT_CONFIG_{key.upper()}")
    if config.get("allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_ALLOWED_HOSTS")
    if config.get("max_page_bytes") != 2097152:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_MAX_PAGE_BYTES")
    if config.get("max_script_bytes") != 1048576:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_MAX_SCRIPT_BYTES")
    if config.get("max_scripts") != 8:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_MAX_SCRIPTS")
    if config.get("max_total_script_bytes") != 6291456:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_MAX_TOTAL_SCRIPT_BYTES")
    page = urlparse(str(config.get("page_url", "")))
    if page.scheme != "https" or page.hostname != "www.fnde.gov.br":
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_PAGE_URL")
    if config.get("required_product_name") != "Dados Gerais - SIOPE":
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_PRODUCT")
    if config.get("required_artifact_path") != "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz":
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_ARTIFACT")
    if config.get("candidate_keywords") != ["download", "export", "artefato", "artifact"]:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_CONFIG_KEYWORDS")


def load_export_contract_discovery_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _attribute_pairs(opening_tag: str) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    pattern = re.compile(
        r"(?<![A-Za-z0-9_:-])([A-Za-z_:][A-Za-z0-9_:.-]*)(?:\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+)))?",
        flags=re.IGNORECASE,
    )
    first = True
    for match in pattern.finditer(opening_tag):
        if first:
            first = False
            continue
        name = match.group(1).lower()
        value = next((v for v in match.groups()[1:] if v is not None), "")
        pairs.append((name, unescape(value)))
    return tuple(pairs)


def _classify_public_value(value: str, *, artifact_basename: str, keywords: tuple[str, ...]) -> str:
    lower = value.lower().strip()
    if artifact_basename.lower() in lower:
        return "ARTIFACT_REFERENCE"
    if lower.startswith("https://"):
        return "ABSOLUTE_HTTPS_REFERENCE"
    if lower.startswith(("/", "./", "../")):
        return "RELATIVE_REFERENCE"
    if re.fullmatch(r"[0-9]{1,18}", lower):
        return "NUMERIC_IDENTIFIER"
    if re.fullmatch(r"[#.]?[A-Za-z_][A-Za-z0-9_.:-]{0,119}", value.strip()):
        if any(word in lower for word in keywords):
            return "EXPORT_IDENTIFIER"
        return "SIMPLE_IDENTIFIER"
    if any(word in lower for word in keywords):
        return "EXPORT_LABEL_OR_EXPRESSION"
    return "OTHER_PUBLIC_VALUE"


def _safe_public_value(value: str) -> str | None:
    value = value.strip()
    lower = value.lower()
    if not value or len(value) > 180:
        return None
    if any(term in lower for term in ("token", "secret", "authorization", "signature", "session", "password", "passwd", "apikey", "api_key")):
        return None
    if "?" in value or "&" in value:
        return None
    if re.fullmatch(r"[A-Za-z0-9_./:#${}()\[\], -]{1,180}", value):
        return value
    return None


def summarize_export_controls(
    html: str,
    *,
    artifact_basename: str,
    keywords: tuple[str, ...],
) -> tuple[dict, ...]:
    observations: list[dict] = []
    for match in re.finditer(r"<([A-Za-z][A-Za-z0-9:-]*)\b([^>]*)>", html, flags=re.IGNORECASE | re.DOTALL):
        tag_name = match.group(1).lower()
        opening = match.group(0)
        attrs = _attribute_pairs(opening)
        data_matches: list[dict] = []
        for name, value in attrs:
            if not name.startswith("data-"):
                continue
            lower = f"{name} {value}".lower()
            if artifact_basename.lower() not in lower and not any(word in lower for word in keywords):
                continue
            item = {
                "name": name,
                "value_class": _classify_public_value(value, artifact_basename=artifact_basename, keywords=keywords),
            }
            safe = _safe_public_value(value)
            if safe is not None:
                item["safe_public_value"] = safe
            data_matches.append(item)
        if not data_matches:
            continue
        names = {name for name, _ in attrs}
        observations.append({
            "tag_name": tag_name,
            "export_data_attributes": data_matches[:8],
            "href_present": "href" in names,
            "action_present": "action" in names,
            "onclick_present": "onclick" in names,
            "id_present": "id" in names,
            "class_present": "class" in names,
        })
        if len(observations) >= 12:
            break
    return tuple(observations)


def _script_mechanisms(text: str) -> dict:
    lower = text.lower()
    patterns = {
        "fetch": r"\bfetch\s*\(",
        "xmlhttprequest": r"\bXMLHttpRequest\b",
        "axios": r"\baxios(?:\.|\s*\()",
        "jquery_ajax": r"\$\s*\.\s*(?:ajax|get|post)\s*\(",
        "window_open": r"\bwindow\s*\.\s*open\s*\(",
        "location_navigation": r"(?:\bwindow\s*\.\s*)?\blocation\s*(?:\.\s*(?:href|assign|replace))?\s*(?:=|\()",
        "form_submit": r"\.\s*submit\s*\(",
        "event_listener": r"\.\s*addEventListener\s*\(",
        "click_event_literal": r"['\"]click['\"]",
        "anchor_download": r"\.\s*download\s*=|\bdownload\s*=",
        "blob": r"\bBlob\s*\(",
        "object_url": r"\bURL\s*\.\s*createObjectURL\s*\(",
        "url_search_params": r"\bURLSearchParams\s*\(",
    }
    return {name: len(re.findall(pattern, text, flags=re.IGNORECASE)) for name, pattern in patterns.items()}


def _dataset_keys(text: str) -> tuple[str, ...]:
    values = set(re.findall(r"\.dataset\.([A-Za-z_$][A-Za-z0-9_$]*)", text))
    return tuple(sorted(values)[:24])


def _data_attribute_names(text: str) -> tuple[str, ...]:
    values = set(re.findall(r"getAttribute\s*\(\s*['\"](data-[A-Za-z0-9_-]+)['\"]", text, flags=re.IGNORECASE))
    return tuple(sorted(value.lower() for value in values)[:24])


def _export_identifiers(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    identifiers = set()
    for identifier in re.findall(r"\b([A-Za-z_$][A-Za-z0-9_$]{1,100})\b", text):
        lower = identifier.lower()
        if any(word in lower for word in keywords):
            identifiers.add(identifier)
    return tuple(sorted(identifiers)[:32])


def _literal_strings_including_templates(text: str) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for quote, body in re.findall(r"(['\"`])((?:(?!\1).){1,800}?)\1", text, flags=re.DOTALL):
        decoded = unescape(body.replace("\\/", "/"))
        kind = "TEMPLATE_LITERAL" if quote == "`" else "QUOTED_LITERAL"
        values.append((kind, decoded))
    return tuple(values)


def _sanitize_route_template(value: str, *, base_url: str, allowed_hosts: tuple[str, ...]) -> dict | None:
    if not value.startswith(("https://", "/", "./", "../")):
        return None
    normalized = re.sub(r"\$\{[^}]{1,200}\}", "{VAR}", value)
    absolute = urljoin(base_url, normalized)
    parsed = urlparse(absolute)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        return None
    path = parsed.path
    if len(path) > 300:
        return None
    clean = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
    return {
        "template_without_query": clean,
        "dynamic": "{VAR}" in clean,
        "query_present": bool(parsed.query),
    }


def extract_route_templates(
    text: str,
    *,
    base_url: str,
    allowed_hosts: tuple[str, ...],
    artifact_basename: str,
    keywords: tuple[str, ...],
) -> tuple[dict, ...]:
    results: list[dict] = []
    seen: set[str] = set()
    for literal_kind, value in _literal_strings_including_templates(text):
        lower = value.lower()
        if artifact_basename.lower() not in lower and not any(word in lower for word in keywords):
            continue
        candidate = _sanitize_route_template(value, base_url=base_url, allowed_hosts=allowed_hosts)
        if candidate is None:
            continue
        key = candidate["template_without_query"] + ("?" if candidate["query_present"] else "")
        if key in seen:
            continue
        seen.add(key)
        results.append({
            **candidate,
            "literal_kind": literal_kind,
            "artifact_reference_present": artifact_basename.lower() in lower,
        })
        if len(results) >= 12:
            break
    return tuple(results)


def summarize_script_signals(
    text: str,
    *,
    source_kind: str,
    source_index: int,
    byte_count: int,
    base_url: str,
    allowed_hosts: tuple[str, ...],
    artifact_basename: str,
    keywords: tuple[str, ...],
) -> ScriptSignals:
    lower = text.lower()
    return ScriptSignals(
        source_kind=source_kind,
        source_index=source_index,
        byte_count=byte_count,
        keyword_present=any(word in lower for word in keywords),
        artifact_reference_present=artifact_basename.lower() in lower,
        mechanisms=_script_mechanisms(text),
        dataset_keys=_dataset_keys(text),
        data_attribute_names=_data_attribute_names(text),
        export_identifiers=_export_identifiers(text, keywords),
        route_templates=extract_route_templates(
            text,
            base_url=base_url,
            allowed_hosts=allowed_hosts,
            artifact_basename=artifact_basename,
            keywords=keywords,
        ),
    )


def _signal_to_dict(signal: ScriptSignals) -> dict:
    return {
        "source_kind": signal.source_kind,
        "source_index": signal.source_index,
        "byte_count": signal.byte_count,
        "keyword_present": signal.keyword_present,
        "artifact_reference_present": signal.artifact_reference_present,
        "mechanisms": signal.mechanisms,
        "dataset_keys": list(signal.dataset_keys),
        "data_attribute_names": list(signal.data_attribute_names),
        "export_identifiers": list(signal.export_identifiers),
        "route_templates": list(signal.route_templates),
    }


def discover_export_contract(config: dict, *, client: ReadOnlyDeclaredResourceClient | None = None) -> dict:
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
        raise SiopeExportContractDiscoveryError(str(exc)) from None

    if config["required_product_name"] not in page.body:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_PRODUCT_NOT_VERIFIED")
    if config["required_artifact_path"] not in page.body:
        raise SiopeExportContractDiscoveryError("STOP_SIOPE_EXPORT_CONTRACT_ARTIFACT_NOT_DECLARED")

    artifact_basename = config["required_artifact_path"].rsplit("/", 1)[-1]
    keywords = tuple(config["candidate_keywords"])
    controls = summarize_export_controls(page.body, artifact_basename=artifact_basename, keywords=keywords)

    inline_bodies = re.findall(
        r"<script\b(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script\s*>",
        page.body,
        flags=re.IGNORECASE | re.DOTALL,
    )
    inline_signals: list[ScriptSignals] = []
    for index, body in enumerate(inline_bodies, start=1):
        signal = summarize_script_signals(
            body,
            source_kind="INLINE_SCRIPT",
            source_index=index,
            byte_count=len(body.encode("utf-8")),
            base_url=page.url,
            allowed_hosts=allowed_hosts,
            artifact_basename=artifact_basename,
            keywords=keywords,
        )
        if signal.keyword_present or signal.artifact_reference_present:
            inline_signals.append(signal)

    script_urls = extract_declared_script_urls(
        page.body,
        page_url=page.url,
        allowed_hosts=allowed_hosts,
        max_scripts=int(config["max_scripts"]),
    )
    external_signals: list[ScriptSignals] = []
    script_failures: list[dict] = []
    total_script_bytes = 0
    fetched_scripts = 0
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
        signal = summarize_script_signals(
            script.body,
            source_kind="DECLARED_EXTERNAL_SCRIPT",
            source_index=script_index,
            byte_count=script.byte_count,
            base_url=script.url,
            allowed_hosts=allowed_hosts,
            artifact_basename=artifact_basename,
            keywords=keywords,
        )
        if signal.keyword_present or signal.artifact_reference_present:
            external_signals.append(signal)

    all_signals = inline_signals + external_signals
    route_template_count = sum(len(signal.route_templates) for signal in all_signals)
    diagnostics = {
        "page_verified": True,
        "artifact_declared": True,
        "page_bytes": page.byte_count,
        "export_control_count": len(controls),
        "export_controls": list(controls),
        "inline_export_script_count": len(inline_signals),
        "inline_export_scripts": [_signal_to_dict(signal) for signal in inline_signals[:8]],
        "declared_script_count": len(script_urls),
        "fetched_script_count": fetched_scripts,
        "external_export_script_count": len(external_signals),
        "external_export_scripts": [_signal_to_dict(signal) for signal in external_signals[:8]],
        "script_failure_count": len(script_failures),
        "script_failures": script_failures,
        "total_fetched_script_bytes": total_script_bytes,
        "route_template_count": route_template_count,
    }

    if not controls and not all_signals:
        raise SiopeExportContractDiscoveryError(
            "STOP_SIOPE_EXPORT_CONTRACT_NOT_OBSERVED",
            diagnostics=diagnostics,
        )

    contract_status = (
        "ROUTE_TEMPLATE_OBSERVED_NOT_CALLED"
        if route_template_count
        else "DYNAMIC_EXPORT_CONTROL_OBSERVED_ROUTE_UNPROVEN"
    )
    return {
        "status": "PASS_M7_SIOPE_EXPORT_CONTRACT_DISCOVERY_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "network_called": True,
        "network_method": "GET_ONLY",
        **diagnostics,
        "export_contract_status": contract_status,
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
        "next_gate": config["next_gate"],
    }
