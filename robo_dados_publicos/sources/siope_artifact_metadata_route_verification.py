from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class SiopeArtifactMetadataVerificationError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


@dataclass(frozen=True)
class MetadataResponse:
    url: str
    status: int
    content_type: str
    byte_count: int
    payload: object


class _SameHostHttpsRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allowed_hosts: tuple[str, ...]):
        super().__init__()
        self.allowed_hosts = set(allowed_hosts)

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        parsed = urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_REDIRECT_NOT_ALLOWED")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class MetadataRouteClient:
    def __init__(self, *, allowed_hosts: tuple[str, ...], opener=None):
        self.allowed_hosts = allowed_hosts
        self.opener = opener or build_opener(ProxyHandler({}), _SameHostHttpsRedirectHandler(allowed_hosts))

    def get_json(self, url: str, *, max_bytes: int, allowed_content_types: tuple[str, ...]) -> MetadataResponse:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_HOST_NOT_ALLOWED")
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_URL_NOT_EXACT")

        req = Request(
            url,
            headers={
                "User-Agent": "ROBO_DADOS_PUBLICOS/0.8.0 (+public-transparency-research)",
                "Accept": "application/json,text/json,text/plain;q=0.5",
            },
            method="GET",
        )
        try:
            response = self.opener.open(req, timeout=15)
            with response:
                final_url = str(getattr(response, "url", response.geturl()))
                final = urlparse(final_url)
                if final.scheme != "https" or final.hostname not in self.allowed_hosts:
                    raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_REDIRECT_NOT_ALLOWED")
                status = int(getattr(response, "status", response.getcode()))
                content_type = str(response.headers.get("Content-Type", "")).split(";", 1)[0].strip().lower()
                raw = response.read(max_bytes + 1)
        except SiopeArtifactMetadataVerificationError:
            raise
        except HTTPError as exc:
            raise SiopeArtifactMetadataVerificationError(f"STOP_SIOPE_METADATA_HTTP_{exc.code}") from None
        except (TimeoutError, socket.timeout):
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_TIMEOUT") from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
                raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_TIMEOUT") from None
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_NETWORK") from None
        except OSError:
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_NETWORK") from None

        if len(raw) > max_bytes:
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_RESPONSE_TOO_LARGE")
        if status != 200:
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_HTTP_STATUS")
        if content_type not in set(allowed_content_types):
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_CONTENT_TYPE")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_INVALID_JSON") from None
        if not isinstance(payload, (dict, list)):
            raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_JSON_ROOT")
        return MetadataResponse(final_url, status, content_type, len(raw), payload)


def _validate_config(config: dict) -> None:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_ANTONIETA_ARTIFACT_METADATA_ROUTE_VERIFICATION_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "EXACT_OBSERVED_METADATA_ROUTE_VERIFICATION_ONLY",
        "network": "ONE_READ_ONLY_GET_EXACT_METADATA_ROUTE",
        "metadata_url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/products/data-products/20/artifact-metadata",
        "route_evidence_run": 32837068191,
        "route_evidence_artifact": 9559032864,
        "required_product_id": 20,
        "required_artifact_path": "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
        "allowed_hosts": ["www.fnde.gov.br"],
        "allowed_method": "GET",
        "max_response_bytes": 131072,
        "allowed_content_types": ["application/json", "text/json", "text/plain"],
        "redirect_policy": "SAME_HOST_HTTPS_ONLY",
        "max_json_depth": 8,
        "max_json_nodes": 2048,
        "max_observed_candidates": 24,
        "raw_metadata_persist": "PROHIBITED",
        "response_body_persist": "PROHIBITED",
        "query_value_persist": "PROHIBITED",
        "request_headers_persist": "PROHIBITED",
        "cookies_persist": "PROHIBITED",
        "download_candidate_request": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "head_request": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "next_gate_if_metadata_verified": "M7_SIOPE_ARTIFACT_DOWNLOAD_ROUTE_VERIFICATION_DESIGN_0_8_0",
        "next_gate_if_metadata_verified_without_route": "M7_SIOPE_ARTIFACT_METADATA_SCHEMA_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopeArtifactMetadataVerificationError(f"STOP_SIOPE_METADATA_CONFIG_{key.upper()}")

    parsed = urlparse(config["metadata_url"])
    if parsed.scheme != "https" or parsed.hostname != "www.fnde.gov.br" or parsed.query or parsed.fragment:
        raise SiopeArtifactMetadataVerificationError("STOP_SIOPE_METADATA_CONFIG_URL")


def load_artifact_metadata_verification_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _safe_key(value: object) -> str:
    text = str(value)
    if len(text) > 120:
        return text[:117] + "..."
    return text


def _sanitize_url_or_path(value: str, *, field_path: str, allowed_hosts: set[str]) -> dict | None:
    candidate = value.strip()
    if not candidate or len(candidate) > 4096:
        return None

    parsed = urlparse(candidate)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        route = urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", "", ""))
        return {
            "field_path": field_path,
            "value_kind": "ABSOLUTE_URL",
            "scheme": parsed.scheme,
            "host": parsed.hostname,
            "route_without_query": route,
            "query_keys": sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True) if key}),
            "query_present": bool(parsed.query),
            "allowed_host": parsed.scheme == "https" and parsed.hostname in allowed_hosts,
        }

    relative = urlparse(candidate)
    looks_pathlike = candidate.startswith(("/", "./", "../", "exports/")) or "/" in candidate
    if looks_pathlike:
        clean_path = relative.path or candidate.split("?", 1)[0].split("#", 1)[0]
        return {
            "field_path": field_path,
            "value_kind": "RELATIVE_OR_STORAGE_PATH",
            "path_without_query": clean_path,
            "query_keys": sorted({key for key, _ in parse_qsl(relative.query, keep_blank_values=True) if key}),
            "query_present": bool(relative.query),
        }
    return None


def summarize_metadata_payload(payload: object, config: dict) -> dict:
    _validate_config(config)
    max_depth = int(config["max_json_depth"])
    max_nodes = int(config["max_json_nodes"])
    max_candidates = int(config["max_observed_candidates"])
    required_path = str(config["required_artifact_path"])
    required_basename = required_path.rsplit("/", 1)[-1]
    allowed_hosts = set(config["allowed_hosts"])

    top_level_keys = sorted(_safe_key(key) for key in payload) if isinstance(payload, dict) else []
    interesting_key_paths: set[str] = set()
    candidates: list[dict] = []
    seen_candidates: set[str] = set()
    artifact_path_observed = False
    product_id_observed = False
    node_count = 0
    truncated = False

    stack: list[tuple[object, str, int]] = [(payload, "$", 0)]
    while stack:
        current, path, depth = stack.pop()
        node_count += 1
        if node_count > max_nodes:
            truncated = True
            break
        if depth > max_depth:
            truncated = True
            continue

        if isinstance(current, dict):
            for raw_key, value in reversed(list(current.items())):
                key = _safe_key(raw_key)
                child_path = f"{path}.{key}"
                lower_key = key.lower()
                if any(marker in lower_key for marker in ("artifact", "artef", "download", "export", "file", "path", "storage", "product")):
                    interesting_key_paths.add(child_path)
                stack.append((value, child_path, depth + 1))
            continue

        if isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append((current[index], f"{path}[{index}]", depth + 1))
            continue

        if isinstance(current, bool) or current is None:
            continue
        if isinstance(current, (int, float)):
            if current == config["required_product_id"] and "product" in path.lower():
                product_id_observed = True
            continue
        if not isinstance(current, str):
            continue

        if current == required_path or required_basename in current:
            artifact_path_observed = True
        if current.strip() == str(config["required_product_id"]) and "product" in path.lower():
            product_id_observed = True

        sanitized = _sanitize_url_or_path(current, field_path=path, allowed_hosts=allowed_hosts)
        if sanitized is None:
            continue
        route_key = json.dumps(sanitized, sort_keys=True, ensure_ascii=False)
        if route_key in seen_candidates:
            continue
        seen_candidates.add(route_key)
        if len(candidates) < max_candidates:
            candidates.append(sanitized)
        else:
            truncated = True

    if truncated:
        raise SiopeArtifactMetadataVerificationError(
            "STOP_SIOPE_METADATA_SUMMARY_TRUNCATED",
            diagnostics={"json_node_count": node_count, "observed_candidate_count": len(candidates)},
        )

    return {
        "json_root_type": "object" if isinstance(payload, dict) else "array",
        "top_level_keys": top_level_keys[:64],
        "top_level_key_count": len(top_level_keys),
        "json_node_count": node_count,
        "interesting_key_paths": sorted(interesting_key_paths)[:64],
        "interesting_key_path_count": len(interesting_key_paths),
        "artifact_path_observed": artifact_path_observed,
        "product_id_observed": product_id_observed,
        "observed_candidate_count": len(candidates),
        "observed_candidates": candidates,
    }


def verify_artifact_metadata_route(config: dict, *, client: MetadataRouteClient | None = None) -> dict:
    _validate_config(config)
    client = client or MetadataRouteClient(allowed_hosts=tuple(config["allowed_hosts"]))
    response = client.get_json(
        config["metadata_url"],
        max_bytes=int(config["max_response_bytes"]),
        allowed_content_types=tuple(config["allowed_content_types"]),
    )
    summary = summarize_metadata_payload(response.payload, config)

    next_gate = (
        config["next_gate_if_metadata_verified"]
        if summary["observed_candidate_count"] > 0
        else config["next_gate_if_metadata_verified_without_route"]
    )

    return {
        "status": "PASS_M7_SIOPE_ARTIFACT_METADATA_ROUTE_VERIFICATION_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "metadata_route_status": "VERIFIED_200_JSON_EXACT_OBSERVED_ROUTE",
        "metadata_url": config["metadata_url"],
        "network_called": True,
        "network_method": "GET",
        "network_request_count_logical": 1,
        "response_status": response.status,
        "response_content_type": response.content_type,
        "response_byte_count": response.byte_count,
        **summary,
        "raw_metadata_persisted": False,
        "response_body_persisted": False,
        "query_values_persisted": False,
        "request_headers_persisted": False,
        "cookies_persisted": False,
        "download_candidate_requested": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "form_submission": False,
        "captcha_bypass": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": next_gate,
    }
